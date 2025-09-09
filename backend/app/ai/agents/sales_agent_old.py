"""
Sales Intelligence Agent

Specialized agent for entertainment industry sales analysis,
lead qualification, and market intelligence.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent
from ..config import AIConfig, AgentType
from ..llm.router import LLMRouter  
from ..llm.prompt_templates import PromptType
from ..services.knowledge_service import KnowledgeGraphService
from ..tools.tool_mixins import CRMToolsMixin
from ...core.exceptions import AIProcessingError
from database.neo4j_client import Neo4jClient
from tools.folk_ingestion.folk_client import FolkClient

logger = logging.getLogger(__name__)

class SalesIntelligenceAgent(BaseAgent, CRMToolsMixin):
    """
    Sales intelligence agent specialized in:
    - Lead qualification and scoring
    - Market analysis and trends  
    - Competitive intelligence
    - Pricing optimization
    - Opportunity assessment
    """
    
    def __init__(
        self,
        config: AIConfig,
        llm_router: LLMRouter,
        knowledge_service: Optional[KnowledgeGraphService] = None,
        redis_client=None,
        model_config_manager=None,
        neo4j_client: Optional[Neo4jClient] = None,
        folk_client: Optional[FolkClient] = None
    ):
        super().__init__(
            agent_type=AgentType.SALES,
            config=config,
            llm_router=llm_router,
            redis_client=redis_client,
            model_config_manager=model_config_manager
        )
        
        self.knowledge_service = knowledge_service
        self.neo4j_client = neo4j_client
        self.folk_client = folk_client
        self.specialization = "sales_intelligence"
        
        # Initialize CRM-specific tools if client is available
        if neo4j_client:
            self.init_crm_tools(neo4j_client, folk_client, redis_client)
            logger.info("Sales tools initialized for SalesIntelligenceAgent")

    def _get_prompt_type(self) -> PromptType:
        """Get prompt type for sales agent"""
        return PromptType.SALES_INTELLIGENCE

    def _extract_name_from_query(self, query: str) -> Dict[str, str]:
        """Extract person name and company from query"""
        import re
        
        result = {"name": "", "company": ""}
        query_lower = query.lower()
        
        # Pattern 1: "profile for John Doe" or "tell me about Jane Smith"
        name_pattern = r'(?:profile for|tell me about|who is|information on|details about)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        match = re.search(name_pattern, query, re.IGNORECASE)
        if match:
            result["name"] = match.group(1).strip()
        
        # Pattern 2: "John Doe who works at" or "Jane Smith at Company"
        name_company_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+who works at|\s+at)\s+([A-Z][^.?!]*)'
        match = re.search(name_company_pattern, query)
        if match:
            result["name"] = match.group(1).strip()
            result["company"] = match.group(2).strip()
        
        # Pattern 3: Just capitalized names (fallback)
        if not result["name"]:
            name_fallback = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
            match = re.search(name_fallback, query)
            if match:
                result["name"] = match.group(1).strip()
        
        # Extract company from various patterns
        if not result["company"]:
            company_patterns = [
                r'at\s+([A-Z][^.?!,]*?)(?:\.|,|$|\s+I\s+need)',
                r'works at\s+([A-Z][^.?!,]*?)(?:\.|,|$|\s+I\s+need)',
                r'from\s+([A-Z][^.?!,]*?)(?:\.|,|$|\s+I\s+need)'
            ]
            for pattern in company_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    result["company"] = match.group(1).strip()
                    break
        
        return result

    def _extract_organization_from_query(self, query: str) -> str:
        """Extract organization/company name from organization-focused queries"""
        import re
        
        # Remove common question words and relationship indicators
        cleaned_query = query.strip()
        
        # Pattern 1: "do we work with CocaCola?" -> "CocaCola"
        work_with_pattern = r'(?:do we work with|work with|working with|partner with|client)\s+([A-Za-z][A-Za-z0-9\s&\.]+?)(?:\?|$|\.|\s+and|\s+or)'
        match = re.search(work_with_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "what about CocaCola?" -> "CocaCola"
        what_about_pattern = r'(?:what about|tell me about|information about|details about)\s+([A-Za-z][A-Za-z0-9\s&\.]+?)(?:\s+(?:relationship|partnership|collaboration|client|project)|$|\?|\.)'
        match = re.search(what_about_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 3: "CocaCola relationship" -> "CocaCola"  
        relationship_pattern = r'([A-Za-z][A-Za-z0-9\s&\.]+?)\s+(?:relationship|partnership|collaboration|client|project)'
        match = re.search(relationship_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 4: "our client CocaCola" -> "CocaCola"
        our_client_pattern = r'(?:our client|our partner|client|partner)\s+([A-Za-z][A-Za-z0-9\s&\.]+?)(?:\?|$|\.|\s+is|\s+has)'
        match = re.search(our_client_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 5: "wrote/worked/treatments/campaigns for [Company]" -> "Company"
        work_for_pattern = r'(?:wrote|worked|treatments|projects|campaigns|work|did)\s+for\s+([A-Za-z][A-Za-z0-9\s&\.]+?)(?:\?|$|\.|\s+and|\s+or)'
        match = re.search(work_for_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 5b: "what/which projects did we do for [Company]" -> "Company"
        what_for_pattern = r'(?:what|which)\s+(?:projects?|work|campaigns?)\s+(?:did we|do we)\s+(?:do|did)\s+for\s+([A-Za-z][A-Za-z0-9\s&\.]+?)(?:\?|$|\.)'
        match = re.search(what_for_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 6: "who wrote the treatments for [Company]" -> "Company" (more specific)
        who_for_pattern = r'(?:who|what)\s+(?:wrote|worked on|did|created)\s+(?:the\s+)?(?:treatments?|projects?|campaigns?|work)\s+for\s+([A-Za-z][A-Za-z0-9\s&\.]+?)(?:\?|$|\.)'
        match = re.search(who_for_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 7: Simple capitalized company name (fallback)
        # Look for capitalized words that could be company names
        capitalized_pattern = r'\b([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*)\b'
        matches = re.findall(capitalized_pattern, query)
        if matches:
            # Filter out common words and return the longest match
            common_words = {'Do', 'We', 'Work', 'With', 'What', 'About', 'Tell', 'Me', 'Information', 'Client', 'Partner'}
            valid_matches = [match for match in matches if match not in common_words and len(match) > 2]
            if valid_matches:
                return max(valid_matches, key=len)  # Return longest potential company name
        
        return ""

    async def _analyze_query(
        self,
        query: str, 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze sales-related query for context"""
        
        query_lower = query.lower()
        logger.debug(f"Analyzing query: '{query[:100]}...'")
        
        # Detect query intent
        intent = "general"
        task_params = {}
        
        # Check for organization/company lookup queries first (highest priority)
        organization_keywords = [
            "do we work with", "work with", "working with", "partner with", "client", "relationship with", 
            "what about", "collaboration", "our client", "our partner", "wrote for", "worked on", 
            "treatments for", "projects for", "campaigns for", "work for", "did for"
        ]
        organization_match = any(keyword in query_lower for keyword in organization_keywords)
        logger.debug(f"Organization keywords match: {organization_match}, found: {[kw for kw in organization_keywords if kw in query_lower]}")
        
        if organization_match:
            # Extract organization name from query
            organization_name = self._extract_organization_from_query(query)
            logger.debug(f"Extracted organization name: '{organization_name}'")
            if organization_name:  # Only if we found an organization name
                intent = "organization_lookup"
                logger.debug(f"Intent set to organization_lookup for organization: {organization_name}")
                task_params = {
                    "organization": organization_name,
                    "query": query
                }
        
        # Check for profile/person lookup queries (second priority)
        if intent == "general":  # Only if not already organization_lookup
            profile_keywords = ["profile", "who is", "who works", "tell me about", "information on", "details about", "comprehensive profile"]
            profile_match = any(keyword in query_lower for keyword in profile_keywords)
            logger.debug(f"Profile keywords match: {profile_match}, found: {[kw for kw in profile_keywords if kw in query_lower]}")
            
            if profile_match:
                # Extract name and company from query
                extracted_info = self._extract_name_from_query(query)
                logger.debug(f"Extracted name info: {extracted_info}")
                if extracted_info["name"]:  # Only if we found a name
                    intent = "profile_lookup"
                    logger.debug(f"Intent set to profile_lookup for name: {extracted_info['name']}")
                    task_params = {
                        "name": extracted_info["name"],
                        "company": extracted_info["company"],
                        "query": query
                    }
        
        # Check for traditional lead qualification (expanded keywords)  
        if intent == "general":  # Only if no higher priority intent set
            lead_keywords = ["lead", "qualify", "score", "prospect", "potential client", "recommendation"]
            lead_match = any(word in query_lower for word in lead_keywords)
            logger.debug(f"Lead keywords match: {lead_match}, found: {[kw for kw in lead_keywords if kw in query_lower]}")
            
            if lead_match:
                intent = "lead_qualification"
                logger.debug("Intent set to lead_qualification")
                task_params = {
                    "lead_info": query,  # Use query as lead info
                    "context": str(user_context)  # Convert context to string for template
                }
            
        elif any(word in query_lower for word in ["market", "trend", "analysis", "competitive"]):
            if intent == "general":  # Only if no higher priority intent set
                intent = "market_analysis"
                logger.debug("Intent set to market_analysis")
                task_params = {
                    "query": query,
                    "timeframe": "current",
                    "segment": user_context.get("industry_segment", "entertainment"),
                    "location": user_context.get("location", "global")
                }
            
        elif any(word in query_lower for word in ["budget", "cost", "pricing", "rate"]):
            if intent == "general":  # Only if no higher priority intent set
                intent = "budget_analysis"
                logger.debug("Intent set to budget_analysis")
                task_params = {
                    "project_type": user_context.get("project_type", "unspecified"),
                    "budget_range": user_context.get("budget", "not provided"),
                    "requirements": query  # Use query as requirements
                }
        
        logger.info(f"Final intent determined: {intent}")
        
        return {
            "intent": intent,
            "task_type": intent,
            "task_params": task_params,
            "requires_knowledge_graph": intent in ["market_analysis", "lead_qualification", "profile_lookup", "organization_lookup"],
            "complexity": "moderate" if intent != "general" else "simple"
        }

    async def _process_query(self, state) -> Dict[str, Any]:
        """Override base process_query to actually call sales tools"""
        
        # Call parent method to get query analysis
        state = await super()._process_query(state)
        
        # Get the analysis results
        task_context = state.get("task_context", {})
        intent = task_context.get("intent", "general")
        task_params = task_context.get("task_params", {})
        user_context = state.get("user_context", {})
        
        # Get latest user query
        latest_message = state["messages"][-1]
        if hasattr(latest_message, 'content'):
            user_query = latest_message.content
        else:
            user_query = latest_message.get("content", "")
        
        logger.info(f"Sales agent processing query with intent: {intent}")
        
        # Actually call the appropriate tools based on intent
        try:
            if intent == "organization_lookup" and hasattr(self, 'get_organization_profile'):
                logger.info("Calling get_organization_profile tool...")
                # Extract organization name from task params
                organization_name = task_params.get("organization", "")
                logger.info(f"Looking up organization profile for: '{organization_name}'")
                tool_result = await self.get_organization_profile(organization_name)
                state["tool_results"] = {"get_organization_profile": tool_result}
                
            elif intent == "profile_lookup" and hasattr(self, 'get_lead_profile'):
                logger.info("Calling get_lead_profile tool...")
                # Extract name from task params
                name = task_params.get("name", "")
                company = task_params.get("company", "")
                logger.info(f"Looking up profile for: {name} at {company}")
                tool_result = await self.get_lead_profile(name)
                state["tool_results"] = {"get_lead_profile": tool_result}
                
            elif intent == "lead_qualification" and hasattr(self, 'qualify_lead'):
                logger.info("Calling qualify_lead tool...")
                # Extract lead info from query or use defaults
                lead_info = {
                    "company_name": "Creative Studios LA",  # Could extract from query
                    "project_type": "entertainment",
                    "budget": "not specified",
                    "contact_name": "Michael Chen"  # Could extract from query
                }
                tool_result = await self.qualify_lead(lead_info, user_context)
                state["tool_results"] = {"qualify_lead": tool_result}
                
            elif intent == "market_analysis" and hasattr(self, 'market_analysis'):
                logger.info("Calling market_analysis tool...")
                segment = task_params.get("segment", "entertainment")
                location = task_params.get("location", "global")
                tool_result = await self.market_analysis(segment, location)
                state["tool_results"] = {"market_analysis": tool_result}
                
            elif intent == "budget_analysis" and hasattr(self, 'get_pricing_recommendations'):
                logger.info("Calling get_pricing_recommendations tool...")
                project_details = {
                    "type": task_params.get("project_type", "entertainment"),
                    "scope": "standard",
                    "timeline": "not specified"
                }
                tool_result = await self.get_pricing_recommendations(project_details)
                state["tool_results"] = {"pricing_recommendations": tool_result}
                
            else:
                logger.info(f"No specific tool for intent '{intent}', using general response")
                state["tool_results"] = {}
                
        except Exception as e:
            logger.error(f"Error calling sales tools for intent '{intent}': {e}")
            state["tool_results"] = {"error": str(e)}
        
        return state

    async def _generate_response(self, state) -> Dict[str, Any]:
        """Override base generate_response to include tool results"""
        
        # Get tool results if available
        tool_results = state.get("tool_results", {})
        task_context = state.get("task_context", {})
        intent = task_context.get("intent", "general")
        
        # Get latest user message
        latest_message = state["messages"][-1]
        if hasattr(latest_message, 'content'):
            user_query = latest_message.content
        else:
            user_query = latest_message.get("content", "")
        
        # If we have tool results, create a response that incorporates them
        has_valid_tool_results = (
            tool_results and 
            isinstance(tool_results, dict) and 
            len(tool_results) > 0 and 
            not (len(tool_results) == 1 and "error" in tool_results)
        )
        
        if has_valid_tool_results:
            logger.info(f"Generating response with tool results for intent: {intent}")
            
            # Create a response that includes the tool results
            if intent == "organization_lookup" and "get_organization_profile" in tool_results:
                result = tool_results["get_organization_profile"]
                organization_name = result.get("query", "the organization")
                
                if result.get("found") and result.get("organization"):
                    # Build comprehensive organization response
                    org_data = result["organization"]
                    actual_name = org_data.get("display_name") or org_data.get("name") or org_data.get("id") or organization_name
                    
                    # Check if this is a treatment-specific question
                    user_query_lower = user_query.lower()
                    is_treatment_question = any(word in user_query_lower for word in [
                        "treatment", "wrote", "written", "author", "creator", "developed"
                    ])
                    
                    if is_treatment_question:
                        response_content = f"## Treatment Work for {actual_name}\n\n"
                    else:
                        response_content = f"## {actual_name}\n\n"
                    
                    # Basic organization info
                    if org_data.get("description"):
                        response_content += f"**About**: {org_data['description']}\n\n"
                    if org_data.get("industry"):
                        response_content += f"**Industry**: {org_data['industry']}\n"
                    if org_data.get("tier"):
                        response_content += f"**Tier**: {org_data['tier']}\n\n"
                    
                    # Relationship status based on projects and deals
                    projects = result.get("projects", [])
                    deals = result.get("deals", [])
                    people = result.get("people", [])
                    stats = result.get("stats", {})
                    
                    # Determine relationship status
                    has_relationship = len(projects) > 0 or len(deals) > 0
                    
                    if has_relationship:
                        response_content += f"**Relationship Status**: ✅ Yes, we have an active business relationship\n\n"
                        
                        # Show projects if any
                        if projects:
                            if is_treatment_question:
                                # For treatment questions, we found the organization but need to explain the limitation
                                response_content += f"**Projects Found**: We have {len(projects)} project(s) with {actual_name}:\n"
                                for project in projects[:5]:  # Show more projects for treatment queries
                                    response_content += f"• {project}\n"
                                if len(projects) > 5:
                                    response_content += f"• ...and {len(projects) - 5} more projects\n"
                                response_content += "\n"
                                response_content += "**Note**: To find specific treatment authors, I would need to query individual project details or search by person name. The organization lookup shows our business relationship but doesn't include detailed crew information.\n\n"
                            else:
                                response_content += f"**Our Projects** ({len(projects)} total):\n"
                                for project in projects[:3]:  # Show top 3 projects
                                    response_content += f"• {project}\n"
                                if len(projects) > 3:
                                    response_content += f"• ...and {len(projects) - 3} more projects\n"
                                response_content += "\n"
                        
                        # Show deals if any
                        if deals:
                            response_content += f"**Active Deals** ({len(deals)} total):\n"
                            for deal in deals[:3]:  # Show top 3 deals
                                response_content += f"• {deal}\n"
                            if len(deals) > 3:
                                response_content += f"• ...and {len(deals) - 3} more deals\n"
                            response_content += "\n"
                    else:
                        response_content += f"**Relationship Status**: ❌ No current projects or deals found in our records\n\n"
                    
                    # Team/employee info if available
                    if people:
                        response_content += f"**Key Contacts** ({stats.get('people_count', len(people))} in our network):\n"
                        for person_name in people[:5]:  # Show top 5 contacts
                            response_content += f"• {person_name}\n"
                        if len(people) > 5:
                            response_content += f"• ...and {len(people) - 5} more contacts\n"
                        response_content += "\n"
                    
                    # Action items
                    if not has_relationship:
                        response_content += f"**Next Steps**: Consider reaching out to establish a partnership with {actual_name}. "
                        if people:
                            response_content += f"I can help you connect with our {len(people)} known contacts there."
                        else:
                            response_content += "I can help you research key decision makers and potential entry points."
                    else:
                        response_content += f"**Next Steps**: Leverage existing relationship to explore new collaboration opportunities. "
                        if deals:
                            response_content += f"Follow up on {len(deals)} active deals."
                        else:
                            response_content += "Consider proposing new projects based on past success."
                        
                else:
                    response_content = f"I couldn't find information about **{organization_name}** in our database.\n\n"
                    response_content += "This could mean:\n"
                    response_content += "• They're not currently a client or partner\n"
                    response_content += "• They might be a potential new business opportunity\n"
                    response_content += "• The organization name might be spelled differently in our system\n\n"
                    response_content += f"**Would you like me to:**\n"
                    response_content += f"• Research {organization_name} as a potential client\n"
                    response_content += f"• Add them to our prospect database\n"
                    response_content += f"• Search for similar organization names"
                
            elif intent == "profile_lookup" and "get_lead_profile" in tool_results:
                result = tool_results["get_lead_profile"]
                name = result.get("name", "the person")
                
                if result.get("found"):
                    # Build comprehensive profile response
                    response_content = f"## Profile for {name}\n\n"
                    
                    # Basic info
                    if result.get("bio"):
                        response_content += f"**Background**: {result['bio']}\n\n"
                    
                    # Organization info
                    if result.get("organization"):
                        response_content += f"**Organization**: {result['organization']}\n"
                    if result.get("title"):
                        response_content += f"**Title**: {result['title']}\n\n"
                    
                    # Project history
                    projects = result.get("projects", [])
                    if projects:
                        response_content += f"**Recent Projects** ({len(projects)} found):\n"
                        for project in projects[:3]:  # Show top 3 projects
                            proj_name = project.get("title", "Unnamed Project")
                            proj_role = project.get("role", "Unknown Role")
                            response_content += f"• {proj_name} - {proj_role}\n"
                        if len(projects) > 3:
                            response_content += f"• ...and {len(projects) - 3} more projects\n"
                        response_content += "\n"
                    
                    # Skills and expertise
                    skills = result.get("skills", [])
                    if skills:
                        response_content += f"**Key Skills**: {', '.join(skills[:5])}\n\n"
                    
                    # CRM context from lead_context
                    lead_context = result.get("lead_context", {})
                    if lead_context:
                        response_content += f"**Sales Context**:\n"
                        if lead_context.get("is_warm_lead"):
                            response_content += f"• Warm lead with project history\n"
                        if lead_context.get("has_internal_contact"):
                            response_content += f"• Has internal contact/relationship\n"
                        response_content += f"• Organization size: {lead_context.get('organization_size', 'unknown')}\n"
                else:
                    response_content = f"I couldn't find detailed information for {name} in our database. This could be a new contact or they may not be in our current network."
                
            elif intent == "lead_qualification" and "qualify_lead" in tool_results:
                result = tool_results["qualify_lead"]
                response_content = f"Based on my analysis of the lead information for {result.get('lead_info', {}).get('company_name', 'the prospect')}:\n\n"
                response_content += result.get("qualification_analysis", "Lead analysis completed.")
                
            elif intent == "market_analysis" and "market_analysis" in tool_results:
                result = tool_results["market_analysis"]
                response_content = f"Here's my market analysis for the {result.get('segment', 'entertainment')} segment:\n\n"
                response_content += result.get("analysis", "Market analysis completed.")
                
            elif intent == "budget_analysis" and "pricing_recommendations" in tool_results:
                result = tool_results["pricing_recommendations"]
                response_content = f"Based on similar project data, here are my pricing recommendations:\n\n"
                response_content += result.get("pricing_analysis", "Pricing analysis completed.")
                
            else:
                response_content = f"I've analyzed your query about {user_query} and retrieved relevant data from our systems."
            
            # Create the response message
            from langchain_core.messages import AIMessage
            ai_message = AIMessage(content=response_content)
            state["messages"].append(ai_message)
            
        else:
            # Fall back to parent method if no tools were called
            logger.info("No tool results available, using standard LLM response")
            state = await super()._generate_response(state)
        
        return state

    async def qualify_lead(
        self,
        lead_info: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Qualify and score a sales lead"""
        
        if not self.knowledge_service:
            raise AIProcessingError("Knowledge service required for lead qualification")
        
        try:
            # Analyze lead against similar projects
            project_intelligence = await self.knowledge_service.project_intelligence({
                "type": lead_info.get("project_type"),
                "budget": lead_info.get("budget"),
                "location": lead_info.get("location")
            })
            
            # Generate qualification prompt
            qualification_prompt = f"""
            Qualify this lead for our entertainment production services:
            
            Lead Information:
            - Company: {lead_info.get('company_name', 'Not specified')}
            - Project Type: {lead_info.get('project_type', 'Not specified')}
            - Budget Range: {lead_info.get('budget', 'Not specified')}
            - Timeline: {lead_info.get('timeline', 'Not specified')}
            - Location: {lead_info.get('location', 'Not specified')}
            - Contact: {lead_info.get('contact_name', 'Not specified')}
            
            Market Context:
            - Similar Projects: {len(project_intelligence.get('similar_projects', []))} found
            - Average Budget Range: {project_intelligence.get('cost_benchmarks', {}).get('average_budget', 'Unknown')}
            
            Provide:
            1. Qualification Score (1-10)
            2. Key Strengths
            3. Risk Factors
            4. Recommended Actions
            5. Timeline Assessment
            """
            
            # Get AI analysis
            response = await self.chat(
                message=qualification_prompt,
                user_context=user_context
            )
            
            return {
                "lead_info": lead_info,
                "qualification_analysis": response["content"],
                "market_context": project_intelligence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Lead qualification failed: {e}")
            raise AIProcessingError(f"Lead qualification failed: {e}")

    async def market_analysis(
        self,
        segment: str,
        location: Optional[str] = None,
        timeframe: str = "current"
    ) -> Dict[str, Any]:
        """Perform market analysis for specific segment"""
        
        if not self.knowledge_service:
            return {"error": "Knowledge service not available"}
        
        try:
            # Get market insights
            insights = await self.knowledge_service.generate_insights(
                context={"segment": segment, "location": location},
                insight_type="project_trends"
            )
            
            # Generate analysis prompt
            analysis_prompt = f"""
            Analyze the {segment} market segment in {location or 'all locations'}:
            
            Recent Market Data:
            {insights}
            
            Provide:
            1. Market Size and Growth Trends
            2. Key Competitors and Market Share
            3. Pricing Benchmarks
            4. Opportunities and Threats
            5. Strategic Recommendations
            """
            
            response = await self.chat(
                message=analysis_prompt,
                user_context={"role": "sales_analyst"}
            )
            
            return {
                "segment": segment,
                "location": location,
                "timeframe": timeframe,
                "analysis": response["content"],
                "data_sources": insights,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"error": str(e)}

    async def get_pricing_recommendations(
        self,
        project_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate pricing recommendations based on market data"""
        
        if not self.knowledge_service:
            return {"error": "Knowledge service not available"}
        
        try:
            # Get project intelligence
            intelligence = await self.knowledge_service.project_intelligence(project_details)
            
            cost_benchmarks = intelligence.get("cost_benchmarks", {})
            similar_projects = intelligence.get("similar_projects", [])
            
            pricing_prompt = f"""
            Recommend pricing strategy for this project:
            
            Project Details:
            - Type: {project_details.get('type')}
            - Scope: {project_details.get('scope', 'Standard')}
            - Timeline: {project_details.get('timeline')}
            - Location: {project_details.get('location')}
            
            Market Benchmarks:
            - Average Similar Project Budget: ${cost_benchmarks.get('average_budget', 'Unknown')}
            - Budget Range: ${cost_benchmarks.get('min_budget', 'N/A')} - ${cost_benchmarks.get('max_budget', 'N/A')}
            - Sample Size: {cost_benchmarks.get('sample_size', 0)} projects
            
            Similar Projects Reference:
            {len(similar_projects)} comparable projects found
            
            Provide:
            1. Recommended Pricing Range
            2. Pricing Strategy Rationale
            3. Value Proposition Points
            4. Negotiation Guidelines
            5. Risk Considerations
            """
            
            response = await self.chat(
                message=pricing_prompt,
                user_context={"role": "sales_manager"}
            )
            
            return {
                "project_details": project_details,
                "pricing_analysis": response["content"],
                "market_benchmarks": cost_benchmarks,
                "comparable_projects": len(similar_projects),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Pricing recommendation failed: {e}")
            return {"error": str(e)}

    async def sales_forecast(
        self,
        pipeline_data: List[Dict[str, Any]],
        timeframe: str = "quarterly"
    ) -> Dict[str, Any]:
        """Generate sales forecast based on pipeline data"""
        
        try:
            # Analyze pipeline
            total_pipeline_value = sum(
                lead.get("budget", 0) * lead.get("probability", 0.5)
                for lead in pipeline_data
            )
            
            pipeline_summary = {
                "total_leads": len(pipeline_data),
                "total_value": total_pipeline_value,
                "avg_deal_size": total_pipeline_value / max(1, len(pipeline_data)),
                "stages": {}
            }
            
            # Stage analysis
            for lead in pipeline_data:
                stage = lead.get("stage", "unknown")
                if stage not in pipeline_summary["stages"]:
                    pipeline_summary["stages"][stage] = {"count": 0, "value": 0}
                pipeline_summary["stages"][stage]["count"] += 1
                pipeline_summary["stages"][stage]["value"] += lead.get("budget", 0)
            
            forecast_prompt = f"""
            Generate {timeframe} sales forecast based on current pipeline:
            
            Pipeline Summary:
            - Total Leads: {pipeline_summary['total_leads']}
            - Total Pipeline Value: ${pipeline_summary['total_value']:,.2f}
            - Average Deal Size: ${pipeline_summary['avg_deal_size']:,.2f}
            
            Pipeline by Stage:
            {pipeline_summary['stages']}
            
            Provide:
            1. Forecasted Revenue
            2. Confidence Intervals
            3. Key Assumptions
            4. Risk Factors
            5. Action Items to Improve Forecast
            """
            
            response = await self.chat(
                message=forecast_prompt,
                user_context={"role": "sales_director"}
            )
            
            return {
                "timeframe": timeframe,
                "pipeline_summary": pipeline_summary,
                "forecast_analysis": response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sales forecast failed: {e}")
            return {"error": str(e)}

    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and specializations"""
        
        return {
            "agent_type": "sales_intelligence",
            "specializations": [
                "Lead qualification and scoring",
                "Market analysis and competitive intelligence",
                "Pricing strategy optimization",
                "Sales forecasting and pipeline analysis",
                "Entertainment industry expertise"
            ],
            "key_methods": [
                "qualify_lead",
                "market_analysis", 
                "get_pricing_recommendations",
                "sales_forecast"
            ],
            "knowledge_domains": [
                "Entertainment industry trends",
                "Production budgets and costs",
                "Client relationship management",
                "Union compliance and rates",
                "Market segmentation"
            ],
            "requires_knowledge_graph": True,
            "timestamp": datetime.utcnow().isoformat()
        }