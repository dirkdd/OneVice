T### **AI-Powered Business Intelligence Hub: Final Software Development Request**

**Project Title:** OneVice AI-Powered Business Intelligence Hub
**Version:** 8.0: OneVice Implementation Ready
**Status:** Ready for Implementation - Phase 1

**1. Executive Summary & Project Vision**

This document outlines the requirements for the OneVice AI-Powered Business Intelligence Hub, a secure, centralized intelligence platform. The project's vision is to transform our vast archive of unstructured data into a strategic, queryable asset. By leveraging a sophisticated, private AI chat interface, we will empower our Sales, Creative, Production, and Management teams to uncover hidden relationships in our data, make faster, more informed decisions, and develop more competitive bidding strategies. The core business problem this initiative solves is the current fragmentation of institutional knowledge, leading to missed opportunities and inefficiencies. This platform will create a single, secure source of truth.

**2. Core Features & Phased Rollout**

The platform will be developed with a clear distinction between the Minimum Viable Product (MVP) for initial launch and a roadmap for future enhancements.

**2.1. MVP User Goals & Capabilities**
*   **Proactive Sales Intelligence:** Automate the research process for sales calls, enabling users to generate comprehensive pre-call briefs on contacts and companies.
*   **Targeted Case Study Compilation:** Enable the rapid assembly of pitch materials by finding past projects that meet specific client concerns or scope requirements.
*   **Advanced Talent & Resource Discovery:** Provide a powerful internal search engine for production needs, allowing users to find talent based on complex, multi-faceted queries (role, project history, budget tier, union status, etc.).
*   **Intelligent Bidding Support:** Create data-driven bid proposals by analyzing comparable past projects and integrating external, real-time union rule data.

**2.2. Key MVP Technical Deliverables**
*   **AI Agent Frontend:** A simple, web-based chat interface.
*   **LangGraph Orchestration:** The backend application managing the specialized AI agents, their tools, and the security filtering logic.
*   **Graph Ontology:** The defined schema for entities and their relationships (e.g., people, projects, brands, union status, budget ranges) and their relationships. This ontology will critically distinguish between the roles of **Director** (execution-focused, brings the concept to life, often on the London Alley roster) and **Creative Director** (concept/strategy-focused, conceives the idea, can be internal or external), allowing for precise tracking of creative responsibilities.
*   **ETL Pipeline for Archived Data:** The initial data ingestion process for the ~200 archived documents.
*   **Knowledge Graph:** The populated Neo4j graph database.

**2.3. Post-MVP Roadmap**
*   **Live Data Integration:** Implement ETL pipelines for **Folk (CRM)** and **Monday.com (PM)**.
*   **Enhanced Visualizations:** Introduce dashboard-style summaries and visual UI components.
*   **Advanced Admin Tools:** Develop an interactive graph visualization interface for power users.

**3. AI & Agent Architecture**

The system's intelligence will be driven by a multi-agent architecture designed for specialization and security.

*   **Private & Secure LLM Deployment:** All AI processing will be handled by a **private, locally-hosted Large Language Model (e.g., Llama via vLLM/Ollama)** to guarantee absolute data sovereignty.
*   **Authentication System:** Clerk authentication with Email and Okta SSO integration, replacing previous Supabase implementation.
*   **Specialized Agents with Security Fail-safe:** Distinct agents will be created for each core feature. A final "Filtering Node" will act as a supervisor, programmatically enforcing all defined access rules on every response before it reaches the user.
*   **Bidding Agent - Advanced Requirements:** The Bidding Agent must be equipped with specialized tools and knowledge to:
    1.  Differentiate between **UNION** and **Non-Union** projects in our historical data.
    2.  Integrate with external, real-time data sources to pull the most current union rules (e.g., from **IATSE, DGA, Local 399** websites) based on the specified state or country of a proposed shoot.
    3.  Factor union rules, including holiday pay and overtime, into all budget suggestions and feasibility analyses.

**4. Data Sources & Integration**

*   **MVP Data Source:** The initial proof-of-concept will be built using a corpus of ~200 archived documents.
*   **UI/UX Requirements:** Pixel-perfect implementation of 5 Figma pages (Home, Login, Leadership, Talent Discovery, Bidding) with glassmorphism design system, responsive design optimized for 1440px desktop, and accessibility compliance (WCAG 2.1 AA).
*   **Entity Normalization:** A critical component of the ETL pipeline is an entity resolution layer to merge duplicate entities.
*   **Future Data Ingestion Targets (Post-MVP):** The architecture will be designed to pull high-value fields from external systems, including CRM and Project Management platforms.

**5. Security & Permissions**

Security is a foundational principle, enforced by the private LLM architecture and granular, role-based access rules (RBAC).

*   **Data Terminology Clarification:** For the purpose of this document, **"Budget Information"** refers to the costs and breakdown of a specific project. **"Financial Information"** refers to internal company data such as Profit & Loss (P&L), which is considered highly sensitive.
*   **Defined Data Sensitivity Hierarchy (Most to Least Sensitive):**
    1.  Budgets
    2.  Contracts
    3.  Internal Strategy Notes
    4.  Call Sheets
    5.  Scripts
    6.  Sales Decks
*   **Defined Role-Based Access Control (RBAC) Rules:**
    *   **Leadership / Executive Producer Role:** Full, unrestricted access to all data levels, including detailed budget and financial information.
    *   **Salesperson Role:** Can view project summaries, personnel involved, and general **budget ranges** (e.g., "$100k-$300k tier"). They are explicitly restricted from viewing exact budget breakdowns or internal financial information.
    *   **Creative Director Role:** This role, whether internal (e.g., from London Alley Creative Studio) or external (e.g., from a client or agency), is focused on the creative concept rather than financial execution. Therefore, permissions are aligned with the **Salesperson role**. They can view **budget ranges** but are restricted from viewing exact, detailed budget breakdowns and internal financial information.
    *   **Director Role:** Permissions for Directors on the London Alley roster will align with the **Leadership / Executive Producer Role** for the specific projects they are attached to, granting them access to the necessary detailed budget information required for execution.

**6. Infrastructure & Operations**

*   **Deployment Strategy:** The MVP will be orchestrated and deployed using modern cloud infrastructure, with **Next.js 15.4 with Turbopack** for frontend and **FastAPI** backend.
*   **Technology Stack:** Latest 2025 versions including React 19 stable, LangGraph 0.6.6+ with supervisor patterns, LangMem SDK (February 2025 release), Node.js 20+ LTS, and Python 3.12+.
*   **Maintenance & Hand-off:** The project will be initially maintained by the current lead before being transitioned to a future internal team, supported by comprehensive documentation.
*   **Design Implementation:** Dark, modern, glassmorphic design system with specific gradient specifications, 1440px container width, 78px header height, and consistent 8px border radius for frames.