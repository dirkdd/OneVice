# OneVice Architecture Diagrams

**Version:** 2.0  
**Date:** September 1, 2025  
**Status:** Design Complete

## 1. System Component Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Next.js 15.4 Frontend<br/>React 19 + TypeScript 5.6<br/>Glassmorphic Design System<br/>Real-time WebSocket]
        Mobile[Mobile Web Interface<br/>Responsive Design<br/>Touch Optimized]
    end
    
    subgraph "Authentication & Security Layer"
        Clerk[Clerk Authentication<br/>JWT Token Management<br/>User Profile Management]
        Okta[Okta SSO Integration<br/>Enterprise Directory<br/>Role Synchronization]
        RBAC[RBAC Enforcement<br/>6-Level Data Sensitivity<br/>Role-Based Filtering]
    end
    
    subgraph "API & Gateway Layer"
        Gateway[FastAPI 0.115.x Gateway<br/>Request Validation<br/>Rate Limiting<br/>WebSocket Management]
        LB[Load Balancer<br/>HAProxy/Nginx<br/>SSL Termination<br/>Health Checking]
    end
    
    subgraph "AI Agent Orchestration Layer"
        Supervisor[LangGraph Supervisor<br/>Agent Routing<br/>Workflow Coordination]
        
        subgraph "Specialized AI Agents"
            SA[Sales Intelligence Agent<br/>• Contact Research<br/>• Company Analysis<br/>• Relationship Mapping]
            CSA[Case Study Agent<br/>• Project Matching<br/>• Template Generation<br/>• Portfolio Assembly]
            TDA[Talent Discovery Agent<br/>• Multi-faceted Search<br/>• Availability Prediction<br/>• Skill Matching]
            BSA[Bidding Support Agent<br/>• Union Rule Integration<br/>• Budget Analysis<br/>• Risk Assessment]
        end
        
        SFN[Security Filtering Node<br/>Role-Based Response Filtering<br/>Data Sensitivity Control<br/>Audit Logging]
        
        Memory[LangMem Memory Management<br/>User Profiles<br/>Episode Learning<br/>Domain Knowledge]
    end
    
    subgraph "Data & Knowledge Layer"
        Graph[Neo4j 5.25.x Graph Database<br/>Entertainment Industry Ontology<br/>Vector Search Integration<br/>Relationship Analytics]
        
        Cache[Redis 7.4.x Cache Layer<br/>Session Management<br/>Query Result Caching<br/>Message Queuing]
        
        Vector[Vector Store<br/>Document Embeddings<br/>Semantic Search<br/>Similarity Matching]
    end
    
    subgraph "LLM & AI Layer"
        Router[LLM Router<br/>Model Selection<br/>Cost Optimization<br/>Load Distribution]
        
        Local[Local Llama<br/>Sensitive Data Processing<br/>On-Premise Inference<br/>Privacy Compliance]
        
        Claude[Anthropic Claude<br/>Complex Reasoning<br/>Strategic Analysis<br/>Natural Language]
        
        Gemini[Google Gemini<br/>Multimodal Processing<br/>Long Context Analysis<br/>Document Understanding]
    end
    
    subgraph "External Integration Layer"
        Unions[Union APIs<br/>IATSE<br/>DGA<br/>SAG-AFTRA<br/>Local 399]
        
        Industry[Industry Data Sources<br/>IMDb Pro<br/>The Numbers<br/>Box Office Mojo<br/>Variety Intelligence]
        
        Talent[Talent Databases<br/>Casting Networks<br/>Agency Rosters<br/>Union Directories]
    end
    
    subgraph "Infrastructure & Monitoring Layer"
        Observability[LangSmith Observability<br/>Performance Monitoring<br/>Cost Tracking<br/>Quality Metrics]
        
        Logging[Centralized Logging<br/>Audit Trails<br/>Error Tracking<br/>Security Events]
        
        Backup[Backup & Recovery<br/>Data Replication<br/>Disaster Recovery<br/>Business Continuity]
    end
    
    UI --> Gateway
    Mobile --> Gateway
    Gateway --> Clerk
    Clerk --> Okta
    Gateway --> Supervisor
    
    Supervisor --> SA
    Supervisor --> CSA
    Supervisor --> TDA
    Supervisor --> BSA
    Supervisor --> Memory
    
    SA --> SFN
    CSA --> SFN
    TDA --> SFN
    BSA --> SFN
    
    SFN --> Graph
    Memory --> Cache
    Graph --> Vector
    
    Supervisor --> Router
    Router --> Local
    Router --> Claude
    Router --> Gemini
    
    BSA --> Unions
    SA --> Industry
    TDA --> Talent
    
    Gateway -.-> Observability
    SFN -.-> Logging
    Graph -.-> Backup
    
    style UI fill:#1e293b,stroke:#3b82f6,stroke-width:2px
    style Supervisor fill:#065f46,stroke:#10b981,stroke-width:2px
    style Graph fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style Router fill:#581c87,stroke:#a855f7,stroke-width:2px
