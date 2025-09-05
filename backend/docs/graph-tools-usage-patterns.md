# Graph Tools Usage Patterns

## Overview

This document provides practical usage patterns and examples for the OneVice graph tools integration. These patterns demonstrate how different agents leverage the shared GraphQueryTools to solve entertainment industry use cases.

## Pattern Categories

### 1. People Discovery & Analysis Patterns

#### Pattern: Lead Qualification (Sales Agent)
```python
class SalesIntelligenceAgent(CRMToolsMixin):
    async def qualify_lead(self, company_name: str, contact_name: str):
        """Comprehensive lead qualification using multiple graph tools"""
        
        # Step 1: Get organization intelligence
        org_profile = await self.get_organization_profile(company_name)
        
        if not org_profile.get("found"):
            return {"qualified": False, "reason": "Organization not found"}
        
        # Step 2: Analyze decision makers
        decision_makers = await self.find_decision_makers(company_name)
        
        # Step 3: Get contact's detailed profile
        contact_profile = await self.get_person_details(contact_name)
        
        # Step 4: Analyze network connections
        connections = await self.get_network_connections(contact_name, degrees=2)
        
        # Qualification scoring
        qualification_score = self._calculate_lead_score(
            org_profile, decision_makers, contact_profile, connections
        )
        
        return {
            "qualified": qualification_score > 70,
            "score": qualification_score,
            "organization": org_profile,
            "contact_analysis": contact_profile,
            "decision_makers": decision_makers,
            "network_strength": len(connections.get("connections", [])),
            "recommended_approach": self._get_approach_strategy(qualification_score)
        }

    def _calculate_lead_score(self, org_profile, decision_makers, contact_profile, connections):
        """Lead scoring algorithm using graph data"""
        score = 0
        
        # Organization factors (40% of score)
        if org_profile.get("tier") == "Enterprise":
            score += 20
        if org_profile.get("industry") in ["Entertainment", "Media"]:
            score += 15
        if org_profile.get("recent_projects", 0) > 5:
            score += 5
        
        # Contact factors (30% of score)  
        if contact_profile.get("title") in ["CEO", "President", "VP", "Director"]:
            score += 15
        if contact_profile.get("decision_making_authority", False):
            score += 10
        if contact_profile.get("years_experience", 0) > 10:
            score += 5
        
        # Network factors (20% of score)
        network_size = len(connections.get("connections", []))
        if network_size > 50:
            score += 10
        elif network_size > 20:
            score += 5
        
        # Decision maker access (10% of score)
        high_influence_dms = [dm for dm in decision_makers.get("decision_makers", []) 
                             if dm.get("decision_maker_score") == "high"]
        if len(high_influence_dms) > 0:
            score += 10
        
        return min(score, 100)
```

