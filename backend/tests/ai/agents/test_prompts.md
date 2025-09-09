# OneVice Multi-Agent System Test Prompts

This document provides comprehensive test prompts to validate all specialized agents and their tools in the OneVice AI platform. Use these prompts to ensure each agent performs correctly across their specialized domains.

## Agent Architecture Overview

The OneVice system features three specialized agents:
- **SalesIntelligenceAgent**: Lead qualification, market analysis, pricing optimization
- **TalentAcquisitionAgent**: Crew matching, style expertise, availability tracking  
- **LeadershipAnalyticsAgent**: Performance analysis, trend insights, document intelligence

Each agent has access to 20+ graph query tools through specialized mixins and integrates with Neo4j, Folk API, and Redis caching.

---

## 1. Sales Intelligence Agent Test Prompts

### Core Sales Functions

#### Lead Qualification Tests

**Prompt 1: Basic Lead Qualification**
```
"I have a potential client, Sarah Johnson at Apex Productions. They're looking to produce a documentary series with a budget of $2.5M over 12 months. Can you qualify this lead and provide a recommendation?"
```
*Expected: Uses qualify_lead method, analyzes project intelligence, provides qualification score*

**Prompt 2: Lead Profile Deep Dive**
```
"Get me a comprehensive profile for Michael Chen who works at Creative Studios LA. I need to understand his project history, organization connections, and decision-making authority."
```
*Expected: Uses get_lead_profile method from CRMToolsMixin, retrieves person details with CRM context*

**Prompt 3: Decision Maker Discovery**
```
"Find all the decision makers at Warner Brothers Entertainment. I need to identify who has budget authority for documentary projects."
```
*Expected: Uses find_decision_makers method, filters by role authority, provides decision maker scores*

#### Market Analysis Tests

**Prompt 4: Market Trend Analysis**
```
"Analyze the current market for reality TV production in Los Angeles. What are the trends, opportunities, and competitive landscape?"
```
*Expected: Uses market_analysis method, leverages knowledge graph for insights*

**Prompt 5: Competitive Intelligence**
```
"I need competitive analysis for the streaming documentary market. Who are the key players, what are typical budgets, and where are the opportunities?"
```
*Expected: Integrates project intelligence with market data, provides strategic recommendations*

#### Pricing Strategy Tests

**Prompt 6: Project Pricing Recommendations**
```
"A client wants to produce a 6-episode true crime series for Netflix with A-list talent. Timeline is 18 months, shooting in New York. What should our pricing strategy be?"
```
*Expected: Uses get_pricing_recommendations method, analyzes similar projects, provides pricing ranges*

**Prompt 7: Custom Budget Analysis**
```
"Analyze pricing for a documentary project: independent film, 90 minutes, $500K budget, shooting in multiple international locations."
```
*Expected: Leverages cost benchmarks, considers location factors, provides detailed analysis*

#### Sales Pipeline Tests

**Prompt 8: Sales Forecast Generation**
```
"Generate a quarterly sales forecast based on our current pipeline: 12 active leads worth $15M total, stages ranging from initial contact to contract negotiation."
```
*Expected: Uses sales_forecast method, analyzes pipeline stages, provides confidence intervals*

#### Deal Attribution Tests

**Prompt 9: Deal Source Tracking**
```
"Who sourced the 'Urban Chronicles' documentary deal? I need attribution for commission calculations."
```
*Expected: Uses get_deal_attribution method, queries Folk API for sourcer information*

**Prompt 10: Live Deal Status**
```
"What's the current status of our Netflix documentary series deal? I need real-time updates."
```
*Expected: Uses get_live_deal_status method, integrates Neo4j + Folk API data*

---

## 2. Talent Acquisition Agent Test Prompts

### Talent Search and Matching

#### Creative Style Matching

