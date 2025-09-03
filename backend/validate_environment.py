#!/usr/bin/env python3
"""
Enhanced Environment Validation for OneVice Memory System

Validates all required environment variables for the memory system deployment.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class EnvironmentValidator:
    """Validates environment configuration for memory system"""
    
    def __init__(self):
        self.validation_results = {}
        self.missing_vars = []
        self.warnings = []
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all environment validations"""
        print("🔍 OneVice Memory System Environment Validation")
        print("=" * 60)
        
        # Run all validation categories
        self.validate_database_config()
        self.validate_redis_config()
        self.validate_neo4j_config()
        self.validate_llm_providers()
        self.validate_memory_config()
        self.validate_optional_config()
        
        # Generate report
        return self.generate_report()
    
    def validate_database_config(self):
        """Validate PostgreSQL database configuration"""
        print("\n📊 Database Configuration")
        print("-" * 30)
        
        required_vars = {
            'DATABASE_URL': 'PostgreSQL connection string'
        }
        
        db_config = {}
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Mask password for security
                if 'postgresql://' in value and ':' in value and '@' in value:
                    masked_value = value.split('@')[0].split(':')[:-1]
                    masked_value = ':'.join(masked_value) + ':***@' + value.split('@')[1]
                else:
                    masked_value = value[:20] + "..." if len(value) > 20 else value
                    
                print(f"  ✅ {var}: {masked_value}")
                db_config[var] = {'status': 'present', 'masked_value': masked_value}
            else:
                print(f"  ❌ {var}: Missing - {description}")
                self.missing_vars.append(var)
                db_config[var] = {'status': 'missing', 'description': description}
        
        self.validation_results['database'] = db_config
    
    def validate_redis_config(self):
        """Validate Redis configuration"""
        print("\n🔴 Redis Configuration")
        print("-" * 30)
        
        required_vars = {
            'REDIS_URL': 'Redis connection string for sessions and checkpointing'
        }
        
        redis_config = {}
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Mask password if present
                if '@' in value and ':' in value:
                    parts = value.split('@')
                    if len(parts) > 1:
                        masked_value = parts[0].split(':')[:-1]
                        masked_value = ':'.join(masked_value) + ':***@' + parts[1]
                    else:
                        masked_value = value
                else:
                    masked_value = value
                    
                print(f"  ✅ {var}: {masked_value}")
                redis_config[var] = {'status': 'present', 'masked_value': masked_value}
            else:
                print(f"  ❌ {var}: Missing - {description}")
                self.missing_vars.append(var)
                redis_config[var] = {'status': 'missing', 'description': description}
        
        self.validation_results['redis'] = redis_config
    
    def validate_neo4j_config(self):
        """Validate Neo4j configuration"""
        print("\n🟢 Neo4j Configuration (Graph Database)")
        print("-" * 40)
        
        required_vars = {
            'NEO4J_URI': 'Neo4j connection URI (neo4j+s://...)',
            'NEO4J_USERNAME': 'Neo4j username (usually neo4j)',
            'NEO4J_PASSWORD': 'Neo4j password'
        }
        
        optional_vars = {
            'NEO4J_DATABASE': 'Neo4j database name (defaults to neo4j)'
        }
        
        neo4j_config = {}
        
        # Required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                if 'PASSWORD' in var:
                    masked_value = '***' + value[-4:] if len(value) > 4 else '***'
                elif 'URI' in var:
                    # Show URI but mask credentials if present
                    if '@' in value:
                        parts = value.split('@')
                        auth_part = parts[0].split('//')[-1]
                        if ':' in auth_part:
                            masked_auth = auth_part.split(':')[0] + ':***'
                            masked_value = value.replace(auth_part, masked_auth)
                        else:
                            masked_value = value
                    else:
                        masked_value = value
                else:
                    masked_value = value
                    
                print(f"  ✅ {var}: {masked_value}")
                neo4j_config[var] = {'status': 'present', 'masked_value': masked_value}
                
                # Validate URI format
                if var == 'NEO4J_URI' and not (value.startswith('neo4j://') or 
                                              value.startswith('neo4j+s://') or 
                                              value.startswith('bolt://') or 
                                              value.startswith('bolt+s://')):
                    self.warnings.append(f"NEO4J_URI should start with neo4j://, neo4j+s://, bolt://, or bolt+s://")
            else:
                print(f"  ❌ {var}: Missing - {description}")
                self.missing_vars.append(var)
                neo4j_config[var] = {'status': 'missing', 'description': description}
        
        # Optional variables
        for var, description in optional_vars.items():
            value = os.getenv(var, 'neo4j')  # Default value
            print(f"  ✅ {var}: {value}")
            neo4j_config[var] = {'status': 'present', 'value': value, 'is_default': var not in os.environ}
        
        self.validation_results['neo4j'] = neo4j_config
    
    def validate_llm_providers(self):
        """Validate LLM provider configurations"""
        print("\n🧠 LLM Provider Configuration")
        print("-" * 35)
        
        providers = {
            'TOGETHER_API_KEY': {
                'name': 'Together.ai',
                'description': 'Primary LLM provider',
                'required': True
            },
            'OPENAI_API_KEY': {
                'name': 'OpenAI',
                'description': 'Fallback LLM provider',
                'required': False
            },
            'ANTHROPIC_API_KEY': {
                'name': 'Anthropic',
                'description': 'Optional LLM provider',
                'required': False
            }
        }
        
        llm_config = {}
        at_least_one_provider = False
        
        for var, info in providers.items():
            value = os.getenv(var)
            if value:
                masked_value = value[:8] + '***' if len(value) > 8 else '***'
                print(f"  ✅ {info['name']}: {masked_value}")
                llm_config[var] = {
                    'status': 'present',
                    'name': info['name'],
                    'masked_value': masked_value,
                    'required': info['required']
                }
                at_least_one_provider = True
            else:
                status_icon = "❌" if info['required'] else "⚠️"
                print(f"  {status_icon} {info['name']}: Missing - {info['description']}")
                llm_config[var] = {
                    'status': 'missing',
                    'name': info['name'],
                    'description': info['description'],
                    'required': info['required']
                }
                if info['required']:
                    self.missing_vars.append(var)
        
        if not at_least_one_provider:
            self.warnings.append("No LLM providers configured - system will not function")
        
        self.validation_results['llm_providers'] = llm_config
    
    def validate_memory_config(self):
        """Validate memory system specific configuration"""
        print("\n🧠 Memory System Configuration")
        print("-" * 35)
        
        optional_vars = {
            'LANGSMITH_API_KEY': 'LangSmith tracing and monitoring (optional)',
            'LANGSMITH_PROJECT': 'LangSmith project name (optional)'
        }
        
        memory_config = {}
        
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                if 'API_KEY' in var:
                    masked_value = value[:8] + '***' if len(value) > 8 else '***'
                else:
                    masked_value = value
                print(f"  ✅ {var}: {masked_value}")
                memory_config[var] = {'status': 'present', 'masked_value': masked_value}
            else:
                print(f"  ⚠️ {var}: Not set - {description}")
                memory_config[var] = {'status': 'missing', 'description': description}
        
        self.validation_results['memory_system'] = memory_config
    
    def validate_optional_config(self):
        """Validate optional configuration variables"""
        print("\n⚙️ Optional Configuration")
        print("-" * 30)
        
        optional_vars = {
            'DEBUG': ('Debug mode', 'false'),
            'LOG_LEVEL': ('Logging level', 'INFO'),
            'HOST': ('Server host', '0.0.0.0'),
            'PORT': ('Server port', '8000'),
            'ENVIRONMENT': ('Environment name', 'development'),
        }
        
        optional_config = {}
        
        for var, (description, default) in optional_vars.items():
            value = os.getenv(var, default)
            is_default = var not in os.environ
            
            print(f"  ✅ {var}: {value}" + (" (default)" if is_default else ""))
            optional_config[var] = {
                'status': 'present',
                'value': value,
                'is_default': is_default,
                'description': description
            }
        
        self.validation_results['optional'] = optional_config
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        print("\n" + "=" * 60)
        print("📊 ENVIRONMENT VALIDATION REPORT")
        print("=" * 60)
        
        # Summary
        total_critical = sum(1 for var in ['DATABASE_URL', 'REDIS_URL', 'NEO4J_URI', 
                                         'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'TOGETHER_API_KEY'] 
                           if var in self.missing_vars)
        
        total_warnings = len(self.warnings)
        
        print(f"\n✅ Critical Variables: {6 - total_critical}/6 configured")
        print(f"⚠️ Warnings: {total_warnings}")
        print(f"❌ Missing Critical: {total_critical}")
        
        # Status assessment
        if total_critical == 0:
            if total_warnings == 0:
                status = "🟢 READY FOR PRODUCTION"
                recommendation = "All critical variables configured. System ready for deployment."
            else:
                status = "🟡 READY WITH WARNINGS"
                recommendation = "System can run but consider addressing warnings for optimal performance."
        else:
            status = "🔴 NOT READY"
            recommendation = "Critical variables missing. System will not start properly."
        
        print(f"\n{status}")
        print(f"Recommendation: {recommendation}")
        
        # Missing variables
        if self.missing_vars:
            print(f"\n❌ Missing Critical Variables:")
            for var in self.missing_vars:
                print(f"  - {var}")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        if total_critical == 0:
            print("  1. ✅ Run connection tests: python test_connections_enhanced.py")
            print("  2. ✅ Setup virtual environment: python -m venv venv_clean")
            print("  3. ✅ Install dependencies: pip install -r requirements.txt")
            print("  4. ✅ Run integration tests")
        else:
            print("  1. ❌ Configure missing critical variables in .env file")
            print("  2. ❌ Re-run validation: python validate_environment.py")
            print("  3. ⏸️ Wait for validation to pass before proceeding")
        
        # Return structured report
        return {
            'status': status,
            'critical_missing': total_critical,
            'warnings': total_warnings,
            'missing_vars': self.missing_vars,
            'warnings_list': self.warnings,
            'validation_results': self.validation_results,
            'ready_for_production': total_critical == 0,
            'recommendation': recommendation
        }

def main():
    """Main validation entry point"""
    validator = EnvironmentValidator()
    report = validator.validate_all()
    
    # Save report to file
    with open('environment_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: environment_validation_report.json")
    
    # Exit with appropriate code
    sys.exit(0 if report['ready_for_production'] else 1)

if __name__ == "__main__":
    main()