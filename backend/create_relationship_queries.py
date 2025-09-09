#!/usr/bin/env python3
"""
Create Enhanced Relationship Queries for Treatment Writer Discovery

Based on the relationship investigation findings, this script creates and tests
enhanced Cypher queries that can properly connect treatment writers to their projects.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from database.neo4j_client import Neo4jClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_relationship_queries():
    """Test enhanced relationship queries for treatment writer discovery"""
    
    neo4j_client = Neo4jClient()
    await neo4j_client.connect()
    
    print("\n" + "="*70)
    print("TESTING ENHANCED RELATIONSHIP QUERIES FOR TREATMENT WRITERS")
    print("="*70 + "\n")
    
    try:
        # Query 1: Find writers who authored/wrote treatments for a specific company
        print("1. QUERY: Find treatment writers for Boost Mobile")
        print("-" * 50)
        
        boost_writers_query = """
        MATCH (writer:Person)-[r:AUTHORED_BY|WROTE_TREATMENT_FOR|DIRECTED]-(project)
        WHERE (toLower(project.id) CONTAINS 'boost' OR toLower(project.name) CONTAINS 'boost')
        AND (toLower(writer.role) CONTAINS 'writer' OR toLower(writer.role) CONTAINS 'director')
        RETURN writer.id AS writer_id, writer.name AS writer_name, writer.role AS writer_role,
               project.id AS project_id, project.name AS project_name, 
               type(r) AS relationship_type,
               project.description AS project_description
        ORDER BY writer.id, project.id
        """
        
        result = await neo4j_client.execute_query(boost_writers_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} writer-project relationships for Boost Mobile:")
            for record in result.records:
                writer_id = record.get('writer_id', 'unknown')
                writer_name = record.get('writer_name', 'unknown')
                writer_role = record.get('writer_role', 'unknown')
                project_id = record.get('project_id', 'unknown')
                project_name = record.get('project_name', 'unknown')
                relationship = record.get('relationship_type', 'unknown')
                project_desc = record.get('project_description', '')
                
                print(f"  👤 Writer: {writer_id} ({writer_role})")
                print(f"     Name: {writer_name}")
                print(f"     --[{relationship}]--> {project_id}")
                print(f"     Project Name: {project_name}")
                if project_desc:
                    print(f"     Description: {project_desc[:100]}...")
                print()
        else:
            print("❌ No writer-project relationships found for Boost Mobile")
        
        # Query 2: Generic treatment writer finder (can be parameterized)
        print("\n2. QUERY: Generic treatment writer finder for any company")
        print("-" * 50)
        
        generic_writer_query = """
        MATCH (writer:Person)-[r:AUTHORED_BY|WROTE_TREATMENT_FOR|DIRECTED|CREATED]-(project)
        WHERE $search_term IS NULL OR (
            toLower(project.id) CONTAINS toLower($search_term) OR 
            toLower(project.name) CONTAINS toLower($search_term) OR
            toLower(project.client) CONTAINS toLower($search_term)
        )
        AND (
            toLower(writer.role) CONTAINS 'writer' OR 
            toLower(writer.role) CONTAINS 'director' OR
            toLower(writer.role) CONTAINS 'author'
        )
        RETURN writer.id AS writer_id, writer.name AS writer_name, writer.role AS writer_role,
               writer.bio AS writer_bio,
               project.id AS project_id, project.name AS project_name, project.client AS project_client,
               type(r) AS relationship_type,
               project.description AS project_description,
               project.type AS project_type
        ORDER BY writer.id, project.id
        LIMIT 10
        """
        
        # Test with "boost" parameter
        result = await neo4j_client.execute_query(generic_writer_query, {"search_term": "boost"})
        if result and result.records:
            print(f"✅ Generic query found {len(result.records)} writer-project relationships:")
            for record in result.records:
                writer_id = record.get('writer_id', 'unknown')
                writer_role = record.get('writer_role', 'unknown')
                project_id = record.get('project_id', 'unknown')
                project_client = record.get('project_client', 'unknown')
                relationship = record.get('relationship_type', 'unknown')
                project_type = record.get('project_type', 'unknown')
                
                print(f"  👤 {writer_id} ({writer_role}) --[{relationship}]--> {project_id}")
                print(f"     Client: {project_client}, Type: {project_type}")
        else:
            print("❌ Generic query found no results")
        
        # Query 3: Comprehensive treatment discovery query
        print("\n3. QUERY: Comprehensive treatment discovery (includes documents)")
        print("-" * 50)
        
        comprehensive_query = """
        // Find writers connected to treatments through multiple paths
        MATCH (writer:Person)
        WHERE toLower(writer.role) CONTAINS 'writer' 
           OR toLower(writer.role) CONTAINS 'director'
           OR toLower(writer.role) CONTAINS 'author'
        
        OPTIONAL MATCH (writer)-[r1:AUTHORED_BY|WROTE_TREATMENT_FOR|DIRECTED|CREATED]-(project:Project)
        WHERE toLower(project.id) CONTAINS $company_name 
           OR toLower(project.name) CONTAINS $company_name
           OR toLower(project.client) CONTAINS $company_name
        
        OPTIONAL MATCH (writer)-[r2:AUTHORED_BY|WROTE_TREATMENT_FOR|CREATED]-(doc:Document)
        WHERE toLower(doc.id) CONTAINS $company_name 
           OR toLower(doc.title) CONTAINS $company_name
           OR toLower(doc.content) CONTAINS $company_name
        
        WITH writer, project, doc, r1, r2
        WHERE project IS NOT NULL OR doc IS NOT NULL
        
        RETURN writer.id AS writer_id, writer.name AS writer_name, writer.role AS writer_role,
               writer.bio AS writer_bio,
               project.id AS project_id, project.name AS project_name, project.client AS project_client,
               doc.id AS document_id, doc.title AS document_title,
               type(r1) AS project_relationship, type(r2) AS document_relationship
        ORDER BY writer.id
        """
        
        result = await neo4j_client.execute_query(comprehensive_query, {"company_name": "boost"})
        if result and result.records:
            print(f"✅ Comprehensive query found {len(result.records)} writer connections:")
            for record in result.records:
                writer_id = record.get('writer_id', 'unknown')
                writer_role = record.get('writer_role', 'unknown')
                project_id = record.get('project_id', 'N/A')
                document_id = record.get('document_id', 'N/A')
                proj_rel = record.get('project_relationship', 'N/A')
                doc_rel = record.get('document_relationship', 'N/A')
                
                print(f"  👤 {writer_id} ({writer_role})")
                if project_id != 'N/A':
                    print(f"     Project: --[{proj_rel}]--> {project_id}")
                if document_id != 'N/A':
                    print(f"     Document: --[{doc_rel}]--> {document_id}")
                print()
        else:
            print("❌ Comprehensive query found no results")
        
        # Query 4: Test the exact question format
        print("\n4. QUERY: Answer 'Who wrote the treatment for Boost Mobile?'")
        print("-" * 50)
        
        answer_query = """
        // Direct answer to "Who wrote the treatment for Boost Mobile?"
        MATCH (writer:Person)-[r:AUTHORED_BY|WROTE_TREATMENT_FOR|DIRECTED]-(item)
        WHERE (
            // Match various ways Boost Mobile might be referenced
            toLower(item.id) CONTAINS 'boost mobile' OR
            toLower(item.name) CONTAINS 'boost mobile' OR
            toLower(item.client) CONTAINS 'boost mobile' OR
            (toLower(item.id) CONTAINS 'boost' AND toLower(item.id) CONTAINS 'mobile')
        )
        AND (
            // Treatment-related content
            toLower(item.type) CONTAINS 'treatment' OR
            toLower(item.id) CONTAINS 'treatment' OR
            toLower(item.name) CONTAINS 'treatment' OR
            toLower(item.description) CONTAINS 'treatment'
        )
        AND (
            // Writer/creative roles
            toLower(writer.role) CONTAINS 'writer' OR
            toLower(writer.role) CONTAINS 'director' OR  
            toLower(writer.role) CONTAINS 'author'
        )
        
        RETURN writer.id AS writer, writer.name AS writer_name, writer.role AS role,
               item.id AS treatment, item.name AS treatment_name, item.type AS treatment_type,
               type(r) AS relationship,
               item.description AS description
        ORDER BY writer.id, item.id
        """
        
        result = await neo4j_client.execute_query(answer_query)
        if result and result.records:
            print(f"🎯 DIRECT ANSWER found {len(result.records)} treatment writers:")
            writers = set()
            for record in result.records:
                writer = record.get('writer', 'unknown')
                writer_name = record.get('writer_name', 'unknown')
                role = record.get('role', 'unknown')
                treatment = record.get('treatment', 'unknown')
                relationship = record.get('relationship', 'unknown')
                
                writers.add(f"{writer} ({role})")
                print(f"  ✅ {writer} ({role}) --[{relationship}]--> {treatment}")
                if writer_name and writer_name != 'unknown':
                    print(f"     Full Name: {writer_name}")
            
            print(f"\n🎉 ANSWER: The treatment for Boost Mobile was written by:")
            for writer in sorted(writers):
                print(f"  • {writer}")
        else:
            print("❌ No direct treatment writer found - may need to broaden search criteria")
            
            # Fallback broader search
            print("\n   Trying broader search...")
            fallback_query = """
            MATCH (writer:Person)-[r]-(item)
            WHERE toLower(item.id) CONTAINS 'boost'
            AND (toLower(writer.role) CONTAINS 'writer' OR toLower(writer.role) CONTAINS 'director')
            RETURN writer.id AS writer, writer.role AS role, item.id AS item, type(r) AS rel
            LIMIT 5
            """
            
            result = await neo4j_client.execute_query(fallback_query)
            if result and result.records:
                print(f"   Fallback found {len(result.records)} Boost-related connections:")
                for record in result.records:
                    writer = record.get('writer', 'unknown')
                    role = record.get('role', 'unknown')
                    item = record.get('item', 'unknown')
                    rel = record.get('rel', 'unknown')
                    print(f"     {writer} ({role}) --[{rel}]--> {item}")
        
    except Exception as e:
        print(f"❌ Error testing relationship queries: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection properly
        if hasattr(neo4j_client, 'driver') and neo4j_client.driver:
            await neo4j_client.driver.close()
    
    print("\n" + "="*70)
    print("RELATIONSHIP QUERY TESTING COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_relationship_queries())