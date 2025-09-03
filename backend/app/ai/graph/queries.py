"""
Entertainment Industry Queries

Pre-built Cypher queries for common entertainment industry operations
and business intelligence.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date

from .connection import Neo4jClient
from .schema import NodeLabel, RelationshipType

logger = logging.getLogger(__name__)

class EntertainmentQueries:
    """
    Entertainment industry specific query operations
    """
    
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client

    # ================================
    # TALENT QUERIES
    # ================================
    
    async def find_talent_by_skills(
        self,
        skills: List[str],
        location: Optional[str] = None,
        union_status: Optional[List[str]] = None,
        max_day_rate: Optional[int] = None,
        availability_date: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find talent matching specific skills and criteria"""
        
        query = f"""
        MATCH (p:{NodeLabel.PERSON})
        WHERE ANY(skill IN $skills WHERE skill IN p.skills)
        """
        
        parameters = {"skills": skills, "limit": limit}
        
        # Add optional filters
        if location:
            query += " AND p.location CONTAINS $location"
            parameters["location"] = location
            
        if union_status:
            query += " AND ANY(union IN $union_status WHERE union IN p.union_status)"
            parameters["union_status"] = union_status
            
        if max_day_rate:
            query += " AND p.day_rate <= $max_day_rate"
            parameters["max_day_rate"] = max_day_rate
        
        # Calculate skill match score
        query += """
        WITH p, 
             size([skill IN p.skills WHERE skill IN $skills]) as matched_skills,
             size(p.skills) as total_skills
        WITH p, 
             toFloat(matched_skills) / size($skills) as skill_match_score,
             matched_skills,
             total_skills
        """
        
        # Get recent projects
        query += f"""
        OPTIONAL MATCH (p)-[worked:{RelationshipType.WORKED_ON}]->(proj:{NodeLabel.PROJECT})
        WHERE proj.date >= date('2022-01-01')
        WITH p, skill_match_score, matched_skills, total_skills,
             collect({{
                 project_name: proj.name,
                 project_type: proj.type,
                 date: proj.date,
                 role: worked.role
             }}) as recent_projects
        
        RETURN p {{
            .*,
            skill_match_score: skill_match_score,
            matched_skills: matched_skills,
            recent_projects: recent_projects[0..3]
        }}
        ORDER BY skill_match_score DESC, p.experience_years DESC
        LIMIT $limit
        """
        
        return await self.neo4j.run_query(query, parameters)

    async def get_talent_network(
        self,
        person_id: str,
        degrees: int = 2
    ) -> Dict[str, Any]:
        """Get talent's professional network"""
        
        query = f"""
        MATCH (center:{NodeLabel.PERSON} {{id: $person_id}})
        
        // Direct collaborators
        OPTIONAL MATCH (center)-[r1:{RelationshipType.COLLABORATES_WITH}|{RelationshipType.WORKED_ON}*1..{degrees}]-(connected:{NodeLabel.PERSON})
        WHERE connected <> center
        
        // Shared projects
        OPTIONAL MATCH (center)-[:{RelationshipType.WORKED_ON}]->(shared_proj:{NodeLabel.PROJECT})<-[:{RelationshipType.WORKED_ON}]-(collaborator:{NodeLabel.PERSON})
        WHERE collaborator <> center
        
        WITH center, 
             collect(DISTINCT connected) as network,
             collect(DISTINCT {{
                 person: collaborator,
                 shared_project: shared_proj.name
             }}) as project_collaborators
        
        RETURN center {{
            .*,
            network_size: size(network),
            direct_collaborators: [n IN network | n {{
                .id, .name, .role, .skills, .location
            }}][0..10],
            project_collaborators: project_collaborators[0..10]
        }}
        """
        
        results = await self.neo4j.run_query(query, {"person_id": person_id})
        return results[0] if results else {}

    # ================================
    # PROJECT QUERIES  
    # ================================
    
    async def find_similar_projects(
        self,
        project_type: str,
        budget_range: Optional[tuple] = None,
        location: Optional[str] = None,
        date_range: Optional[tuple] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find projects similar to given criteria"""
        
        query = f"""
        MATCH (p:{NodeLabel.PROJECT})
        WHERE p.type = $project_type
        """
        
        parameters = {"project_type": project_type, "limit": limit}
        
        if budget_range:
            query += " AND p.budget >= $min_budget AND p.budget <= $max_budget"
            parameters["min_budget"] = budget_range[0]
            parameters["max_budget"] = budget_range[1]
            
        if location:
            query += " AND p.location CONTAINS $location"
            parameters["location"] = location
            
        if date_range:
            query += " AND p.date >= date($start_date) AND p.date <= date($end_date)"
            parameters["start_date"] = date_range[0]
            parameters["end_date"] = date_range[1]
        
        # Get project team
        query += f"""
        OPTIONAL MATCH (team:{NodeLabel.PERSON})-[worked:{RelationshipType.WORKED_ON}]->(p)
        WITH p, collect({{
            person: team.name,
            role: worked.role,
            day_rate: worked.day_rate
        }}) as team_members
        
        RETURN p {{
            .*,
            team_size: size(team_members),
            team_members: team_members,
            cost_per_day: reduce(total = 0, member IN team_members | total + coalesce(member.day_rate, 0))
        }}
        ORDER BY p.date DESC
        LIMIT $limit
        """
        
        return await self.neo4j.run_query(query, parameters)

    async def get_project_analytics(
        self,
        project_type: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """Get project performance analytics"""
        
        base_query = f"""
        MATCH (p:{NodeLabel.PROJECT})
        """
        
        parameters = {}
        
        if project_type:
            base_query += " WHERE p.type = $project_type"
            parameters["project_type"] = project_type
            
        if date_range:
            if project_type:
                base_query += " AND "
            else:
                base_query += " WHERE "
            base_query += "p.date >= date($start_date) AND p.date <= date($end_date)"
            parameters["start_date"] = date_range[0]
            parameters["end_date"] = date_range[1]
        
        # Analytics query
        query = base_query + """
        WITH p
        
        // Budget statistics
        WITH collect(p.budget) as budgets, collect(p) as projects
        
        RETURN {
            total_projects: size(projects),
            avg_budget: reduce(total = 0, budget IN budgets | total + budget) / size(budgets),
            min_budget: reduce(min = budgets[0], budget IN budgets | case when budget < min then budget else min end),
            max_budget: reduce(max = budgets[0], budget IN budgets | case when budget > max then budget else max end),
            budget_distribution: apoc.coll.frequencies(budgets)
        } as analytics,
        projects
        
        // Project types breakdown
        WITH analytics, 
             [type IN collect(DISTINCT projects.type) | {
                 type: type,
                 count: size([p IN projects WHERE p.type = type])
             }] as type_breakdown
        
        RETURN analytics {
            .*,
            project_types: type_breakdown
        }
        """
        
        try:
            results = await self.neo4j.run_query(query, parameters)
            return results[0]["analytics"] if results else {}
        except:
            # Fallback without APOC functions
            simple_query = base_query + """
            WITH p
            RETURN {
                total_projects: count(p),
                avg_budget: avg(p.budget),
                min_budget: min(p.budget),
                max_budget: max(p.budget)
            } as analytics
            """
            results = await self.neo4j.run_query(simple_query, parameters)
            return results[0]["analytics"] if results else {}

    # ================================
    # COMPANY QUERIES
    # ================================
    
    async def find_production_companies(
        self,
        specialties: Optional[List[str]] = None,
        location: Optional[str] = None,
        size: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find production companies by criteria"""
        
        query = f"""
        MATCH (c:{NodeLabel.COMPANY})
        WHERE c.type = 'Production Company'
        """
        
        parameters = {"limit": limit}
        
        if specialties:
            query += " AND ANY(specialty IN $specialties WHERE specialty IN c.specialties)"
            parameters["specialties"] = specialties
            
        if location:
            query += " AND c.location CONTAINS $location"
            parameters["location"] = location
            
        if size:
            query += " AND c.size = $size"
            parameters["size"] = size
        
        # Get company statistics
        query += f"""
        OPTIONAL MATCH (c)<-[:{RelationshipType.COLLABORATES_WITH}]-(talent:{NodeLabel.PERSON})
        OPTIONAL MATCH (c)<-[:{RelationshipType.EMPLOYED_BY}]-(employee:{NodeLabel.PERSON})
        
        WITH c, 
             collect(DISTINCT talent) as collaborators,
             collect(DISTINCT employee) as employees
        
        OPTIONAL MATCH (c)-[:{RelationshipType.WORKED_ON}]->(project:{NodeLabel.PROJECT})
        WHERE project.date >= date('2022-01-01')
        
        WITH c, collaborators, employees, 
             collect(project) as recent_projects
        
        RETURN c {{
            .*,
            collaborator_count: size(collaborators),
            employee_count: size(employees),
            recent_project_count: size(recent_projects),
            recent_projects: [p IN recent_projects | p {{
                .name, .type, .budget, .date
            }}][0..5]
        }}
        ORDER BY size(recent_projects) DESC, c.name
        LIMIT $limit
        """
        
        return await self.neo4j.run_query(query, parameters)

    # ================================
    # HYBRID QUERIES (Vector + Graph)
    # ================================
    
    async def semantic_talent_search(
        self,
        query_vector: List[float],
        skills: Optional[List[str]] = None,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Semantic search for talent using vector similarity + graph filtering"""
        
        # Vector search for people with bio embeddings
        vector_results = await self.neo4j.run_vector_query(
            index_name="person_bio_vector",
            vector=query_vector,
            top_k=limit * 2,  # Get more candidates for filtering
            similarity_threshold=similarity_threshold
        )
        
        if not vector_results:
            return []
        
        # Extract person IDs from vector results
        person_ids = [result["node_properties"]["id"] for result in vector_results]
        
        # Enhanced graph query with skill filtering
        query = f"""
        MATCH (p:{NodeLabel.PERSON})
        WHERE p.id IN $person_ids
        """
        
        parameters = {"person_ids": person_ids}
        
        if skills:
            query += " AND ANY(skill IN $skills WHERE skill IN p.skills)"
            parameters["skills"] = skills
        
        query += f"""
        // Get recent work and collaborators
        OPTIONAL MATCH (p)-[work:{RelationshipType.WORKED_ON}]->(proj:{NodeLabel.PROJECT})
        WHERE proj.date >= date('2022-01-01')
        
        WITH p, 
             collect(proj {{.name, .type, .budget, .date}}) as recent_projects,
             collect(work.role) as recent_roles
        
        // Calculate experience diversity score
        WITH p, recent_projects, recent_roles,
             size(collect(DISTINCT work.role)) as role_diversity,
             size(recent_projects) as project_count
        
        RETURN p {{
            .*,
            recent_projects: recent_projects[0..3],
            role_diversity: role_diversity,
            recent_project_count: project_count,
            experience_score: toFloat(p.experience_years * role_diversity + project_count) / 10
        }}
        ORDER BY p.experience_score DESC
        LIMIT $limit
        """
        
        graph_results = await self.neo4j.run_query(query, parameters)
        
        # Merge vector similarity scores with graph results
        similarity_map = {
            result["node_properties"]["id"]: result["similarity_score"]
            for result in vector_results
        }
        
        for result in graph_results:
            person_id = result["p"]["id"]
            result["p"]["semantic_similarity"] = similarity_map.get(person_id, 0.0)
        
        return graph_results

    # ================================
    # ANALYTICS QUERIES
    # ================================
    
    async def get_market_trends(
        self,
        months_back: int = 12
    ) -> Dict[str, Any]:
        """Get entertainment market trends"""
        
        cutoff_date = datetime.now().replace(day=1).date()
        # Approximate date calculation (simplified)
        
        query = f"""
        MATCH (p:{NodeLabel.PROJECT})
        WHERE p.date >= date('2023-01-01')  // Simplified date filter
        
        WITH p, p.date.year as year, p.date.month as month
        
        // Monthly project counts by type
        WITH year, month, p.type, count(p) as project_count, avg(p.budget) as avg_budget
        ORDER BY year, month
        
        WITH year, month, 
             collect({{
                 type: p.type,
                 count: project_count,
                 avg_budget: avg_budget
             }}) as monthly_breakdown
        
        RETURN {{
            year: year,
            month: month,
            breakdown: monthly_breakdown,
            total_projects: reduce(total = 0, item IN monthly_breakdown | total + item.count),
            total_budget: reduce(total = 0.0, item IN monthly_breakdown | total + item.avg_budget * item.count)
        }} as trend_data
        ORDER BY year DESC, month DESC
        """
        
        return await self.neo4j.run_query(query)

    async def get_talent_utilization(
        self,
        date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Get talent utilization statistics"""
        
        query = f"""
        MATCH (p:{NodeLabel.PERSON})-[work:{RelationshipType.WORKED_ON}]->(proj:{NodeLabel.PROJECT})
        """
        
        parameters = {}
        
        if date_range:
            query += " WHERE proj.date >= date($start_date) AND proj.date <= date($end_date)"
            parameters["start_date"] = date_range[0]
            parameters["end_date"] = date_range[1]
        
        query += """
        WITH p, collect(work) as projects_worked,
             collect(proj.budget) as project_budgets,
             collect(work.day_rate) as day_rates
        
        WITH p,
             size(projects_worked) as projects_count,
             reduce(total = 0, budget IN project_budgets | total + budget) as total_project_value,
             avg([rate IN day_rates WHERE rate IS NOT NULL]) as avg_day_rate
        
        RETURN p {
            .id, .name, .role, .skills, .location,
            projects_count: projects_count,
            total_project_value: total_project_value,
            avg_day_rate: avg_day_rate,
            utilization_score: projects_count * coalesce(avg_day_rate, 0) / 1000
        }
        ORDER BY utilization_score DESC
        """
        
        return await self.neo4j.run_query(query, parameters)

    # ================================
    # UTILITY QUERIES
    # ================================
    
    async def search_entities(
        self,
        search_term: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """General entity search across all node types"""
        
        results = []
        
        # Define searchable labels
        searchable_labels = entity_types or [
            NodeLabel.PERSON.value,
            NodeLabel.PROJECT.value,
            NodeLabel.COMPANY.value
        ]
        
        for label in searchable_labels:
            query = f"""
            MATCH (n:{label})
            WHERE toLower(n.name) CONTAINS toLower($search_term)
               OR ANY(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($search_term))
            
            RETURN '{label}' as entity_type, n
            LIMIT {limit // len(searchable_labels)}
            """
            
            try:
                label_results = await self.neo4j.run_query(query, {"search_term": search_term})
                results.extend(label_results)
            except Exception as e:
                logger.warning(f"Search failed for label {label}: {e}")
        
        return results[:limit]

    async def get_recommendations(
        self,
        person_id: str,
        recommendation_type: str = "collaborators",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on network analysis"""
        
        if recommendation_type == "collaborators":
            # Recommend people who worked on similar projects
            query = f"""
            MATCH (person:{NodeLabel.PERSON} {{id: $person_id}})-[:{RelationshipType.WORKED_ON}]->(proj:{NodeLabel.PROJECT})
            MATCH (proj)<-[:{RelationshipType.WORKED_ON}]-(collaborator:{NodeLabel.PERSON})
            WHERE collaborator <> person
            
            WITH collaborator, count(proj) as shared_projects,
                 collect(proj.type) as project_types
            
            // Find collaborators of collaborators (2nd degree)
            OPTIONAL MATCH (collaborator)-[:{RelationshipType.WORKED_ON}]->(other_proj:{NodeLabel.PROJECT})
                <-[:{RelationshipType.WORKED_ON}]-(recommendation:{NodeLabel.PERSON})
            WHERE recommendation <> person AND recommendation <> collaborator
            
            WITH recommendation, 
                 count(other_proj) as indirect_connections,
                 collect(DISTINCT other_proj.type) as recommended_project_types
            
            RETURN recommendation {{
                .*,
                connection_strength: indirect_connections,
                shared_project_types: recommended_project_types
            }}
            ORDER BY connection_strength DESC
            LIMIT $limit
            """
            
        elif recommendation_type == "projects":
            # Recommend projects based on skills and past work
            query = f"""
            MATCH (person:{NodeLabel.PERSON} {{id: $person_id}})
            MATCH (person)-[:{RelationshipType.WORKED_ON}]->(past_proj:{NodeLabel.PROJECT})
            
            WITH person, collect(DISTINCT past_proj.type) as past_types
            
            MATCH (similar_proj:{NodeLabel.PROJECT})
            WHERE similar_proj.type IN past_types
              AND similar_proj.status = 'Open'  // Assuming there's a status field
              AND NOT (person)-[:{RelationshipType.WORKED_ON}]->(similar_proj)
            
            RETURN similar_proj {{
                .*,
                match_reason: 'Similar to past projects: ' + apoc.text.join(past_types, ', ')
            }}
            ORDER BY similar_proj.budget DESC
            LIMIT $limit
            """
        
        else:
            return []
        
        return await self.neo4j.run_query(query, {"person_id": person_id, "limit": limit})