# Talent Acquisition Agent - Detailed Test Scenarios

Advanced test scenarios for validating the TalentAcquisitionAgent's specialized capabilities including creative style matching, crew composition analysis, and talent assessment.

## Agent Capabilities Overview

The TalentAcquisitionAgent specializes in:
- Creative style and concept-based talent matching
- Comprehensive talent experience assessment
- Client relationship leveraging for crew selection  
- Project crew composition analysis and gap identification
- Union compliance and availability coordination

## Deep Dive Test Scenarios

### 1. Creative Style Matching Advanced Scenarios

#### Scenario 1.1: Complex Visual Style Requirements
**Context**: High-concept project requiring specific artistic vision
**Test Prompt**:
```
"I need to find crew for a cyberpunk-themed limited series that combines neon-noir aesthetics with futuristic urban landscapes. The visual style should be similar to 'Blade Runner 2049' meets 'Ghost in the Shell'. Find me a cinematographer, production designer, and VFX supervisor who have experience with this specific aesthetic blend."
```

**Expected Behavior**:
- Uses `find_talent_by_style` method with complex concept matching
- Searches across multiple related creative concepts
- Cross-references projects with similar visual themes
- Provides portfolio examples from matched talent
- Assesses style consistency across different projects

**Validation Points**:
- Returns talent with demonstrable cyberpunk/neon-noir experience
- Includes specific project examples showing style expertise
- Provides availability and rate estimates
- Shows experience level assessment for each recommendation

#### Scenario 1.2: Genre Evolution and Adaptation
**Test Prompt**:
```
"We're producing a psychological thriller that blends traditional suspense with modern interactive storytelling elements. I need a director who has experience with both classic thriller techniques and newer narrative innovations like non-linear storytelling or audience participation elements."
```

**Expected Behavior**:
- Identifies talent with cross-genre experience
- Analyzes evolution of creative approaches in talent portfolios
- Considers innovation and adaptation capabilities
- Provides examples of genre-blending work

### 2. Talent Assessment Complex Scenarios

#### Scenario 2.1: Career Trajectory Analysis
**Context**: Long-term project requiring talent growth assessment
**Test Prompt**:
```
"Assess the career development of editor Sarah Chen over the past 5 years. I need to understand if she's ready to step up from documentaries to high-budget narrative series, considering skill progression, project complexity, and industry reputation."
```

**Expected Behavior**:
- Uses `assess_talent_experience` with career progression analysis
- Tracks project complexity evolution over time
- Evaluates skill set expansion and adaptation
- Provides readiness assessment for role elevation
- Includes industry reputation and peer feedback analysis

**Validation Points**:
- Shows clear progression metrics across time periods
- Identifies skill gaps or areas needing development
- Provides confidence rating for role transition
- Includes comparable talent benchmarking

#### Scenario 2.2: Multi-Domain Expertise Evaluation
**Test Prompt**:
```
"I need to evaluate Marcus Rodriguez who claims expertise in both traditional cinematography and emerging virtual production techniques. Validate his experience across both domains and assess his adaptability to hybrid production environments."
```

**Expected Behavior**:
- Comprehensive skill validation across multiple domains
- Project portfolio analysis for technology adoption
- Assessment of learning curve and adaptation speed
- Evaluation of hybrid production readiness

### 3. Client Experience Leveraging Scenarios

#### Scenario 3.1: Premium Client Relationship Mining
**Context**: High-stakes project requiring proven client relationships
**Test Prompt**:
```
"For our upcoming Netflix original series, I need department heads who have not just worked with Netflix before, but have successful multi-project relationships and understand their specific production standards, approval processes, and quality expectations."
```

**Expected Behavior**:
- Uses `find_client_experienced_talent` with relationship depth analysis
- Evaluates multiple project history with same client
- Assesses success metrics and repeat hiring patterns
- Provides insight into client-specific working relationships

**Validation Points**:
- Shows multi-project history with Netflix
- Includes project success indicators
- Demonstrates familiarity with client processes
- Provides relationship strength assessment

#### Scenario 3.2: Client Transition and Expansion
**Test Prompt**:
```
"We're pitching to Amazon Prime for the first time. Find talent who have successfully transitioned from other major streamers (Netflix, Hulu, HBO Max) to Amazon and can help us understand their unique requirements and working style."
```

**Expected Behavior**:
- Identifies talent with multi-platform experience
- Analyzes successful platform transitions
- Provides insights into platform-specific requirements
- Offers strategic guidance for new client relationships

### 4. Crew Composition and Gap Analysis Scenarios

#### Scenario 4.1: Complex Production Crew Planning
**Context**: Multi-format production requiring specialized crew mix
**Test Prompt**:
```
"Analyze the crew needs for 'Urban Mysteries' - a hybrid production that combines traditional documentary interviews, scripted reenactments, and interactive digital content. What's our current crew composition and what specialized roles do we need to add?"
```

**Expected Behavior**:
- Uses `analyze_project_crew_gaps` with hybrid production analysis
- Identifies standard vs. specialized role requirements
- Calculates crew completion scores across different production formats
- Provides hiring priority recommendations
- Considers cross-functional role capabilities

**Validation Points**:
- Shows detailed role gap analysis
- Provides completion scores for each production format
- Identifies critical vs. optional hiring needs
- Includes budget impact assessment for additional roles

#### Scenario 4.2: International Production Staffing
**Test Prompt**:
```
"We're co-producing a documentary series with filming locations in Japan, Germany, and Brazil. Analyze our crew needs considering local hiring requirements, union regulations, and cultural liaison needs for each location."
```