**Prompt 11: Style-Based Crew Search**
```
"Find experienced crew for a film noir project. I need a cinematographer and director who have worked on similar atmospheric, high-contrast visual styles."
```
*Expected: Uses find_talent_by_style method, searches projects by concept, returns experienced crew*

**Prompt 12: Genre Expertise Search**
```
"I need a director experienced in psychological thrillers. Show me directors who have worked on projects with dark, suspenseful themes."
```
*Expected: Leverages find_crew_by_style with concept matching, provides genre-specific recommendations*

#### Experience Assessment

**Prompt 13: Individual Talent Assessment**
```
"Assess the experience and suitability of Emma Rodriguez for a lead cinematographer role. Provide a detailed analysis of her project history and capabilities."
```
*Expected: Uses assess_talent_experience method, analyzes project diversity and experience level*

**Prompt 14: Skill-Based Talent Evaluation**
```
"Evaluate David Park's experience with documentary filmmaking. I need to understand his expertise level and recent activity."
```
*Expected: Uses get_talent_profile method, provides talent-specific context and recommendations*

#### Client Experience Matching

**Prompt 15: Client-Experienced Talent**
```
"Find editors who have previously worked with HBO. I want talent familiar with their standards and approval processes."
```
*Expected: Uses find_client_experienced_talent method, queries contributor history with specific client*

**Prompt 16: Relationship Leverage**
```
"Show me all talent who have successful project history with Amazon Studios. Focus on producers and directors."
```
*Expected: Uses find_experienced_crew method, leverages client relationship data*

#### Project Crew Analysis

**Prompt 17: Crew Gap Analysis**
```
"Analyze the crew composition for 'Midnight in Manhattan' project. What roles are missing and what are our hiring priorities?"
```
*Expected: Uses analyze_project_crew_gaps method, identifies missing standard roles, provides hiring strategy*

**Prompt 18: Team Composition Review**
```
"Review the current team for our upcoming thriller series. Are we missing any critical roles? What's our crew completion score?"
```
*Expected: Uses get_project_crew_needs method, calculates completion score against standard roles*

#### Availability and Logistics

**Prompt 19: Multi-Project Talent Search**
```
"Find available sound engineers for a 3-month shoot starting in June. They need experience with outdoor location recording."
```
*Expected: Combines talent search with project matching, considers availability windows*

**Prompt 20: Geographic Talent Matching**
```
"I need local crew in Vancouver for a limited series. Find experienced talent based in that area for key department head positions."
```
*Expected: Uses location-based filtering in talent search, prioritizes local experience*

---

## 3. Leadership Analytics Agent Test Prompts

### Performance Analytics

#### Individual Performance Analysis

**Prompt 21: Team Member Performance Review**
```
"Analyze the performance of Jennifer Walsh over the past 2 years. I need metrics on project involvement, role diversity, and productivity trends."
```
*Expected: Uses analyze_team_member_performance method, provides comprehensive performance metrics*

**Prompt 22: Talent Market Value Assessment**
```
"Assess the market value and career trajectory of cinematographer Mark Stevens. How does his experience compare to industry standards?"
```
*Expected: Leverages performance analysis with market benchmarking*

#### Creative Trend Analysis

**Prompt 23: Concept Trend Tracking**
```
"Analyze trends for 'cyberpunk' themed projects over the last 5 years. Is this concept gaining or losing market interest?"
```
*Expected: Uses analyze_creative_trends method, provides trend direction and client demand patterns*

**Prompt 24: Genre Market Evolution**
```
"Track the evolution of documentary filmmaking trends. What styles are emerging and which clients are driving demand?"
```
*Expected: Analyzes creative concepts, provides market evolution insights*

### Document Intelligence

#### Project Documentation Analysis

**Prompt 25: Project Document Review**
```
"Analyze all documentation for the 'Urban Stories' project. What insights can you extract about project management, communication patterns, and success factors?"
```
*Expected: Uses analyze_project_documentation method, extracts business intelligence from documents*

