#!/usr/bin/env python3
"""
Test script to verify the tool execution fix
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, '/mnt/c/Users/dirkd/OneDrive/Desktop/OneVice/backend')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

async def test_tool_fix():
    """Test the tool execution fix"""
    try:
        # Import required modules
        from app.ai.tools.factory import tool_factory
        from app.ai.tools.tool_definitions import get_organization_profile
        from app.ai.tools.dependencies import init_tool_dependencies
        
        logger.info("🔄 Starting tool execution test...")
        
        # Initialize dependencies first
        await init_tool_dependencies()
        logger.info("✅ Dependencies initialized")
        
        # Test the actual tool that's already created in tool_definitions.py
        logger.info("🧪 Testing tool via ainvoke method...")
        result = await get_organization_profile.ainvoke({"org_name": "Boost Mobile"})
        logger.info(f"📊 Tool result: {type(result)} - {len(str(result))} chars")
        
        logger.info("🎉 Test completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_fix())