**Expected Behavior**:
- Multi-location crew analysis
- Local hiring requirement assessment
- Cultural and language consideration
- Union compliance across international locations

### 5. Advanced Talent Matching Scenarios

#### Scenario 5.1: Ensemble Cast Chemistry Assessment
**Context**: Projects requiring strong team dynamics
**Test Prompt**:
```
"I need to build a core creative team (director, DP, production designer) for a character-driven drama series. Beyond individual skills, I need talent who have worked well together before or have complementary working styles that suggest good collaboration potential."
```

**Expected Behavior**:
- Uses collaboration history analysis
- Evaluates working style compatibility
- Identifies successful previous partnerships
- Provides team chemistry recommendations
- Considers personality and communication style factors

#### Scenario 5.2: Crisis Management and Replacement Planning
**Test Prompt**:
```
"Our lead cinematographer on 'Night Visions' just had a family emergency and needs to leave the production. I need immediate replacements who can step in mid-project, match the visual style already established, and work with our existing camera team without major disruption."
```

**Expected Behavior**:
- Emergency replacement scenario handling
- Style consistency requirements
- Team integration capabilities
- Availability for immediate start
- Minimal disruption transition planning

### 6. Union and Compliance Scenarios

#### Scenario 6.1: Union Compliance Validation
**Test Prompt**:
```
"Validate that our proposed crew for the 'Metropolitan Stories' series meets all DGA, IATSE, and SAG-AFTRA requirements for a union production. Identify any compliance gaps and suggest corrections."
```

**Expected Behavior**:
- Comprehensive union requirement checking
- Role-specific compliance validation
- Gap identification and correction suggestions
- Cost implications of compliance requirements

#### Scenario 6.2: Mixed Union and Non-Union Production
**Test Prompt**:
```
"We have a documentary project that will shoot in both union and non-union territories. Help me structure the crew to maintain compliance while optimizing costs across different production phases."
```

**Expected Behavior**:
- Hybrid production structure analysis
- Territory-specific compliance requirements
- Cost optimization across union boundaries
- Crew transition planning between territories

### 7. Performance and Availability Optimization

#### Scenario 7.1: Schedule Optimization and Availability Matching
**Context**: Complex scheduling with multiple talent availability windows
**Test Prompt**:
```
"I have a 6-month production window and need to optimize crew scheduling across three overlapping documentary projects. Identify talent who can work on multiple projects and suggest scheduling to maximize utilization while avoiding conflicts."
```

**Expected Behavior**:
- Multi-project scheduling optimization
- Availability window analysis
- Resource sharing recommendations
- Conflict identification and resolution

#### Scenario 7.2: Budget-Constrained Talent Selection
**Test Prompt**:
```
"Working with a reduced budget for our independent documentary. Find experienced talent willing to work at lower rates, possibly in exchange for career development opportunities, creative control, or profit sharing arrangements."
```

**Expected Behavior**:
- Budget-constrained talent identification
- Alternative compensation structure analysis
- Career development opportunity matching
- Creative incentive alignment

### 8. Integration with Other Systems

#### Scenario 8.1: Talent-to-Sales Feedback Loop
**Context**: Talent recommendations affecting project pricing
**Test Prompt**:
```
"Based on our talent recommendations for the 'Future Cities' documentary, what's the budget impact? Should the sales team adjust pricing or client expectations?"
```

**Expected Behavior**:
- Provides talent cost analysis for sales integration
- Identifies budget impact of crew recommendations
- Suggests pricing adjustments or alternatives
- Maintains communication with sales agent

#### Scenario 8.2: Analytics-Driven Talent Selection
**Test Prompt**:
```
"Our analytics show that projects with certain crew combinations have 30% higher success rates. Use this data to optimize talent recommendations for our upcoming thriller series."
```

**Expected Behavior**:
- Integrates analytics insights into recommendations
- Applies success pattern matching
- Optimizes for proven combination effectiveness
- Provides data-backed recommendation rationale

### 9. Folk API Integration for Talent Management

#### Scenario 9.1: Real-Time Availability Updates
**Test Prompt**:
```
"I need current availability status for our top 5 cinematographer candidates. Some may have recently booked other projects not yet reflected in our knowledge graph."
```

**Expected Behavior**:
- Hybrid Neo4j + Folk API availability queries
- Real-time status updates
- Booking conflict identification
- Alternative candidate prioritization

#### Scenario 9.2: Talent Relationship Management
**Test Prompt**:
```
"Track our engagement history with director Alex Morrison including all outreach, negotiations, and project discussions. I need complete context before our next conversation."
```

**Expected Behavior**:
- Complete engagement history retrieval
- Relationship timeline construction
- Communication context preparation
- Next steps recommendation based on history

## Test Execution Guidelines

### Setup Requirements
- Neo4j with comprehensive talent and project relationship data
- Folk API integration for real-time talent management
- Union regulation databases for compliance checking
- Availability and scheduling data integration

### Data Prerequisites
- Talent profiles with detailed project histories
- Creative concept taxonomies with project mappings
- Client relationship data with success metrics
- Union compliance requirements database

### Performance Benchmarks
- Creative style matching: <4 seconds for complex queries
- Talent assessment: <3 seconds for individual analysis
- Crew gap analysis: <5 seconds for complete project analysis
- Client experience matching: <3 seconds with relationship data

### Success Criteria
- Accurate style-based matching with portfolio validation
- Comprehensive talent assessment with career trajectory analysis
- Effective crew composition optimization with budget considerations
- Seamless client relationship leveraging for strategic advantage
- Real-time availability and compliance validation

---

*Test Scenario Version: 1.0*  
*Agent Version: TalentAcquisitionAgent v2.0*  
*Last Updated: December 2024*