#### Pattern: Talent Pool Analysis (Talent Agent)
```python
class TalentAcquisitionAgent(TalentToolsMixin):
    async def build_talent_pool(self, project_requirements: Dict[str, Any]):
        """Build comprehensive talent pool for project requirements"""
        
        project_type = project_requirements.get("type", "commercial")
        required_skills = project_requirements.get("skills", [])
        budget_tier = project_requirements.get("budget_tier", "mid")
        location = project_requirements.get("location", "Los Angeles")
        
        # Step 1: Find similar successful projects
        similar_projects = await self.find_similar_projects(
            f"{project_type} campaign", 
            similarity_threshold=0.75
        )
        
        # Step 2: Extract successful team patterns
        successful_teams = []
        for project in similar_projects.get("projects", []):
            team_details = await self.get_project_team_details(project["title"])
            successful_teams.append(team_details)
        
        # Step 3: Identify key roles and preferred collaborations
        role_patterns = self._analyze_team_patterns(successful_teams)
        
        # Step 4: Build talent pools for each role
        talent_pools = {}
        for role, pattern in role_patterns.items():
            
            # Get people with this role
            candidates = await self._find_candidates_by_role(role, required_skills, location)
            
            # Score candidates based on pattern matching
            scored_candidates = []
            for candidate in candidates.get("people", []):
                
                # Get detailed profile
                profile = await self.get_person_details(candidate["name"])
                
                # Find their collaborators
                collaborators = await self.find_collaborators(
                    candidate["name"], 
                    project_type
                )
                
                # Calculate fit score
                fit_score = self._calculate_talent_fit_score(
                    profile, collaborators, pattern, project_requirements
                )
                
                scored_candidates.append({
                    **candidate,
                    "detailed_profile": profile,
                    "collaborators": collaborators,
                    "fit_score": fit_score,
                    "availability": self._check_availability(profile),
                    "rate_estimate": self._estimate_rate(profile, budget_tier)
                })
            
            # Sort by fit score
            talent_pools[role] = sorted(
                scored_candidates, 
                key=lambda x: x["fit_score"], 
                reverse=True
            )[:10]  # Top 10 per role
        
        return {
            "project_requirements": project_requirements,
            "similar_projects": similar_projects,
            "team_patterns": role_patterns,
            "talent_pools": talent_pools,
            "recommended_combinations": self._generate_team_combinations(talent_pools)
        }

    def _analyze_team_patterns(self, successful_teams):
        """Analyze patterns in successful team compositions"""
        patterns = {}
        
        for team in successful_teams:
            for member in team.get("crew", []):
                role = member.get("role")
                if role not in patterns:
                    patterns[role] = {
                        "frequency": 0,
                        "avg_experience": 0,
                        "common_skills": {},
                        "collaboration_patterns": []
                    }
                
                patterns[role]["frequency"] += 1
                patterns[role]["avg_experience"] += member.get("years_experience", 0)
                
                # Track skill frequencies
                for skill in member.get("skills", []):
                    if skill not in patterns[role]["common_skills"]:
                        patterns[role]["common_skills"][skill] = 0
                    patterns[role]["common_skills"][skill] += 1
        
        # Normalize and rank patterns
        for role in patterns:
            if patterns[role]["frequency"] > 0:
                patterns[role]["avg_experience"] /= patterns[role]["frequency"]
                # Sort skills by frequency
                patterns[role]["common_skills"] = dict(
                    sorted(patterns[role]["common_skills"].items(), 
                          key=lambda x: x[1], reverse=True)
                )
        
        return patterns
```

### 2. Project Intelligence Patterns

#### Pattern: Competitive Analysis (Sales Agent)
```python
async def analyze_competitive_landscape(self, target_client: str, project_category: str):
    """Analyze competitive landscape for client acquisition"""
    
    # Step 1: Get client's organization profile
    client_profile = await self.get_organization_profile(target_client)
    
    # Step 2: Find client's recent projects
    client_projects = await self.search_projects_by_criteria({
        "client": target_client,
        "date_range": "last_2_years",
        "status": ["completed", "in_production"]
    })
    
    # Step 3: Identify competing production companies
    competitors = set()
    for project in client_projects.get("projects", []):
        project_details = await self.get_project_team_details(project["title"])
        production_company = project_details.get("production_company")
        if production_company:
            competitors.add(production_company)
    
    # Step 4: Analyze competitor strengths
    competitor_analysis = {}
    for competitor in competitors:
        comp_profile = await self.get_organization_profile(competitor)
        comp_projects = await self.search_projects_by_criteria({
            "production_company": competitor,
            "date_range": "last_2_years"
        })
        
        competitor_analysis[competitor] = {
            "profile": comp_profile,
            "project_count": len(comp_projects.get("projects", [])),
            "avg_budget": self._calculate_avg_budget(comp_projects),
            "specializations": self._identify_specializations(comp_projects),
            "key_talent": await self._get_competitor_key_talent(competitor),
            "recent_wins": self._identify_recent_wins(comp_projects, target_client)
        }
    
    # Step 5: Find differentiation opportunities
    market_gaps = await self._identify_market_gaps(
        client_projects, competitor_analysis, project_category
    )
    
    return {
        "target_client": client_profile,
        "client_project_history": client_projects,
        "competitor_landscape": competitor_analysis,
        "market_gaps": market_gaps,
        "positioning_strategy": self._generate_positioning_strategy(
            client_profile, competitor_analysis, market_gaps
        ),
        "recommended_approach": self._generate_sales_approach(
            client_profile, competitor_analysis
        )
    }
```

