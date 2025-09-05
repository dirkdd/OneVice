"""
Folk Ingestion Configuration

Configuration management for Folk.app data ingestion tool.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class FolkConfig:
    """Configuration for Folk ingestion process"""
    
    # Folk API Configuration
    api_keys: List[str] = field(default_factory=list)
    base_url: str = "https://api.folk.app/v1"
    rate_limit: int = 100
    timeout: int = 30
    max_retries: int = 3
    page_size: int = 100
    
    # Neo4j Configuration  
    neo4j_uri: str = ""
    neo4j_username: str = ""
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    
    # Ingestion Configuration
    dry_run: bool = False
    batch_size: int = 50
    max_concurrent_requests: int = 5
    enable_detailed_logging: bool = False
    backup_before_ingestion: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    @classmethod
    def from_environment(cls) -> "FolkConfig":
        """Create configuration from environment variables"""
        
        # Parse API keys from comma-separated string
        api_keys_str = os.getenv("FOLK_API_KEYS", "")
        api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
        
        if not api_keys:
            raise ValueError("FOLK_API_KEYS environment variable is required")
        
        # Neo4j configuration
        neo4j_uri = os.getenv("NEO4J_URI", "")
        if not neo4j_uri:
            raise ValueError("NEO4J_URI environment variable is required")
        
        neo4j_username = os.getenv("NEO4J_USERNAME", "")
        if not neo4j_username:
            raise ValueError("NEO4J_USERNAME environment variable is required")
        
        neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        if not neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")
        
        return cls(
            # Folk API
            api_keys=api_keys,
            base_url=os.getenv("FOLK_API_BASE_URL", "https://api.folk.app/v1"),
            rate_limit=int(os.getenv("FOLK_API_RATE_LIMIT", "100")),
            timeout=int(os.getenv("FOLK_API_TIMEOUT", "30")),
            max_retries=int(os.getenv("FOLK_API_MAX_RETRIES", "3")),
            page_size=int(os.getenv("FOLK_API_PAGE_SIZE", "100")),
            
            # Neo4j
            neo4j_uri=neo4j_uri,
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
            
            # Ingestion
            dry_run=os.getenv("FOLK_INGESTION_DRY_RUN", "false").lower() == "true",
            batch_size=int(os.getenv("FOLK_INGESTION_BATCH_SIZE", "50")),
            max_concurrent_requests=int(os.getenv("FOLK_INGESTION_MAX_CONCURRENT", "5")),
            enable_detailed_logging=os.getenv("FOLK_INGESTION_DETAILED_LOGGING", "false").lower() == "true",
            backup_before_ingestion=os.getenv("FOLK_INGESTION_BACKUP", "true").lower() == "true",
            
            # Logging
            log_level=os.getenv("FOLK_LOG_LEVEL", "INFO"),
            log_file=os.getenv("FOLK_LOG_FILE")
        )
    
    def validate(self) -> None:
        """Validate configuration settings"""
        
        if not self.api_keys:
            raise ValueError("At least one Folk API key is required")
        
        if not self.neo4j_uri:
            raise ValueError("Neo4j URI is required")
        
        if not self.neo4j_username:
            raise ValueError("Neo4j username is required")
        
        if not self.neo4j_password:
            raise ValueError("Neo4j password is required")
        
        if self.batch_size <= 0:
            raise ValueError("Batch size must be greater than 0")
        
        if self.max_concurrent_requests <= 0:
            raise ValueError("Max concurrent requests must be greater than 0")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
    
    def setup_logging(self) -> None:
        """Configure logging based on settings"""
        
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format=self.log_format,
            filename=self.log_file,
            filemode='a' if self.log_file else None
        )
        
        # Set specific loggers
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        
        if self.enable_detailed_logging:
            logging.getLogger("folk_ingestion").setLevel(logging.DEBUG)
    
    def get_neo4j_connection_config(self) -> Dict[str, Any]:
        """Get Neo4j connection configuration"""
        
        return {
            "uri": self.neo4j_uri,
            "username": self.neo4j_username,
            "password": self.neo4j_password,
            "database": self.neo4j_database
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)"""
        
        config_dict = {
            "folk_api": {
                "base_url": self.base_url,
                "rate_limit": self.rate_limit,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "page_size": self.page_size,
                "api_keys_count": len(self.api_keys)
            },
            "neo4j": {
                "uri": self.neo4j_uri.split("@")[-1] if "@" in self.neo4j_uri else self.neo4j_uri,  # Hide credentials
                "database": self.neo4j_database,
                "username": self.neo4j_username[:3] + "***" if len(self.neo4j_username) > 3 else "***"
            },
            "ingestion": {
                "dry_run": self.dry_run,
                "batch_size": self.batch_size,
                "max_concurrent_requests": self.max_concurrent_requests,
                "detailed_logging": self.enable_detailed_logging,
                "backup_enabled": self.backup_before_ingestion
            },
            "logging": {
                "level": self.log_level,
                "file": self.log_file
            }
        }
        
        return config_dict