```

## 2. Data Flow Architecture

```mermaid
graph TD
    subgraph "User Interaction Flow"
        User[User Query<br/>Natural Language]
        Auth[Authentication Check<br/>Clerk JWT Validation]
        Role[Role Identification<br/>RBAC Context Loading]
    end
    
    subgraph "Query Processing Pipeline"
        Route[Query Routing<br/>Intent Classification<br/>Agent Selection]
        Memory[Memory Retrieval<br/>User Context<br/>Historical Patterns]
        Enhance[Query Enhancement<br/>Context Integration<br/>Personalization]
    end
    
    subgraph "Agent Execution Environment"
        Agent[Selected AI Agent<br/>Specialized Processing]
        
        subgraph "Data Sources"
            GraphQuery[Neo4j Graph Query<br/>Relationship Traversal<br/>Entity Extraction]
            VectorSearch[Vector Similarity<br/>Semantic Matching<br/>Content Retrieval]
            ExternalAPI[External APIs<br/>Union Rules<br/>Industry Data]
        end
        
        Synthesis[Response Synthesis<br/>Multi-source Integration<br/>Context Aggregation]
    end
    
    subgraph "Security & Filtering"
        Security[Security Filtering<br/>RBAC Application<br/>Data Sensitivity Check]
        
        Filter[Content Filtering<br/>Budget Range Conversion<br/>PII Removal]
        
        Audit[Audit Logging<br/>Access Tracking<br/>Compliance Recording]
    end
    
    subgraph "Response Delivery"
        Stream[WebSocket Streaming<br/>Real-time Delivery<br/>Chunk Processing]
        
        Cache[Result Caching<br/>Performance Optimization<br/>Future Query Acceleration]
        
        UI[Frontend Update<br/>UI State Management<br/>User Notification]
    end
    
    subgraph "Background Processing"
        MemoryExtract[Memory Extraction<br/>Interaction Learning<br/>Pattern Recognition]
        
        MetricsUpdate[Metrics Update<br/>Performance Tracking<br/>Quality Assessment]
        
        Knowledge[Knowledge Update<br/>Domain Learning<br/>Fact Validation]
    end
    
    User --> Auth --> Role --> Route
    Route --> Memory --> Enhance --> Agent
    
    Agent --> GraphQuery
    Agent --> VectorSearch  
    Agent --> ExternalAPI
    
    GraphQuery --> Synthesis
    VectorSearch --> Synthesis
    ExternalAPI --> Synthesis
    
    Synthesis --> Security --> Filter --> Audit
    
    Audit --> Stream --> Cache --> UI
    
    Filter -.-> MemoryExtract
    Stream -.-> MetricsUpdate
    Synthesis -.-> Knowledge
    
    style User fill:#1e293b,stroke:#3b82f6,stroke-width:2px
    style Agent fill:#065f46,stroke:#10b981,stroke-width:2px
    style Security fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style Stream fill:#581c87,stroke:#a855f7,stroke-width:2px
