"""
Graph Database Integration

Neo4j integration for entertainment industry knowledge graphs
with vector search capabilities.
"""

from .connection import Neo4jClient
from .schema import EntertainmentSchema
from .queries import EntertainmentQueries

__all__ = ["Neo4jClient", "EntertainmentSchema", "EntertainmentQueries"]