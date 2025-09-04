#!/usr/bin/env python3
"""
Folk.app CRM Data Ingestion - Easy Run Script

A simple script to run the Folk ingestion tool with various options.
"""

import asyncio
import argparse
import sys
import os
import logging

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from tools.folk_ingestion.config import validate_environment, get_sample_env_file, get_config
from tools.folk_ingestion.folk_ingestion import FolkIngestionService


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("folk_ingestion.log", mode="a")
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def print_banner():
    """Print application banner"""
    
    print("""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                   Folk.app CRM Data Ingestion Tool                    ┃
┃                         OneVice Platform                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
""")


def print_help_info():
    """Print additional help information"""
    
    print("""
📋 USAGE EXAMPLES:

1. Run full ingestion:
   python3 run_folk_ingestion.py

2. Run in dry-run mode (preview only):
   python3 run_folk_ingestion.py --dry-run

3. Run with detailed logging:
   python3 run_folk_ingestion.py --log-level DEBUG

4. Test environment setup:
   python3 run_folk_ingestion.py --test

5. Check environment configuration:
   python3 run_folk_ingestion.py --check-env

📚 DOCUMENTATION:
   See tools/folk_ingestion/README.md for complete documentation

🔧 CONFIGURATION:
   Configure Folk API keys in backend/.env file:
   FOLK_API_KEYS=your_api_key_1,your_api_key_2
""")


def check_environment():
    """Check environment configuration"""
    
    print("🔍 Checking environment configuration...")
    
    validation = validate_environment()
    
    if validation["valid"]:
        print("✅ Environment validation PASSED")
        print(f"📊 Required variables present: {len(validation['present_required'])}/{validation['total_required']}")
        
        if validation['present_optional']:
            print(f"📋 Optional variables configured: {len(validation['present_optional'])}")
        
        return True
    else:
        print("❌ Environment validation FAILED")
        print(f"Missing required variables: {validation['missing_required']}")
        print("\n📝 Add these variables to your .env file:")
        print(get_sample_env_file())
        return False


async def run_test():
    """Run test suite"""
    
    print("🧪 Running Folk ingestion test suite...")
    
    try:
        from tools.folk_ingestion.test_folk_ingestion import main as test_main
        success = await test_main()
        
        if success:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
        
        return success
    
    except ImportError:
        print("❌ Test module not found. Make sure test_folk_ingestion.py is available.")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False


async def run_ingestion(dry_run: bool = False, log_level: str = "INFO"):
    """Run the Folk ingestion process"""
    
    print("🚀 Starting Folk CRM data ingestion...")
    
    try:
        # Setup logging
        setup_logging(log_level)
        
        # Load configuration
        config = get_config()
        
        # Override dry_run setting if specified
        if dry_run:
            config.dry_run = True
            print("📋 Running in DRY-RUN mode (no database changes)")
        
        print(f"📝 Configuration loaded:")
        print(f"   - API keys: {len(config.api_keys)}")
        print(f"   - Neo4j database: {config.neo4j_database}")
        print(f"   - Batch size: {config.batch_size}")
        print(f"   - Dry run: {config.dry_run}")
        
        # Run ingestion
        async with FolkIngestionService(config) as service:
            stats = await service.run_full_ingestion()
            
            # Print results
            print("\n" + "="*60)
            print("📊 INGESTION COMPLETED")
            print("="*60)
            print(f"⏱️  Duration: {stats.duration_seconds:.2f} seconds")
            print(f"🔑 API keys processed: {stats.api_keys_processed}")
            print(f"📡 API requests made: {stats.api_requests_made}")
            print(f"👥 People processed: {stats.people_processed}")
            print(f"🏢 Companies processed: {stats.companies_processed}")
            print(f"📋 Groups processed: {stats.groups_processed}")
            print(f"💼 Custom Objects processed: {stats.custom_objects_processed} ({stats.entity_types_discovered} types)")
            print(f"🔗 Relationships created: {stats.relationships_created}")
            print(f"📊 Transactions executed: {stats.transactions_executed}")
            
            # Error summary
            total_errors = len(stats.validation_errors) + len(stats.processing_errors)
            if total_errors > 0:
                print(f"\n⚠️  ERRORS ENCOUNTERED: {total_errors}")
                if stats.validation_errors:
                    print(f"   Validation errors: {len(stats.validation_errors)}")
                if stats.processing_errors:
                    print(f"   Processing errors: {len(stats.processing_errors)}")
                
                print("\n📝 Recent errors:")
                all_errors = stats.validation_errors + stats.processing_errors
                for error in all_errors[-3:]:  # Show last 3 errors
                    print(f"   • {error}")
            else:
                print("✅ No errors encountered!")
            
            # Success message
            if total_errors == 0:
                print("\n🎉 Ingestion completed successfully!")
            elif total_errors < 5:
                print("\n✅ Ingestion completed with minor errors.")
            else:
                print(f"\n⚠️  Ingestion completed with {total_errors} errors. Review logs for details.")
            
            return total_errors == 0
    
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        logging.error(f"Ingestion failed: {e}", exc_info=True)
        return False


async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Folk.app CRM Data Ingestion Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run full ingestion
  %(prog)s --dry-run          # Preview mode (no changes)
  %(prog)s --test             # Run test suite
  %(prog)s --check-env        # Check configuration
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (preview only, no database changes)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true", 
        help="Run test suite instead of ingestion"
    )
    
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check environment configuration only"
    )
    
    parser.add_argument(
        "--help-info",
        action="store_true",
        help="Show detailed help information"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Handle special commands
    if args.help_info:
        print_help_info()
        return True
    
    if args.check_env:
        return check_environment()
    
    if args.test:
        return await run_test()
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please configure your .env file.")
        return False
    
    # Run ingestion
    return await run_ingestion(
        dry_run=args.dry_run,
        log_level=args.log_level
    )


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Ingestion interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)