#### Pattern: Creative Intelligence (Analytics Agent)
```python
async def analyze_creative_trends(self, category: str, time_period: str):
    """Analyze creative trends and patterns across projects"""
    
    # Step 1: Get projects in category and time period
    projects = await self.search_projects_by_criteria({
        "type": category,
        "date_range": time_period,
        "status": "completed"
    })
    
    # Step 2: Extract creative concepts from each project
    creative_analysis = {}
    concept_frequency = {}
    
    for project in projects.get("projects", []):
        concepts = await self.get_creative_concepts_for_project(project["title"])
        
        project_analysis = {
            "title": project["title"],
            "concepts": concepts,
            "performance": await self.extract_project_insights(
                project["title"], "performance"
            )
        }
        creative_analysis[project["title"]] = project_analysis
        
        # Track concept frequencies
        for concept in concepts.get("concepts", []):
            concept_name = concept.get("name")
            if concept_name not in concept_frequency:
                concept_frequency[concept_name] = {
                    "count": 0,
                    "projects": [],
                    "avg_performance": 0,
                    "categories": set()
                }
            
            concept_frequency[concept_name]["count"] += 1
            concept_frequency[concept_name]["projects"].append(project["title"])
            concept_frequency[concept_name]["categories"].add(concept.get("category"))
    
    # Step 3: Identify trending concepts
    trending_concepts = self._identify_trending_concepts(concept_frequency, projects)
    
    # Step 4: Analyze performance correlation
    performance_insights = self._analyze_concept_performance(
        creative_analysis, concept_frequency
    )
    
    # Step 5: Generate creative recommendations
    recommendations = self._generate_creative_recommendations(
        trending_concepts, performance_insights, category
    )
    
    return {
        "analysis_period": time_period,
        "category": category,
        "projects_analyzed": len(projects.get("projects", [])),
        "creative_concepts": concept_frequency,
        "trending_concepts": trending_concepts,
        "performance_insights": performance_insights,
        "recommendations": recommendations,
        "emerging_styles": self._identify_emerging_styles(concept_frequency)
    }
```

### 3. Network Analysis Patterns

#### Pattern: Influence Mapping (Sales Agent)
```python
async def map_client_influence_network(self, target_client: str):
    """Map influence networks within target client organization"""
    
    # Step 1: Get organization profile and people
    org_profile = await self.get_organization_profile(target_client)
    
    # Step 2: Find all people associated with organization
    org_people = await self._find_organization_people(target_client)
    
    # Step 3: Build influence map
    influence_network = {}
    
    for person in org_people:
        person_profile = await self.get_person_details(person["name"])
        connections = await self.get_network_connections(person["name"], degrees=2)
        
        # Calculate influence metrics
        influence_metrics = {
            "internal_connections": self._count_internal_connections(
                connections, target_client
            ),
            "external_connections": self._count_external_connections(
                connections, target_client  
            ),
            "decision_making_power": self._assess_decision_power(person_profile),
            "project_involvement": await self._get_project_involvement(person["name"]),
            "network_centrality": self._calculate_network_centrality(connections)
        }
        
        influence_network[person["name"]] = {
            "profile": person_profile,
            "connections": connections,
            "influence_metrics": influence_metrics,
            "influence_score": self._calculate_influence_score(influence_metrics),
            "approach_strategy": self._determine_approach_strategy(
                person_profile, influence_metrics
            )
        }
    
    # Step 4: Identify key influencers and pathways
    key_influencers = self._identify_key_influencers(influence_network)
    influence_pathways = self._map_influence_pathways(influence_network)
    
    return {
        "organization": org_profile,
        "influence_network": influence_network,
        "key_influencers": key_influencers,
        "influence_pathways": influence_pathways,
        "engagement_strategy": self._generate_engagement_strategy(
            key_influencers, influence_pathways
        )
    }
```