```

## 3. Database Schema Relationships

```mermaid
erDiagram
    PERSON {
        uuid id PK
        string name
        enum role_type
        enum union_status
        array specialization
        json contact_info
        string bio
        int years_experience
        string location
        enum availability_status
        array bio_embedding
        array skills_embedding
        datetime created_at
        datetime updated_at
    }
    
    PROJECT {
        uuid id PK
        string name
        enum type
        enum budget_tier
        float exact_budget
        enum union_status
        date completion_date
        date production_date
        enum status
        int duration
        enum format
        array genre
        array awards
        int views
        array platform
        array concept_embedding
        array description_embedding
        datetime created_at
        datetime updated_at
    }
    
    ORGANIZATION {
        uuid id PK
        string name
        enum type
        string industry
        enum tier
        string location
        string website
        json contact_info
        string annual_revenue
        int employee_count
        int founded_year
        datetime created_at
        datetime updated_at
    }
    
    CREATIVE_CONCEPT {
        uuid id PK
        string concept
        enum category
        string description
        array tags
        string inspiration_source
        enum difficulty_level
        enum budget_impact
        array concept_embedding
        datetime created_at
    }
    
    DOCUMENT {
        uuid id PK
        string title
        enum type
        int sensitivity_level
        string file_path
        enum file_type
        date created_date
        date modified_date
        int word_count
        text full_text_content
        string summary
        array content_embedding
        array summary_embedding
    }
    
    UNION {
        uuid id PK
        string name
        enum type
        string local_number
        string jurisdiction
        json contract_details
        json current_rates
        datetime rules_last_updated
    }
    
    %% Relationships
    PERSON ||--o{ PROJECT : DIRECTED
    PERSON ||--o{ PROJECT : CREATIVE_DIRECTED
    PERSON ||--o{ PROJECT : PERFORMED_IN
    PERSON ||--o{ PROJECT : PRODUCED
    PERSON ||--o{ ORGANIZATION : WORKS_FOR
    PERSON ||--o{ PERSON : COLLABORATED_WITH
    PERSON ||--|| UNION : MEMBER_OF
    
    PROJECT ||--|| ORGANIZATION : FOR_CLIENT
    PROJECT ||--|| ORGANIZATION : PRODUCED_BY
    PROJECT ||--o{ CREATIVE_CONCEPT : INCORPORATES
    PROJECT ||--o{ PROJECT : SIMILAR_TO
    PROJECT ||--|| UNION : GOVERNED_BY
    
    DOCUMENT ||--o{ PROJECT : DESCRIBES
    DOCUMENT ||--o{ PERSON : MENTIONS
    DOCUMENT ||--o{ ORGANIZATION : REFERENCES
    
    CREATIVE_CONCEPT ||--o{ CREATIVE_CONCEPT : INFLUENCES
```

## 4. Authentication & Authorization Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant C as Clerk
    participant O as Okta SSO
    participant G as API Gateway
    participant R as RBAC Filter
    participant A as AI Agents
    participant N as Neo4j
    participant M as Memory Store
    
    U->>F: Access OneVice App
    F->>C: Check Authentication
    
    alt New User - SSO Login
        C->>O: Redirect to Okta
        O->>U: SSO Login Page
        U->>O: Enterprise Credentials
        O->>C: User Profile + Roles
        C->>F: JWT Token + User Data
    else Existing User - Email Login
        C->>U: Email/Password Form
        U->>C: Credentials
        C->>C: Validate Credentials
        C->>F: JWT Token + User Data
    end
    
    F->>F: Store User Session
    U->>F: Send Chat Query
    F->>G: WebSocket Message + JWT
    G->>C: Validate JWT Token
    C-->>G: User Claims + Role
    
    G->>R: Apply Initial RBAC
    R->>A: Route to Appropriate Agent
    
    A->>M: Retrieve User Memory
    M-->>A: Contextual Information
    
    A->>N: Execute Graph Query
    N-->>A: Raw Graph Results
    
    A->>R: Apply Final RBAC Filter
    R->>R: Filter by Role + Sensitivity
    
    R-->>G: Filtered Response
    G-->>F: Streaming Response
    F-->>U: Real-time Display
    
    par Background Processing
        R->>M: Store Interaction Memory
        R->>G: Log Audit Event
        A->>N: Update Usage Metrics
    end
```

## 5. Multi-Agent Workflow Architecture

```mermaid
graph TD
    subgraph "Query Processing"
        Query[User Query<br/>Natural Language Input]
        Classification[Query Classification<br/>Intent Analysis<br/>Entity Extraction]
        Routing[Agent Routing<br/>Best Agent Selection<br/>Confidence Scoring]
    end
    
    subgraph "LangGraph Supervisor Pattern"
        Supervisor[Supervisor Node<br/>Workflow Coordination<br/>State Management]
        
        subgraph "AI Agent Pool"
            Sales[Sales Intelligence Agent<br/>🎯 Contact Research<br/>🏢 Company Analysis<br/>📊 Market Intelligence]
            
            Case[Case Study Agent<br/>📁 Project Similarity<br/>🎨 Creative Matching<br/>📋 Portfolio Assembly]
            
            Talent[Talent Discovery Agent<br/>👥 Multi-faceted Search<br/>📅 Availability Checking<br/>🎭 Skill Assessment]
            
            Bidding[Bidding Support Agent<br/>💰 Budget Analysis<br/>⚖️ Union Rule Integration<br/>📈 Risk Assessment]
        end
        
        Security[Security Filtering Node<br/>🔒 RBAC Enforcement<br/>🛡️ Data Sensitivity Filter<br/>📝 Audit Logging]
        
        Memory[LangMem Memory Node<br/>🧠 User Profile Management<br/>📚 Episode Learning<br/>🎭 Domain Knowledge]
    end
    
    subgraph "Knowledge Sources"
        Graph[Neo4j Knowledge Graph<br/>👤 Person Relationships<br/>🎬 Project History<br/>🏢 Organization Data]
        
        Vector[Vector Store<br/>📄 Document Embeddings<br/>🔍 Semantic Search<br/>📊 Similarity Matching]
        
        External[External APIs<br/>⚖️ Union Rules (IATSE, DGA)<br/>🎬 Industry Data (IMDb)<br/>📊 Market Intelligence]
    end
    
    subgraph "Response Processing"
        Synthesis[Response Synthesis<br/>Multi-source Integration<br/>Context Aggregation<br/>Quality Validation]
        
        Streaming[Real-time Streaming<br/>WebSocket Delivery<br/>Chunk Processing<br/>Live Updates]
        
        Caching[Result Caching<br/>Performance Optimization<br/>Future Query Acceleration<br/>Role-based Storage]
    end
    
    Query --> Classification --> Routing --> Supervisor
    
    Supervisor --> Sales
    Supervisor --> Case
    Supervisor --> Talent
    Supervisor --> Bidding
    
    Sales --> Graph
    Sales --> External
    Case --> Graph
    Case --> Vector
    Talent --> Graph
    Talent --> External
    Bidding --> Graph
    Bidding --> External
    
    Sales --> Security
    Case --> Security
    Talent --> Security
    Bidding --> Security
    
    Security --> Memory
    Security --> Synthesis
    
    Memory --> Graph
    Memory --> Vector
    
    Synthesis --> Streaming --> Caching
    
    style Supervisor fill:#065f46,stroke:#10b981,stroke-width:3px
    style Security fill:#7c2d12,stroke:#ea580c,stroke-width:3px
    style Graph fill:#1e40af,stroke:#3b82f6,stroke-width:2px
    style Memory fill:#581c87,stroke:#a855f7,stroke-width:2px
```

## 6. Real-Time Communication Architecture

```mermaid
sequenceDiagram
    participant Frontend as Next.js Frontend
    participant Gateway as FastAPI Gateway
    participant Auth as Clerk Auth
    participant Supervisor as LangGraph Supervisor
    participant Agent as AI Agent
    participant Security as Security Filter
    participant Memory as LangMem
    participant Neo4j as Knowledge Graph
    participant User as End User
    
    User->>Frontend: Send Message
    Frontend->>Gateway: WebSocket Message + JWT
    
    Gateway->>Auth: Validate JWT Token
    Auth-->>Gateway: User Claims + Role
    
    Gateway->>Supervisor: Initialize Agent State
    Note over Supervisor: State includes user_id, role, query, context
    
    Supervisor->>Supervisor: Analyze Query for Routing
    Supervisor->>Agent: Route to Best Agent
    
    Agent->>Memory: Retrieve Relevant Memories
    Memory-->>Agent: User Context + Domain Knowledge
    
    Agent->>Neo4j: Execute Knowledge Graph Query
    Neo4j-->>Agent: Graph Results + Relationships
    
    Agent->>Agent: Process & Synthesize Response
    Agent->>Security: Apply RBAC Filtering
    
    Security->>Security: Filter by Role + Sensitivity
    Security-->>Gateway: Filtered Response Chunks
    
    loop Streaming Response
        Gateway-->>Frontend: Stream Chunk
        Frontend-->>User: Display Chunk
    end
    
    Gateway-->>Frontend: Stream Complete Signal
    
    par Background Processing
        Security->>Memory: Store Interaction Memory
        Security->>Gateway: Log Audit Event
        Agent->>Neo4j: Update Usage Metrics
    end
```

## 7. Security Architecture Layers

```mermaid
graph TB
    subgraph "External Security Perimeter"
        WAF[Web Application Firewall<br/>DDoS Protection<br/>Bot Detection<br/>Geographic Filtering]
        
        CDN[Content Delivery Network<br/>SSL/TLS Termination<br/>Edge Caching<br/>Attack Mitigation]
    end
    
    subgraph "Network Security Layer"
        LB[Load Balancer<br/>SSL/TLS Encryption<br/>Health Monitoring<br/>Traffic Distribution]
        
        VPC[Virtual Private Cloud<br/>Network Isolation<br/>Subnet Segmentation<br/>Private Communications]
    end
    
    subgraph "Application Security Layer"
        Auth[Authentication Layer<br/>Clerk + Okta SSO<br/>JWT Token Management<br/>Multi-factor Authentication]
        
        RBAC[Authorization Layer<br/>Role-Based Access Control<br/>6-Level Data Sensitivity<br/>Dynamic Permissions]
        
        API[API Security<br/>Request Validation<br/>Rate Limiting<br/>Input Sanitization]
    end
    
    subgraph "Data Security Layer"
        Encryption[Data Encryption<br/>AES-256 Encryption<br/>Key Management<br/>Field-level Protection]
        
        Filter[Content Filtering<br/>Response Sanitization<br/>PII Detection<br/>Sensitive Data Removal]
        
        Audit[Audit & Compliance<br/>Access Logging<br/>Change Tracking<br/>Regulatory Compliance]
    end
    
    subgraph "Infrastructure Security"
        Monitor[Security Monitoring<br/>Threat Detection<br/>Anomaly Analysis<br/>Incident Response]
        
        Backup[Secure Backup<br/>Encrypted Storage<br/>Disaster Recovery<br/>Data Integrity]
        
        Network[Network Security<br/>Firewall Rules<br/>Intrusion Detection<br/>Traffic Analysis]
    end
    
    WAF --> CDN --> LB --> VPC
    VPC --> Auth --> RBAC --> API
    API --> Encryption --> Filter --> Audit
    Audit --> Monitor --> Backup --> Network
    
    style Auth fill:#065f46,stroke:#10b981,stroke-width:2px
    style RBAC fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style Encryption fill:#581c87,stroke:#a855f7,stroke-width:2px
    style Monitor fill:#1e40af,stroke:#3b82f6,stroke-width:2px
```

## 8. Performance & Scalability Architecture

```mermaid
graph TB
    subgraph "Frontend Performance"
        SSR[Next.js SSR/SSG<br/>Server-Side Rendering<br/>Static Generation<br/>Incremental Regeneration]
        
        PPR[Partial Prerendering<br/>React Suspense<br/>Streaming Components<br/>Progressive Loading]
        
        Cache[Client-Side Caching<br/>Service Worker<br/>Local Storage<br/>IndexedDB]
    end
    
    subgraph "API Performance"
        Gateway[API Gateway<br/>Request Routing<br/>Load Balancing<br/>Connection Pooling]
        
        RateLimit[Rate Limiting<br/>User-based Throttling<br/>Resource Protection<br/>Fair Usage]
        
        Compression[Response Compression<br/>Gzip/Brotli<br/>JSON Optimization<br/>Binary Protocols]
    end
    
    subgraph "Application Scaling"
        HPA[Horizontal Pod Autoscaler<br/>CPU/Memory Scaling<br/>Custom Metrics<br/>Predictive Scaling]
        
        Session[Session Affinity<br/>Sticky Sessions<br/>Consistent Hashing<br/>State Management]
        
        Queue[Message Queuing<br/>Async Processing<br/>Background Jobs<br/>Event-driven Architecture]
    end
    
    subgraph "Data Layer Performance"
        ReadReplicas[Neo4j Read Replicas<br/>Read Query Distribution<br/>Load Distribution<br/>Failover Support]
        
        VectorCache[Vector Search Cache<br/>Embedding Storage<br/>Similarity Results<br/>Search Acceleration]
        
        RedisCluster[Redis Cluster<br/>Distributed Caching<br/>Session Storage<br/>Message Queuing]
    end
    
    subgraph "AI/LLM Optimization"
        ModelRouter[LLM Router<br/>Model Selection<br/>Cost Optimization<br/>Performance Routing]
        
        ResponseCache[Response Caching<br/>Role-based Storage<br/>Query Deduplication<br/>Smart Invalidation]
        
        Streaming[Response Streaming<br/>Chunked Delivery<br/>Real-time Updates<br/>Progressive Enhancement]
    end
    
    subgraph "Monitoring & Optimization"
        Metrics[Performance Metrics<br/>Response Time Tracking<br/>Throughput Analysis<br/>Error Rate Monitoring]
        
        Alerts[Smart Alerting<br/>Threshold Monitoring<br/>Anomaly Detection<br/>Automated Response]
        
        Optimization[Auto-optimization<br/>Query Plan Optimization<br/>Cache Warming<br/>Resource Allocation]
    end
    
    SSR --> Gateway --> HPA
    PPR --> RateLimit --> Session
    Cache --> Compression --> Queue
    
    HPA --> ReadReplicas --> ModelRouter
    Session --> VectorCache --> ResponseCache
    Queue --> RedisCluster --> Streaming
    
    ModelRouter --> Metrics
    ResponseCache --> Alerts
    Streaming --> Optimization
    
    style HPA fill:#065f46,stroke:#10b981,stroke-width:2px
    style ModelRouter fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style RedisCluster fill:#581c87,stroke:#a855f7,stroke-width:2px
    style Metrics fill:#1e40af,stroke:#3b82f6,stroke-width:2px
```

## 9. Deployment & DevOps Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Dev[Local Development<br/>Remote Databases<br/>Hot Reloading<br/>Debug Tools]
        
        Test[Testing Environment<br/>Automated Testing<br/>Integration Tests<br/>E2E Validation]
    end
    
    subgraph "CI/CD Pipeline"
        Source[Source Control<br/>Git Repository<br/>Feature Branches<br/>Code Review]
        
        Build[Build Pipeline<br/>Frontend Build<br/>Backend Package<br/>Render Service Deploy]
        
        Quality[Quality Gates<br/>Unit Tests<br/>Integration Tests<br/>Security Scans<br/>Performance Tests]
        
        Deploy[Deployment Pipeline<br/>Staging Deployment<br/>Production Release<br/>Rollback Capability]
    end
    
    subgraph "Staging Environment"
        Staging[Render Staging<br/>Preview Deployments<br/>User Acceptance Testing<br/>Performance Validation]
        
        Preview[Preview Deployments<br/>Feature Previews<br/>A/B Testing<br/>Stakeholder Review]
    end
    
    subgraph "Production Environment"
        Prod[Render Production<br/>Managed Services<br/>Auto-scaling<br/>Load Balancing]
        
        Monitor[Production Monitoring<br/>Health Checks<br/>Performance Metrics<br/>Error Tracking]
        
        Backup[Backup & Recovery<br/>Automated Backups<br/>Point-in-time Recovery<br/>Disaster Recovery]
    end
    
    subgraph "Infrastructure Management"
        IaC[Infrastructure as Code<br/>render.yaml Blueprint<br/>Render Service Config<br/>Environment Parity]
        
        Secrets[Secret Management<br/>Encrypted Storage<br/>Rotation Policies<br/>Access Control]
        
        Compliance[Compliance Monitoring<br/>Security Audits<br/>Data Governance<br/>Regulatory Adherence]
    end
    
    Dev --> Source --> Build --> Quality --> Deploy
    Deploy --> Staging --> Preview --> Prod
    Prod --> Monitor --> Backup
    
    IaC -.-> Dev
    IaC -.-> Staging  
    IaC -.-> Prod
    
    Secrets -.-> Build
    Secrets -.-> Staging
    Secrets -.-> Prod
    
    Compliance -.-> Quality
    Compliance -.-> Monitor
    
    style Source fill:#065f46,stroke:#10b981,stroke-width:2px
    style Quality fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style Prod fill:#581c87,stroke:#a855f7,stroke-width:2px
    style Monitor fill:#1e40af,stroke:#3b82f6,stroke-width:2px
```

## 10. Memory Management Architecture

```mermaid
graph TB
    subgraph "LangMem Memory Types"
        UserMem[User Profile Memory<br/>👤 Preferences & Context<br/>📊 Interaction Patterns<br/>🎯 Communication Style]
        
        EpisodeMem[Episodic Memory<br/>✅ Successful Interactions<br/>📈 Learning Patterns<br/>🔄 Strategy Optimization]
        
        SemanticMem[Semantic Memory<br/>🎭 Domain Knowledge<br/>⚖️ Union Rules<br/>💰 Budget Practices]
        
        ProjectMem[Project Context Memory<br/>🎬 Project-specific Insights<br/>👥 Team Preferences<br/>📋 Lessons Learned]
    end
    
    subgraph "Memory Operations"
        Extract[Memory Extraction<br/>Background Processing<br/>Pattern Recognition<br/>Knowledge Distillation]
        
        Store[Memory Storage<br/>Vector Indexing<br/>Namespace Management<br/>Conflict Resolution]
        
        Retrieve[Memory Retrieval<br/>Similarity Search<br/>Context Ranking<br/>Relevance Scoring]
        
        Update[Memory Updates<br/>Incremental Learning<br/>Fact Correction<br/>Preference Evolution]
    end
    
    subgraph "Memory Persistence"
        Redis[Redis Memory Store<br/>Session Persistence<br/>Fast Access<br/>Distributed Caching]
        
        Vector[Vector Database<br/>Embedding Storage<br/>Similarity Search<br/>Semantic Indexing]
        
        Archive[Long-term Archive<br/>Historical Data<br/>Compliance Storage<br/>Analytical Access]
    end
    
    subgraph "Memory Integration"
        QueryEnhance[Query Enhancement<br/>Context Integration<br/>Personalization<br/>Historical Awareness]
        
        ResponsePersonalize[Response Personalization<br/>Style Adaptation<br/>Preference Application<br/>Context Awareness]
        
        Learning[Continuous Learning<br/>Pattern Discovery<br/>Success Optimization<br/>Failure Analysis]
    end
    
    UserMem --> Extract --> Store --> Redis
    EpisodeMem --> Extract --> Store --> Vector
    SemanticMem --> Extract --> Store --> Archive
    ProjectMem --> Extract --> Store --> Redis
    
    Redis --> Retrieve --> QueryEnhance
    Vector --> Retrieve --> ResponsePersonalize
    Archive --> Retrieve --> Learning
    
    Extract --> Update --> Store
    
    style UserMem fill:#065f46,stroke:#10b981,stroke-width:2px
    style Extract fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style Redis fill:#581c87,stroke:#a855f7,stroke-width:2px
    style QueryEnhance fill:#1e40af,stroke:#3b82f6,stroke-width:2px
```

## 11. External Integration Architecture

```mermaid
graph TB
    subgraph "OneVice Core System"
        Agents[AI Agents<br/>Sales Intelligence<br/>Talent Discovery<br/>Bidding Support]
        
        Cache[Integration Cache<br/>API Response Caching<br/>Rate Limit Management<br/>Fallback Data]
        
        Scheduler[API Scheduler<br/>Request Queuing<br/>Retry Logic<br/>Circuit Breaker]
    end
    
    subgraph "Union & Labor APIs"
        IATSE[IATSE API<br/>Union Rules<br/>Current Rates<br/>Jurisdiction Data]
        
        DGA[DGA API<br/>Director Guidelines<br/>Contract Terms<br/>Minimum Rates]
        
        SAGAFTRA[SAG-AFTRA API<br/>Actor Rates<br/>Residual Rules<br/>Working Conditions]
        
        Local399[Local 399 API<br/>Teamster Rules<br/>Transportation<br/>Equipment Ops]
    end
    
    subgraph "Industry Data Sources"
        IMDb[IMDb Pro API<br/>Cast & Crew Data<br/>Production Details<br/>Release Information]
        
        Numbers[The Numbers API<br/>Box Office Data<br/>Budget Information<br/>Financial Performance]
        
        Variety[Variety Intelligence<br/>Industry News<br/>Market Analysis<br/>Trend Data]
        
        BoxOffice[Box Office Mojo<br/>Revenue Tracking<br/>Performance Metrics<br/>Comparative Analysis]
    end
    
    subgraph "Talent & Casting APIs"
        CastingNetworks[Casting Networks<br/>Talent Profiles<br/>Availability Status<br/>Portfolio Access]
        
        AgencyRosters[Agency Rosters<br/>Representation Data<br/>Contact Information<br/>Client Lists]
        
        UnionDirectories[Union Directories<br/>Member Status<br/>Good Standing<br/>Specialty Skills]
    end
    
    subgraph "Enterprise Integration"
        Okta[Okta SSO<br/>Identity Provider<br/>User Directory<br/>Role Management]
        
        LDAP[LDAP Directory<br/>Employee Data<br/>Organizational Structure<br/>Permission Mapping]
        
        Calendar[Calendar Integration<br/>Availability Checking<br/>Scheduling Coordination<br/>Conflict Resolution]
    end
    
    subgraph "Integration Management"
        APIGateway[API Gateway<br/>Request Routing<br/>Authentication<br/>Rate Limiting<br/>Monitoring]
        
        ErrorHandling[Error Handling<br/>Graceful Degradation<br/>Fallback Mechanisms<br/>Retry Strategies]
        
        Monitoring[Integration Monitoring<br/>API Health Checks<br/>Performance Tracking<br/>Alert Management]
    end
    
    Agents --> Scheduler --> Cache
    
    Scheduler --> IATSE
    Scheduler --> DGA
    Scheduler --> SAGAFTRA
    Scheduler --> Local399
    
    Scheduler --> IMDb
    Scheduler --> Numbers
    Scheduler --> Variety
    Scheduler --> BoxOffice
    
    Scheduler --> CastingNetworks
    Scheduler --> AgencyRosters
    Scheduler --> UnionDirectories
    
    Scheduler --> Okta
    Scheduler --> LDAP
    Scheduler --> Calendar
    
    Cache --> APIGateway --> ErrorHandling --> Monitoring
    
    style Agents fill:#065f46,stroke:#10b981,stroke-width:2px
    style Scheduler fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style APIGateway fill:#581c87,stroke:#a855f7,stroke-width:2px
    style Monitoring fill:#1e40af,stroke:#3b82f6,stroke-width:2px
```

## 12. Technology Stack Integration

```mermaid
graph TB
    subgraph "Frontend Technology Stack"
        NextJS[Next.js 15.4<br/>App Router + Turbopack<br/>Server Components<br/>Streaming SSR]
        
        React[React 19<br/>Concurrent Features<br/>Suspense + Transitions<br/>Server Components]
        
        TypeScript[TypeScript 5.6<br/>Strict Type Checking<br/>Advanced Inference<br/>Performance Optimizations]
        
        Tailwind[Tailwind CSS 3.4<br/>Utility-first Styling<br/>Custom Design Tokens<br/>Glassmorphic Components]
        
        Zustand[Zustand State Management<br/>Lightweight Store<br/>Persistence Layer<br/>Selector Optimization]
    end
    
    subgraph "Backend Technology Stack"
        FastAPI[FastAPI 0.115.x<br/>Async/Await Support<br/>WebSocket Management<br/>OpenAPI Documentation]
        
        Python[Python 3.12+<br/>Performance Improvements<br/>Type Hints<br/>Async Libraries]
        
        LangGraph[LangGraph 0.6.6+<br/>Multi-Agent Orchestration<br/>Supervisor Patterns<br/>State Management]
        
        LangMem[LangMem SDK<br/>Memory Management<br/>Learning Capabilities<br/>Context Persistence]
    end
    
    subgraph "Database Technology Stack"
        Neo4j[Neo4j 5.25.x Enterprise<br/>Graph Database<br/>Vector Search<br/>APOC + GDS Plugins]
        
        Redis[Redis 7.4.x<br/>Caching Layer<br/>Session Storage<br/>Message Queuing]
        
        Embeddings[OpenAI Embeddings<br/>text-embedding-3-small<br/>1536 Dimensions<br/>Semantic Search]
    end
    
    subgraph "AI & LLM Stack"
        LocalLlama[Local Llama<br/>Sensitive Data Processing<br/>On-premise Inference<br/>Privacy Compliance]
        
        Claude[Anthropic Claude<br/>Complex Reasoning<br/>Strategic Analysis<br/>Natural Language Processing]
        
        Gemini[Google Gemini<br/>Multimodal Processing<br/>Long Context Window<br/>Document Understanding]
    end
    
    subgraph "Authentication & Security"
        Clerk[Clerk Authentication<br/>JWT Management<br/>User Profiles<br/>Webhook Integration]
        
        OktaSSO[Okta SSO<br/>Enterprise Integration<br/>SAML/OIDC<br/>Directory Sync]
        
        RBAC[Custom RBAC<br/>6-Level Data Sensitivity<br/>Role-based Filtering<br/>Dynamic Permissions]
    end
    
    subgraph "DevOps & Infrastructure"
        Render[Render Platform<br/>Managed Services<br/>Auto-scaling<br/>Zero-downtime Deploy]
        
        Cloud[Cloud Services<br/>Remote Databases<br/>Managed Services<br/>High Availability]
        
        LangSmith[LangSmith<br/>AI Observability<br/>Performance Monitoring<br/>Cost Tracking]
    end
    
    NextJS --> React --> TypeScript --> Tailwind --> Zustand
    FastAPI --> Python --> LangGraph --> LangMem
    Neo4j --> Redis --> Embeddings
    LocalLlama --> Claude --> Gemini
    Clerk --> OktaSSO --> RBAC
    Render --> Cloud --> LangSmith
    
    React -.-> FastAPI
    LangGraph -.-> Neo4j
    LangMem -.-> Redis
    Claude -.-> Embeddings
    Clerk -.-> LangGraph
    LangSmith -.-> FastAPI
    
    style NextJS fill:#065f46,stroke:#10b981,stroke-width:2px
    style LangGraph fill:#7c2d12,stroke:#ea580c,stroke-width:2px
    style Neo4j fill:#581c87,stroke:#a855f7,stroke-width:2px
    style Clerk fill:#1e40af,stroke:#3b82f6,stroke-width:2px
```

---

**Document Status**: Architecture Diagrams Complete  
**Supporting Documentation**: system-architecture.md  
**Next Phase**: Technical implementation planning