# Environment validation
def validate_environment() -> Dict[str, Any]:
    """
    Validate that all required environment variables are present
    
    Returns:
        Dict with validation results and missing variables
    """
    
    required_vars = [
        "FOLK_API_KEYS",
        "NEO4J_URI", 
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD"
    ]
    
    optional_vars = [
        "FOLK_API_BASE_URL",
        "FOLK_API_RATE_LIMIT", 
        "FOLK_API_TIMEOUT",
        "FOLK_API_MAX_RETRIES",
        "FOLK_API_PAGE_SIZE",
        "NEO4J_DATABASE",
        "FOLK_INGESTION_DRY_RUN",
        "FOLK_INGESTION_BATCH_SIZE",
        "FOLK_INGESTION_MAX_CONCURRENT",
        "FOLK_INGESTION_DETAILED_LOGGING",
        "FOLK_INGESTION_BACKUP",
        "FOLK_LOG_LEVEL",
        "FOLK_LOG_FILE"
    ]
    
    missing_required = []
    present_required = []
    present_optional = []
    
    for var in required_vars:
        if os.getenv(var):
            present_required.append(var)
        else:
            missing_required.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            present_optional.append(var)
    
    validation_result = {
        "valid": len(missing_required) == 0,
        "missing_required": missing_required,
        "present_required": present_required,
        "present_optional": present_optional,
        "total_required": len(required_vars),
        "total_present": len(present_required)
    }
    
    return validation_result


def get_sample_env_file() -> str:
    """Generate sample .env file content for Folk ingestion"""
    
    return """# Folk.app CRM Integration Configuration

# Folk API Keys (comma-separated for multiple team members)
FOLK_API_KEYS=folk_key_1,folk_key_2,folk_key_3

# Folk API Configuration (Optional - defaults provided)
FOLK_API_BASE_URL=https://api.folk.app/v1
FOLK_API_RATE_LIMIT=100
FOLK_API_TIMEOUT=30
FOLK_API_MAX_RETRIES=3
FOLK_API_PAGE_SIZE=100

# Neo4j Configuration (Required - already in your .env)
NEO4J_URI=neo4j+s://your-database.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# Ingestion Configuration (Optional)
FOLK_INGESTION_DRY_RUN=false
FOLK_INGESTION_BATCH_SIZE=50
FOLK_INGESTION_MAX_CONCURRENT=5
FOLK_INGESTION_DETAILED_LOGGING=false
FOLK_INGESTION_BACKUP=true

# Logging Configuration (Optional)
FOLK_LOG_LEVEL=INFO
FOLK_LOG_FILE=folk_ingestion.log
"""


# Global configuration instance
_config: Optional[FolkConfig] = None


def get_config() -> FolkConfig:
    """Get global configuration instance"""
    global _config
    
    if _config is None:
        _config = FolkConfig.from_environment()
        _config.validate()
        _config.setup_logging()
    
    return _config


def reset_config():
    """Reset global configuration (for testing)"""
    global _config
    _config = None