### 4. Performance Analytics Patterns

#### Pattern: Team Performance Analysis (Analytics Agent)
```python
async def analyze_team_performance_patterns(self, analysis_criteria: Dict[str, Any]):
    """Analyze performance patterns across different team compositions"""
    
    project_type = analysis_criteria.get("project_type")
    time_period = analysis_criteria.get("time_period", "last_2_years")
    performance_metrics = analysis_criteria.get("metrics", ["budget", "timeline", "quality"])
    
    # Step 1: Get projects matching criteria
    projects = await self.search_projects_by_criteria({
        "type": project_type,
        "date_range": time_period,
        "status": "completed"
    })
    
    # Step 2: Analyze each project's team and performance
    team_performance_data = []
    
    for project in projects.get("projects", []):
        # Get team composition
        team_details = await self.get_project_team_details(project["title"])
        
        # Get performance insights
        performance = await self.extract_project_insights(
            project["title"], "performance"
        )
        
        # Analyze team characteristics
        team_characteristics = self._analyze_team_characteristics(team_details)
        
        team_performance_data.append({
            "project": project,
            "team_details": team_details,
            "team_characteristics": team_characteristics,
            "performance": performance,
            "performance_score": self._calculate_performance_score(
                performance, performance_metrics
            )
        })
    
    # Step 3: Identify performance patterns
    patterns = {
        "high_performing_teams": [],
        "underperforming_teams": [],
        "success_factors": {},
        "risk_factors": {}
    }
    
    # Separate high and low performers
    sorted_teams = sorted(team_performance_data, 
                         key=lambda x: x["performance_score"], reverse=True)
    
    top_third = len(sorted_teams) // 3
    patterns["high_performing_teams"] = sorted_teams[:top_third]
    patterns["underperforming_teams"] = sorted_teams[-top_third:]
    
    # Step 4: Analyze success and risk factors
    patterns["success_factors"] = self._identify_success_factors(
        patterns["high_performing_teams"]
    )
    patterns["risk_factors"] = self._identify_risk_factors(
        patterns["underperforming_teams"]
    )
    
    # Step 5: Generate team optimization recommendations
    optimization_recommendations = self._generate_optimization_recommendations(
        patterns, team_performance_data
    )
    
    return {
        "analysis_criteria": analysis_criteria,
        "projects_analyzed": len(team_performance_data),
        "performance_patterns": patterns,
        "team_characteristics_analysis": self._summarize_team_characteristics(
            team_performance_data
        ),
        "optimization_recommendations": optimization_recommendations,
        "predictive_insights": self._generate_predictive_insights(patterns)
    }
```

## Error Handling Patterns

