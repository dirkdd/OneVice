"""
Tests for Neo4j connection manager.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from neo4j import AsyncDriver, AsyncSession

from app.ai.graph.connection import Neo4jConnectionManager
from app.ai.config import AIConfig


class TestNeo4jConnectionManager:
    """Test Neo4j connection manager."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock AI configuration."""
        config = MagicMock(spec=AIConfig)
        config.neo4j_uri = "neo4j://localhost:7687"
        config.neo4j_username = "neo4j"
        config.neo4j_password = "test_password"
        config.neo4j_database = "neo4j"
        return config
    
    @pytest.fixture
    def connection_manager(self, mock_config):
        """Create connection manager instance."""
        with patch('app.ai.graph.connection.AsyncGraphDatabase'):
            manager = Neo4jConnectionManager(mock_config)
            return manager
    
    @pytest.mark.asyncio
    async def test_connection_initialization(self, connection_manager, mock_config):
        """Test connection manager initialization."""
        assert connection_manager.config == mock_config
        assert connection_manager.driver is None
        assert not connection_manager._connected
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connection_manager):
        """Test successful database connection."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        
        with patch('app.ai.graph.connection.AsyncGraphDatabase.driver', return_value=mock_driver):
            await connection_manager.connect()
            
            assert connection_manager.driver == mock_driver
            assert connection_manager._connected
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, connection_manager):
        """Test database connection failure."""
        with patch('app.ai.graph.connection.AsyncGraphDatabase.driver', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await connection_manager.connect()
            
            assert connection_manager.driver is None
            assert not connection_manager._connected
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connection_manager):
        """Test database disconnection."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        await connection_manager.disconnect()
        
        mock_driver.close.assert_called_once()
        assert connection_manager.driver is None
        assert not connection_manager._connected
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self, connection_manager):
        """Test successful query execution."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = AsyncMock()
        mock_record = MagicMock()
        mock_record.data.return_value = {"name": "John Doe", "role": "Director"}
        mock_result.__aiter__.return_value = [mock_record]
        
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        query = "MATCH (p:Person) WHERE p.name = $name RETURN p"
        params = {"name": "John Doe"}
        
        results = await connection_manager.execute_query(query, params)
        
        assert len(results) == 1
        assert results[0] == {"name": "John Doe", "role": "Director"}
        mock_session.run.assert_called_once_with(query, params)
    
    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self, connection_manager):
        """Test query execution when not connected."""
        query = "MATCH (p:Person) RETURN p"
        
        with pytest.raises(RuntimeError, match="Not connected to database"):
            await connection_manager.execute_query(query)
    
    @pytest.mark.asyncio
    async def test_execute_query_with_retry(self, connection_manager):
        """Test query execution with retry logic."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        mock_session = AsyncMock(spec=AsyncSession)
        
        # First call fails, second succeeds
        mock_session.run.side_effect = [
            Exception("Temporary failure"),
            AsyncMock(__aiter__=AsyncMock(return_value=iter([])))
        ]
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        query = "MATCH (p:Person) RETURN p"
        
        with patch('asyncio.sleep'):  # Mock sleep to speed up test
            results = await connection_manager.execute_query(query, max_retries=2)
            
            assert results == []
            assert mock_session.run.call_count == 2
    
    @pytest.mark.asyncio
    async def test_run_vector_query(self, connection_manager):
        """Test vector similarity query execution."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = AsyncMock()
        mock_record = MagicMock()
        mock_record.data.return_value = {
            "node": {"name": "John Director", "bio": "Experienced director"},
            "score": 0.85
        }
        mock_result.__aiter__.return_value = [mock_record]
        
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        vector = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        results = await connection_manager.run_vector_query(
            index_name="person_bio_embedding",
            vector=vector,
            top_k=5,
            similarity_threshold=0.8
        )
        
        assert len(results) == 1
        assert results[0]["score"] == 0.85
        assert "John Director" in results[0]["node"]["name"]
    
    @pytest.mark.asyncio
    async def test_create_indexes(self, connection_manager):
        """Test index creation."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = []
        
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        await connection_manager.create_indexes()
        
        # Should have made multiple calls to create indexes
        assert mock_session.run.call_count >= 3  # At least property and vector indexes
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, connection_manager):
        """Test successful health check."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = AsyncMock()
        mock_record = MagicMock()
        mock_record.data.return_value = {"result": 1}
        mock_result.__aiter__.return_value = [mock_record]
        
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        is_healthy = await connection_manager.health_check()
        
        assert is_healthy
        mock_session.run.assert_called_once_with("RETURN 1 as result")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, connection_manager):
        """Test health check failure."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.run.side_effect = Exception("Database error")
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        is_healthy = await connection_manager.health_check()
        
        assert not is_healthy
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, connection_manager):
        """Test transaction rollback on error."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        
        # Mock transaction that fails
        mock_transaction.run.side_effect = Exception("Query failed")
        mock_session.begin_transaction.return_value.__aenter__.return_value = mock_transaction
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        
        connection_manager.driver = mock_driver
        connection_manager._connected = True
        
        queries = ["CREATE (p:Person {name: 'Test'})", "CREATE (c:Company {name: 'Test Co'})"]
        
        with pytest.raises(Exception, match="Query failed"):
            await connection_manager.execute_transaction(queries)
        
        # Should have attempted rollback
        mock_transaction.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_usage(self, connection_manager):
        """Test using connection manager as async context manager."""
        mock_driver = AsyncMock(spec=AsyncDriver)
        
        with patch('app.ai.graph.connection.AsyncGraphDatabase.driver', return_value=mock_driver):
            async with connection_manager:
                assert connection_manager._connected
                assert connection_manager.driver == mock_driver
            
            # Should disconnect when exiting context
            mock_driver.close.assert_called_once()
            assert not connection_manager._connected