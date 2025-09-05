# Sales Intelligence Agent - Detailed Test Scenarios

Advanced test scenarios for validating the SalesIntelligenceAgent's specialized capabilities including CRM integration, pricing optimization, and market intelligence.

## Agent Capabilities Overview

The SalesIntelligenceAgent specializes in:
- Lead qualification and scoring with project intelligence
- Market analysis leveraging knowledge graph insights  
- Pricing strategy optimization using cost benchmarks
- Sales forecasting with pipeline analysis
- Deal attribution through Folk API integration

## Deep Dive Test Scenarios

### 1. Lead Qualification Advanced Scenarios

#### Scenario 1.1: Complex Lead with Multiple Decision Makers
**Context**: Large production company with complex hierarchy
**Test Prompt**:
```
"I've been contacted by Amanda Richardson, VP of Development at Stellar Productions. They're interested in a 12-episode documentary series about renewable energy, budget range $5-8M, 18-month timeline. The project would involve multiple stakeholders including their CEO Mark Stevens and Head of Content Lisa Park. Can you qualify this lead and identify all decision makers I should engage with?"
```

**Expected Behavior**:
- Uses `qualify_lead` method with complex lead info
- Leverages `find_decision_makers` to identify all stakeholders
- Analyzes project intelligence for similar documentary series
- Provides qualification score with stakeholder engagement strategy
- Returns decision maker hierarchy with authority levels

**Validation Points**:
- Qualification score between 1-10 with clear rationale
- Complete stakeholder mapping from organization data
- Market context from similar projects in knowledge graph
- Recommended next steps for multi-contact approach

#### Scenario 1.2: Lead with Incomplete Information
**Test Prompt**:
```
"I have a potential lead from John at some media company in New York. He mentioned wanting to do 'something documentary-related' but didn't provide budget or timeline details. How should I qualify and proceed with this lead?"
```

**Expected Behavior**:
- Handles incomplete information gracefully
- Provides risk assessment for unclear leads
- Suggests information gathering strategies
- Uses market data to provide range estimates

### 2. Market Analysis Complex Scenarios

#### Scenario 2.1: Multi-Segment Market Analysis
**Test Prompt**:
```
"Analyze the streaming documentary market across three segments: true crime, environmental, and biographical. I need to understand which segment has the highest growth potential for the next 18 months, considering both Netflix and HBO as primary targets."
```

**Expected Behavior**:
- Uses `market_analysis` for each segment
- Compares growth trajectories and opportunities
- Analyzes client-specific preferences (Netflix vs HBO)
- Provides strategic recommendations with data backing

#### Scenario 2.2: Geographic Market Expansion
**Test Prompt**:
```
"We're considering expanding into the European market for documentary production services. Analyze the UK and Germany markets specifically - what are the opportunities, local competition, and cultural considerations for American production companies?"
```

**Expected Behavior**:
- Geographic market analysis with location-specific insights
- Cultural and regulatory considerations
- Competitive landscape analysis
- Market entry strategy recommendations

### 3. Pricing Strategy Advanced Scenarios

#### Scenario 3.1: Premium Pricing Strategy
**Test Prompt**:
```
"A major streaming platform wants an exclusive 8-part documentary series featuring A-list celebrity interviews, international filming locations, and premium production values. Budget discussions start at $15M. How should we position our pricing for maximum profitability while remaining competitive?"
```

**Expected Behavior**:
- Uses `get_pricing_recommendations` with premium positioning
- Analyzes comparable high-budget productions
- Considers value-add opportunities
- Provides negotiation strategy for premium market

#### Scenario 3.2: Competitive Bid Scenario
**Test Prompt**:
```
"We're bidding against 3 other production companies for a mid-budget reality series. Client has indicated budget is fixed at $2.5M for 6 episodes. How do we optimize our proposal to win while maintaining margins?"
```

**Expected Behavior**:
- Competitive pricing analysis
- Value proposition optimization
- Risk assessment for fixed-budget projects
- Margin protection strategies

### 4. Sales Forecasting Complex Scenarios

#### Scenario 4.1: Pipeline Analysis with Seasonal Factors
**Test Prompt**:
```
"Generate a sales forecast considering our pipeline of 15 active opportunities totaling $25M, but factor in that Q4 typically sees 40% of annual closures while Q1 is traditionally slow. Also consider that 3 of our biggest deals are dependent on network programming decisions in February."
```