**Prompt 26: Document Search and Analysis**
```
"Search all project documents for mentions of 'budget overrun' and analyze the common patterns and risk factors."
```
*Expected: Uses search_and_analyze_documents method, provides pattern analysis*

#### Knowledge Extraction

**Prompt 27: Document Insights Mining**
```
"Extract key insights from document ID 'DOC_2024_0156'. Focus on project timeline and resource allocation patterns."
```
*Expected: Uses get_document_insights method with specific field path analysis*

**Prompt 28: Cross-Project Document Analysis**
```
"Find and analyze all documents mentioning 'client feedback' across our documentary projects. What are the common themes?"
```
*Expected: Combines document search with thematic analysis*

### Vendor and Cost Analysis

**Prompt 29: Vendor Performance Review**
```
"Analyze vendor performance for the 'City Lights' project. Which vendors delivered on time and budget, and which had issues?"
```
*Expected: Uses analyze_vendor_performance method, provides cost efficiency analysis*

**Prompt 30: Cost Optimization Analysis**
```
"Review all vendor relationships for our reality TV productions. Where can we optimize costs while maintaining quality?"
```
*Expected: Leverages vendor analysis across multiple projects, provides strategic recommendations*

---

## 4. Graph Tools Integration Test Prompts

### Core Graph Query Testing

#### People and Organization Queries

**Prompt 31: Comprehensive Person Profile**
```
"Get complete profile information for 'Alex Thompson' including all projects, organizations, groups, and contact ownership details."
```
*Expected: Uses get_person_details method, retrieves full profile with relationships*

**Prompt 32: Organization Team Discovery**
```
"Find all people working at 'Meridian Productions' and identify their roles and project involvement."
```
*Expected: Uses find_people_at_organization method, maps team structure*

**Prompt 33: Network Connection Analysis**
```
"Map the professional network connections for 'Lisa Martinez' within 2 degrees of separation."
```
*Expected: Uses get_network_connections method, provides relationship mapping*

#### Project Intelligence Queries

**Prompt 34: Project Detail Extraction**
```
"Get comprehensive information about the 'Desert Winds' project including crew, concepts, client, and timeline details."
```
*Expected: Uses get_project_details method, retrieves complete project profile*

**Prompt 35: Concept-Based Project Discovery**
```
"Find all projects that feature 'film noir' concepts and include related creative themes."
```
*Expected: Uses find_projects_by_concept method with include_related=True*

**Prompt 36: Similar Project Analysis**
```
"Find projects similar to 'Midnight Detective' using vector similarity analysis with 0.8 threshold."
```
*Expected: Uses find_similar_projects method with vector search capabilities*

#### Advanced Search and Analytics

**Prompt 37: Multi-Criteria Project Search**
```
"Search for projects matching: type=documentary, year=2023-2024, client=Netflix, status=completed."
```
*Expected: Uses search_projects_by_criteria method with complex filtering*

**Prompt 38: Collaboration Pattern Analysis**
```
"Find all collaborators for director 'Robert Kim' and analyze collaboration patterns by project type."
```
*Expected: Uses find_collaborators method, provides network analysis*

### Folk API Integration Tests

**Prompt 39: Hybrid Data Retrieval**
```
"Get live status updates for deal 'Streaming Series 2024' combining our knowledge graph with current Folk API data."
```
*Expected: Uses get_deal_details_with_live_status method, hybrid query approach*

**Prompt 40: Deal Attribution with Live Data**
```
"Who sourced the 'Documentary Series Alpha' deal and what's the current pipeline status?"
```
*Expected: Combines get_deal_sourcer with live Folk API integration*

### Document Management Tests

**Prompt 41: Full-Text Document Search**
```
"Search all documents for 'location scouting' and return the top 10 most relevant results."
```
*Expected: Uses search_documents_full_text method with ranking*

**Prompt 42: Document Profile Analysis**
```
"Extract detailed profile information from document 'DOC_2024_0089' focusing on the 'budget.breakdown' section."
```
*Expected: Uses get_document_profile_details with JSON path specification*

