# OneVice Backend Test Suite

Comprehensive test suite for the OneVice AI-powered business intelligence platform backend.

## Test Structure

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── ai/                        # AI system tests
│   ├── test_config.py         # AI configuration tests
│   ├── test_llm_router.py     # LLM router tests
│   ├── agents/                # Agent-specific tests
│   │   ├── test_base_agent.py # Base agent functionality
│   │   └── test_sales_agent.py # Sales intelligence agent
│   └── graph/                 # Knowledge graph tests
│       └── test_connection.py # Neo4j connection tests
├── api/                       # API endpoint tests
│   └── test_ai_endpoints.py   # AI API endpoints
├── test_integration.py        # Integration tests
└── README.md                  # This file
```

## Test Categories

### Unit Tests
- **AI Configuration**: Test AI system configuration and environment variables
- **LLM Router**: Test routing between Together.ai and OpenAI providers
- **Base Agent**: Test core agent functionality and conversation management
- **Sales Agent**: Test sales intelligence agent capabilities
- **Neo4j Connection**: Test database connection and query execution

### Integration Tests
- **End-to-End Workflows**: Test complete sales intelligence workflows
- **Multi-Agent Orchestration**: Test coordination between multiple agents
- **Knowledge Graph Integration**: Test Neo4j integration with agents
- **Provider Fallback**: Test LLM provider fallback mechanisms
- **Error Recovery**: Test system resilience and error handling

### API Tests
- **Chat Endpoints**: Test AI chat API endpoints
- **Agent Management**: Test agent-specific endpoints
- **WebSocket**: Test real-time communication endpoints

## Running Tests

### Prerequisites
```bash
# Install test dependencies
cd backend
pip install pytest pytest-asyncio pytest-cov

# Set test environment variables
export TOGETHER_API_KEY="test_together_key"
export OPENAI_API_KEY="test_openai_key"
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="test_password"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/ai/ tests/api/ -m "not integration"

# Integration tests only
pytest tests/test_integration.py

# AI system tests
pytest tests/ai/

# API tests
pytest tests/api/

# Specific test file
pytest tests/ai/test_llm_router.py

# Specific test method
pytest tests/ai/test_llm_router.py::TestLLMRouter::test_route_query_together_provider
```

### Run Tests with Coverage
```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html
```

### Run Tests in Parallel
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run with multiple workers
pytest -n auto
```

## Test Configuration

### Fixtures
- **mock_config**: Mock AI configuration with test environment variables
- **mock_neo4j_driver**: Mock Neo4j driver for database testing
- **mock_redis**: Mock Redis client for memory testing
- **mock_llm_response**: Mock LLM response for provider testing
- **sample_*_data**: Sample data for testing (person, project, company)

### Environment Variables
Tests use separate environment variables to avoid interfering with development:
- `TOGETHER_API_KEY`: Test Together.ai API key
- `OPENAI_API_KEY`: Test OpenAI API key
- `NEO4J_URI`: Test Neo4j connection URI
- `REDIS_HOST`: Test Redis host
- `ENVIRONMENT`: Set to "test" for test mode

### Mocking Strategy
- **Database Connections**: Mocked to avoid requiring live database
- **LLM Providers**: Mocked to avoid API costs and rate limits
- **Redis**: Mocked for consistent test environment
- **Authentication**: Mocked for endpoint testing

## Coverage Goals

- **Overall Coverage**: ≥80%
- **Core AI Modules**: ≥90%
- **Critical Paths**: 100% (authentication, data processing)

### Current Coverage Areas
- ✅ AI configuration and setup
- ✅ LLM routing and provider management
- ✅ Base agent functionality
- ✅ Sales intelligence agent
- ✅ Neo4j connection management
- ✅ API endpoint functionality
- ✅ Error handling and resilience
- ✅ Integration workflows

## Test Data

### Sample Entities
Tests use consistent sample data:
- **Person**: Director with skills, location, union status
- **Project**: Feature film with budget, genre, timeline
- **Company**: Production company with size, specialties

### Mock Responses
- **LLM Responses**: JSON-formatted responses matching expected schemas
- **Database Results**: Realistic Neo4j query results
- **API Responses**: Standard HTTP response formats

## Best Practices

### Test Organization
- Group related tests in classes
- Use descriptive test method names
- Include both positive and negative test cases
- Test error conditions and edge cases

### Async Testing
- Use `@pytest.mark.asyncio` for async tests
- Mock async dependencies properly
- Test concurrent operations where applicable

### Mocking
- Mock external dependencies (databases, APIs)
- Use `AsyncMock` for async operations
- Verify mock calls and arguments

### Assertions
- Test both success and failure cases
- Verify response structure and content
- Check side effects (database writes, cache updates)

## Debugging Tests

### Verbose Output
```bash
pytest -v -s
```

### Debug Specific Test
```bash
pytest tests/ai/test_llm_router.py::TestLLMRouter::test_route_query_together_provider -v -s
```

### Print Debug Information
```python
def test_example():
    result = some_function()
    print(f"Debug: {result}")  # Will show with -s flag
    assert result is not None
```

### Interactive Debugging
```bash
# Install pdb++
pip install pdbpp

# Add breakpoint in test
import pdb; pdb.set_trace()
```

## Continuous Integration

Tests are designed to run in CI/CD environments:
- No external dependencies required
- Environment variables configurable
- Consistent results across environments
- Reasonable execution time (<5 minutes)

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure ≥80% code coverage
3. Include both unit and integration tests
4. Update this README if adding new test categories
5. Run full test suite before committing

For questions about testing, see the main project documentation or contact the development team.