### Pattern: Graceful Degradation
```python
async def robust_person_lookup(self, name: str) -> Dict[str, Any]:
    """Robust person lookup with multiple fallback strategies"""
    
    result = {
        "name": name,
        "found": False,
        "data_sources": [],
        "warnings": []
    }
    
    # Primary: Try cached result
    try:
        cached_result = await self._get_cached_result(f"person_details:{name.lower()}")
        if cached_result:
            result.update(cached_result)
            result["data_sources"].append("cache")
            result["found"] = True
            return result
    except Exception as e:
        result["warnings"].append(f"Cache lookup failed: {str(e)}")
    
    # Secondary: Try Neo4j graph query
    try:
        graph_result = await self._query_neo4j_person(name)
        if graph_result and graph_result.get("found"):
            result.update(graph_result)
            result["data_sources"].append("neo4j")
            result["found"] = True
            
            # Cache successful result
            await self._set_cached_result(
                f"person_details:{name.lower()}", 
                result, 
                self.cache_ttl["person"]
            )
    except Exception as e:
        result["warnings"].append(f"Neo4j query failed: {str(e)}")
    
    # Tertiary: Try Folk API
    if not result["found"] and self.folk_client:
        try:
            folk_result = await self._query_folk_person(name)
            if folk_result and folk_result.get("found"):
                result.update(folk_result)
                result["data_sources"].append("folk_api")
                result["found"] = True
        except Exception as e:
            result["warnings"].append(f"Folk API query failed: {str(e)}")
    
    # Final fallback: Fuzzy search
    if not result["found"]:
        try:
            fuzzy_results = await self._fuzzy_search_person(name)
            if fuzzy_results:
                result["found"] = True
                result["fuzzy_matches"] = fuzzy_results
                result["data_sources"].append("fuzzy_search")
                result["warnings"].append("Exact match not found, showing fuzzy matches")
        except Exception as e:
            result["warnings"].append(f"Fuzzy search failed: {str(e)}")
    
    return result
```

## Performance Optimization Patterns

### Pattern: Batch Query Optimization
```python
async def batch_person_enrichment(self, person_names: List[str]) -> Dict[str, Any]:
    """Efficiently enrich multiple person profiles in batch"""
    
    # Step 1: Check cache for all names
    cache_keys = [f"person_details:{name.lower()}" for name in person_names]
    cached_results = {}
    uncached_names = []
    
    if self.redis_client:
        try:
            # Batch cache lookup
            cache_values = await self.redis_client.mget(cache_keys)
            
            for i, (name, cached_value) in enumerate(zip(person_names, cache_values)):
                if cached_value:
                    cached_results[name] = json.loads(cached_value)
                else:
                    uncached_names.append(name)
        except Exception as e:
            logger.warning(f"Batch cache lookup failed: {e}")
            uncached_names = person_names
    
    # Step 2: Batch Neo4j query for uncached names
    neo4j_results = {}
    if uncached_names:
        try:
            # Single query with multiple name matches
            query = """
            UNWIND $names as name
            MATCH (p:Person)
            WHERE toLower(p.name) CONTAINS toLower(name) OR 
                  toLower(name) CONTAINS toLower(p.name)
            WITH name, p, 
                 CASE WHEN toLower(p.name) = toLower(name) THEN 2 ELSE 1 END as exactness
            ORDER BY exactness DESC
            RETURN name, collect(p)[0] as person
            """
            
            result = await self.neo4j_client.execute_query(
                query, {"names": uncached_names}
            )
            
            for record in result.records:
                name = record["name"]
                person_node = record["person"]
                if person_node:
                    neo4j_results[name] = dict(person_node)
                    
        except Exception as e:
            logger.error(f"Batch Neo4j query failed: {e}")
    
    # Step 3: Combine results and cache new findings
    all_results = {**cached_results}
    
    for name in uncached_names:
        if name in neo4j_results:
            all_results[name] = neo4j_results[name]
            
            # Cache individual result
            await self._set_cached_result(
                f"person_details:{name.lower()}",
                neo4j_results[name],
                self.cache_ttl["person"]
            )
    
    return {
        "requested_names": person_names,
        "found_count": len(all_results),
        "results": all_results,
        "cache_hits": len(cached_results),
        "cache_misses": len(uncached_names),
        "performance": {
            "cache_hit_rate": len(cached_results) / len(person_names),
            "batch_efficiency": "high" if len(person_names) > 5 else "standard"
        }
    }
```

These patterns demonstrate how the shared GraphQueryTools architecture enables sophisticated, performant queries across different agent types while maintaining code reusability and data consistency.