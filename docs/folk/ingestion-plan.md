### **High-Level Strategy: Bridging Business Development and Production**

First, let's establish the goal. Our Neo4j graph currently models the **Production World**: projects, creative concepts, crew, and how work gets *done*. Folk.app models the **Business Development World**: contacts, relationships, sales funnels, and how work gets *won*.

Integrating them creates a seamless, 360-degree view of your entire business, allowing you to answer complex questions that are impossible to answer today, such as:

*   "Which of our past crew members has a strong relationship with the Creative Director at Nike?"
*   "Show me all the pitch decks we've sent to companies in the 'CPG Brands' group in Folk."
*   "What is the current deal status for the 'Sweet Loren's' project, and who was the director on the last project we did with a similar brand?"

### **Analysis of Folk.app Data & Mapping to Your Graph**

Let's map Folk's core objects to our graph ontology. This is the key to understanding how they fit.

*   **Folk `people` -> Neo4j `Person`:** This is a direct match. A person in Folk is the same as a `Person` in your graph. We'll need to merge them based on a unique identifier like email or name.
*   **Folk `companies` -> Neo4j `Organization`:** Another direct match.
*   **Folk `groups` -> New Neo4j `Group` Node:** A "group" in Folk (e.g., "Past Clients," "Music Video Commissioners") is a powerful piece of segmentation data. While you could add it as a simple property, it's far more powerful to model it as its own node. This allows you to query the group itself.
*   **Folk `deals` -> New Neo4j `Deal` Node:** This is a massive value-add. A "deal" represents a potential project in the sales pipeline. It has a status (lead, contacted, won, lost), a value, and is connected to people and companies. This is the missing link between a "lead" and an "awarded project."

### **The Core Decision: Ingestion vs. Live Linking**

You have three primary architectural options for making Folk data available to your agents.

#### **The Hybrid Model (Recommended Best Practice)**

This model provides the best of both worlds and is the standard for robust enterprise AI systems. You ingest the core data but enrich it with live calls when necessary.

*   **How it Works:**
    1.  **Nightly Ingestion:** Run a daily script to ingest and synchronize the core entities: People, Companies, Groups, and Deals. This builds the foundational structure in your graph.
    2.  **Store Foreign Keys:** When you create a `Person` node in Neo4j from a Folk contact, store the Folk ID on that node (e.g., `folkId: "folk_person_123"`).
    3.  **Create Smart Agent Tools:**
        *   A `graph_search_tool` that queries Neo4j for rich, contextual information.
        *   A `folk_api_tool` that performs highly specific, targeted lookups (e.g., `get_latest_deal_status(folk_deal_id)`).
*   **Example Agent Workflow:**
    1.  **User:** "Give me a summary of our relationship with Jane Doe at Acme Inc. and the status of any active deals."
    2.  **Agent:** Uses `graph_search_tool` to query Neo4j: `MATCH (p:Person {name:"Jane Doe"})-[:WORKS_FOR]->(o:Organization {name:"Acme Inc."}) RETURN p, o`.
    3.  **Agent:** From the returned `Person` node, it gets `p.folkId`. It also sees a `Deal` node from last night's import with a status of "Contacted."
    4.  **Agent:** To ensure the status is current, it calls `folk_api_tool.get_deal_status(folk_deal_id=...)`. The API returns a new status: "Meeting Scheduled."
    5.  **Agent:** Synthesizes the information from both sources and provides a complete, up-to-date answer.

---

### **Actionable Plan & Recommendations**

**My strong recommendation is to implement the Hybrid Model.** It gives your agents the speed and deep context of the graph, with the real-time accuracy of live API calls for volatile data.

Here are the steps to get started:

**Step 1: Extend Your Graph Schema**

First, ensure your schema is up-to-date. The consolidated schema should be in `docs/schemas/london_alley_graph_schema.cypher`. This file now includes nodes for `Deal` and `Group` from Folk.

To properly track data provenance, we also need to model who on your team is sourcing the data. Add the following relationship exemplars to your schema file. This allows you to link Folk data back to the internal user who owns it.

```cypher
// ================================================================================
// 1. NODE SCHEMA DEFINITIONS (Additions for Folk.app Integration)
// ================================================================================

// A Deal represents a business opportunity in the sales pipeline.
CREATE CONSTRAINT deal_id_unique IF NOT EXISTS FOR (d:Deal) REQUIRE d.dealId IS UNIQUE;

// A Group represents a custom segment of people or companies from Folk.
CREATE CONSTRAINT group_name_unique IF NOT EXISTS FOR (g:Group) REQUIRE g.name IS UNIQUE;

// ================================================================================
// 3. RELATIONSHIP SCHEMA (EXEMPLARS - Additions for Integration)
// ================================================================================

// -- CRM & Business Development Relationships --
// MATCH (p:Person), (g:Group) MERGE (p)-[:BELONGS_TO]->(g);
// MATCH (d:Deal), (p:Person) MERGE (d)-[:WITH_CONTACT]->(p);
// MATCH (d:Deal), (o:Organization) MERGE (d)-[:FOR_ORGANIZATION]->(o);
// MATCH (d:Deal), (p:Project) MERGE (d)-[:EVOLVED_INTO]->(p); // For won deals

// -- Internal Data Ownership Relationships --
// MATCH (p:Person), (d:Deal) MERGE (p)-[:SOURCED]->(d);
// MATCH (p:Person), (g:Group) MERGE (p)-[:OWNS_CONTACT]->(g);
```

**Step 2: Develop the Ingestion Script**

Develop a Python script to perform the ingestion. The script should be designed to run based on a list of Folk API keys. For each key, it will perform the following steps:

1.  **Identify the Data Owner:** Before fetching data, use the API key to make a request to the `https://api.folk.app/v1/users/me` endpoint. This returns the user profile associated with the key. Find or create the corresponding `:Person` node in your graph for this internal team member. 
    *   Set the `folkUserId` property on this node using the `id` from the API response.
    *   Set the `isInternal` property to `true`.
    *   This user is the "owner" of the data that will be ingested in the following steps.

2.  **Ingest People, Companies, and Groups:** Fetch the core entities from Folk. As you create or merge `:Person`, `:Organization`, and `:Group` nodes in Neo4j, create an `:OWNS_CONTACT` relationship from the internal user (from step 1) to the contacts they own.

3.  **Ingest Deals:** To extract deals, you must iterate through the relevant Group IDs. For each group, make a request to the `https://api.folk.app/v1/groups/{group_id}/deals` endpoint.
    *   As you create `:Deal` nodes, create a `:SOURCED` relationship from the internal user (from step 1) to the new `:Deal` node.
    *   Link the deal to the relevant contacts and organizations using the `:WITH_CONTACT` and `:FOR_ORGANIZATION` relationships.

*For comprehensive API details, refer to the official documentation: [https://developer.folk.app/api-reference/overview](https://developer.folk.app/api-reference/overview)*

**Step 3: Design Your LangGraph Agent Tools**

Define the specific tools your agents will have access to:

*   `find_person_in_graph(name: str, company: str = None)`: Returns a rich profile from Neo4j, including past projects and CRM data.
*   `get_live_deal_status(folk_deal_id: str)`: Takes a Folk ID (stored in the graph) and returns only the current status and last activity.
*   `find_projects_by_concept(concept: str)`: A powerful tool to find past work based on creative DNA.
*   `who_sourced_deal(deal_name: str)`: A new tool that uses the `:SOURCED` relationship to identify the internal team member who brought in a specific deal.

By following this hybrid approach, you will build a system that is not only powerful and insightful but also scalable and maintainable.