**Expected Behavior**:
- Uses `sales_forecast` with seasonality considerations
- Risk adjustment for programming-dependent deals
- Quarterly variance modeling
- Confidence intervals with seasonal factors

### 5. CRM Tools Integration Tests

#### Scenario 5.1: Comprehensive Lead Profile with Relationship Mapping
**Test Prompt**:
```
"Build a complete profile for Michael Zhang, including all his project history, current organization affiliations, and any internal relationships our team has with him or his network. I need this for a major pitch next week."
```

**Expected Behavior**:
- Uses `get_lead_profile` from CRMToolsMixin
- Maps all relationship connections
- Identifies internal contact owners
- Provides relationship leverage opportunities

#### Scenario 5.2: Deal Attribution and Commission Tracking  
**Test Prompt**:
```
"I need to track the attribution chain for our 'Urban Stories' documentary deal that closed last month. Who sourced it, what was the progression, and what commission structure applies?"
```

**Expected Behavior**:
- Uses `get_deal_attribution` method
- Tracks complete sourcing chain
- Integrates with Folk API for live status
- Provides commission calculation data

### 6. Folk API Integration Scenarios

#### Scenario 6.1: Live Deal Status with CRM Sync
**Test Prompt**:
```
"What's the current status of all our active deals in the pipeline? I need real-time updates that combine our knowledge graph data with the latest activity from Folk CRM."
```

**Expected Behavior**:
- Uses `get_live_deal_status` for multiple deals
- Hybrid Neo4j + Folk API queries
- Real-time status synchronization
- Comprehensive pipeline dashboard data

#### Scenario 6.2: CRM Data Validation and Cleanup
**Test Prompt**:
```
"I noticed some discrepancies between our knowledge graph and Folk CRM for contact information. Can you identify and reconcile any data mismatches for our top 10 active prospects?"
```

**Expected Behavior**:
- Cross-references Neo4j and Folk data
- Identifies data inconsistencies
- Suggests data cleanup priorities
- Maintains data integrity across systems

### 7. Performance and Error Handling

#### Scenario 7.1: High-Volume Lead Processing
**Test Prompt**:
```
"I just imported 50 new leads from a trade show. Can you batch process these for qualification scores and prioritization? I need the top 10 qualified leads by end of day."
```

**Expected Behavior**:
- Handles batch lead processing efficiently
- Uses caching to optimize performance
- Provides ranked lead prioritization
- Maintains response quality under load

#### Scenario 7.2: Knowledge Graph Unavailable Fallback
**Test Prompt**:
```
"Our knowledge graph seems to be having connectivity issues. I still need to qualify this urgent lead from Discovery Channel. What can you provide using available data sources?"
```

**Expected Behavior**:
- Graceful degradation when Neo4j unavailable
- Falls back to Folk API and cached data
- Provides clear limitations notice
- Maintains core functionality where possible

### 8. Integration with Other Agents

#### Scenario 8.1: Sales-to-Talent Handoff
**Test Prompt**:
```
"I just closed a deal for a historical documentary series. The client specifically requested crew with period piece experience. Can you provide the deal context to the talent team for crew recommendations?"
```

**Expected Behavior**:
- Provides structured deal information for talent handoff
- Includes client requirements and constraints
- Maintains context through agent coordination
- Enables seamless workflow transition

## Test Execution Guidelines

### Setup Requirements
- Neo4j knowledge graph with sample entertainment industry data
- Folk API integration with test CRM data
- Redis caching layer configured
- LLM routing to Together.ai with fallback to Anthropic

### Data Prerequisites
- Sample leads with varied completeness levels
- Organization hierarchies with decision maker roles
- Project benchmarking data for pricing analysis
- Historical deal pipeline data for forecasting

### Performance Benchmarks
- Lead qualification: <3 seconds for complete profiles
- Market analysis: <5 seconds for single segment
- Pricing recommendations: <4 seconds with benchmark data
- Deal attribution: <2 seconds with Folk API integration

### Success Criteria
- Accurate qualification scores with clear methodology
- Market insights backed by knowledge graph data
- Pricing recommendations within industry benchmarks
- Seamless CRM integration with data consistency
- Graceful error handling and fallback behaviors

---

*Test Scenario Version: 1.0*  
*Agent Version: SalesIntelligenceAgent v2.0*  
*Last Updated: December 2024*