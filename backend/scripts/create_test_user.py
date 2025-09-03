#!/usr/bin/env python3
"""
OneVice Test User Creation Script

Creates a test user with LEADERSHIP role for authentication testing.
This bypasses Clerk integration for quick development testing.
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# Add parent directory to Python path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from passlib.context import CryptContext
from database.connection_manager import ConnectionManager
from auth.models import UserRole

# Load environment variables
load_dotenv()

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_test_user():
    """Create a test user in the database for authentication testing"""
    
    # Test user details
    user_id = str(uuid4())
    email = "admin@onevice.com"
    password = "TestPassword123!"
    name = "Test Admin"
    role = UserRole.LEADERSHIP
    
    print(f"Creating test user: {email}")
    print(f"Password: {password}")
    print(f"Role: {role.name}")
    print(f"User ID: {user_id}")
    
    try:
        # Initialize database connection
        connection_manager = ConnectionManager()
        await connection_manager.initialize()
        
        # Hash password
        password_hash = pwd_context.hash(password)
        print(f"Password hash created: {password_hash[:50]}...")
        
        # Get Neo4j client
        neo4j_client = connection_manager.neo4j_client
        
        # Create user in Neo4j
        query = """
        CREATE (u:User {
            id: $user_id,
            email: $email,
            name: $name,
            role: $role,
            password_hash: $password_hash,
            provider: 'INTERNAL',
            provider_id: $user_id,
            created_at: datetime(),
            last_login: null,
            active: true
        })
        RETURN u
        """
        
        result = await neo4j_client.execute_query(query, {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role.value,  # Store as integer
            'password_hash': password_hash,
        })
        
        if result.records:
            print("✅ User created successfully in Neo4j!")
            
            # Display user info
            user = result.records[0]['u']
            print(f"   ID: {user['id']}")
            print(f"   Email: {user['email']}")
            print(f"   Name: {user['name']}")
            print(f"   Role: {UserRole(user['role']).name}")
            print(f"   Provider: {user['provider']}")
        else:
            print("❌ Failed to create user")
                
        await connection_manager.close()
        
        print("\n🎉 Test user creation complete!")
        print(f"\nYou can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        import traceback
        traceback.print_exc()


async def check_user_exists():
    """Check if test user already exists"""
    
    try:
        connection_manager = ConnectionManager()
        await connection_manager.initialize()
        
        neo4j_client = connection_manager.neo4j_client
        
        query = """
        MATCH (u:User {email: $email})
        RETURN u
        """
        
        result = await neo4j_client.execute_query(query, {'email': 'admin@onevice.com'})
        
        if result.records:
            user = result.records[0]['u']
            print(f"✅ Test user already exists:")
            print(f"   Email: {user['email']}")
            print(f"   Name: {user['name']}")
            print(f"   Role: {UserRole(user['role']).name}")
            return True
        else:
            print("ℹ️  Test user does not exist")
            return False
                
    except Exception as e:
        print(f"❌ Error checking user: {e}")
        return False


if __name__ == "__main__":
    print("OneVice Test User Creation Script")
    print("=" * 40)
    
    # Check if user already exists
    if asyncio.run(check_user_exists()):
        response = input("\nTest user already exists. Create anyway? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Exiting...")
            sys.exit(0)
    
    # Create the test user
    asyncio.run(create_test_user())