---

## 5. Cross-Agent Orchestration Test Prompts

### Multi-Agent Collaboration Scenarios

**Prompt 43: End-to-End Project Planning**
```
"I have a new client inquiry for a 10-episode documentary series about climate change. I need: lead qualification, suitable talent recommendations, and competitive pricing analysis."
```
*Expected: Orchestrates Sales Agent (qualification), Talent Agent (recommendations), and potentially Analytics (market data)*

**Prompt 44: Comprehensive Client Onboarding**
```
"Netflix wants to explore a new true-crime series. Provide: market opportunity analysis, experienced crew recommendations, similar project benchmarks, and pricing strategy."
```
*Expected: Coordinates all three agents for complete client analysis*

**Prompt 45: Project Resource Optimization**
```
"For our upcoming thriller series, I need: crew gap analysis, budget optimization recommendations, vendor performance insights, and market positioning analysis."
```
*Expected: Leverages Talent Agent (crew analysis) and Analytics Agent (optimization insights)*

### Data Handoff Validation

**Prompt 46: Talent-to-Sales Pipeline**
```
"Based on the crew recommendations for 'Urban Chronicles', what's the budget impact and pricing implications?"
```
*Expected: Talent Agent provides crew data, Sales Agent analyzes cost implications*

**Prompt 47: Analytics-to-Talent Intelligence**
```
"Our trend analysis shows growing demand for cyberpunk projects. Find talent with relevant experience and assess availability."
```
*Expected: Analytics provides trend data, Talent Agent matches to available crew*

---

## 6. Error Handling and Edge Case Test Prompts

### Data Validation Tests

**Prompt 48: Missing Person Query**
```
"Find information about 'Nonexistent Person XYZ' and handle the not-found scenario gracefully."
```
*Expected: Graceful error handling, clear not-found messaging*

**Prompt 49: Invalid Project Search**
```
"Get details for project 'This Project Does Not Exist' and provide appropriate fallback responses."
```
*Expected: Proper error handling with suggested alternatives*

### Integration Failure Scenarios

**Prompt 50: Network Connectivity Issues**
```
"What happens when Folk API is unavailable during a live deal status query?"
```
*Expected: Graceful fallback to cached/graph data, clear status indication*

**Prompt 51: Cache Invalidation Testing**
```
"Test cache behavior when Redis is unavailable during high-frequency person detail queries."
```
*Expected: Continues operation without caching, maintains performance*

### Permission and Access Control

**Prompt 52: Data Sensitivity Handling**
```
"Query for highly confidential project information and verify appropriate access controls are enforced."
```
*Expected: Respects data sensitivity levels, applies proper access controls*

**Prompt 53: Role-Based Query Restrictions**
```
"Test analyst-level user trying to access executive-level financial data."
```
*Expected: Proper role-based access control, clear permission messaging*

---

## Usage Instructions

### Running Individual Tests
Use each prompt as a direct query to the respective agent through the OneVice API or WebSocket interface.

### Test Coverage Validation
- **Agent Methods**: 52+ prompts covering all specialized agent methods
- **Graph Tools**: 20+ graph query methods tested across all scenarios  
- **Integration Points**: Neo4j, Folk API, Redis caching, and LLM routing
- **Error Scenarios**: Missing data, network failures, permission boundaries

### Performance Benchmarks
- Response time targets: <2s for cached queries, <5s for complex graph traversals
- Cache hit rates: >70% for person/project queries
- Folk API integration: <3s for hybrid queries
- Concurrent load: Support 10+ simultaneous agent queries

### Continuous Validation
Run these prompts regularly to:
- Validate agent functionality after updates
- Ensure integration point stability  
- Monitor performance benchmarks
- Test new features and capabilities

---

*Document Version: 1.0*  
*Last Updated: December 2024*  
*Test Coverage: 50+ specialized agent test scenarios*