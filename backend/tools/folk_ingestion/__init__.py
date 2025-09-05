"""
Folk.app CRM Data Ingestion Tool for OneVice

This package provides tools for ingesting CRM data from Folk.app into Neo4j,
implementing the hybrid model for business development integration.

Components:
- folk_client: API client for Folk.app interactions
- folk_models: Data models and validation
- folk_ingestion: Main ingestion orchestration
- config: Configuration management
"""

from .folk_client import FolkClient
from .folk_models import FolkPerson, FolkCompany, FolkGroup, FolkDeal
from .folk_ingestion import FolkIngestionService
from .config import FolkConfig

__version__ = "1.0.0"
__author__ = "OneVice Team"

__all__ = [
    "FolkClient",
    "FolkPerson",
    "FolkCompany", 
    "FolkGroup",
    "FolkDeal",
    "FolkIngestionService",
    "FolkConfig"
]