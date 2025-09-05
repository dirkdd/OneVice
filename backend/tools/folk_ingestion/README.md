# Folk.app CRM Data Ingestion Tool

A comprehensive tool for ingesting CRM data from Folk.app into Neo4j, implementing the hybrid model for business development integration with the OneVice platform.

## 🎯 Overview

This tool bridges the gap between your **Production World** (projects, creative concepts, crew) and **Business Development World** (contacts, relationships, sales funnels) by integrating Folk.app CRM data into your Neo4j graph database.

### Key Capabilities

- **Hybrid Data Model**: Ingest core CRM entities while storing Folk IDs for live API lookups
- **Data Provenance Tracking**: Track which team member sourced each contact/deal
- **Relationship Mapping**: Create rich connections between people, organizations, groups, and deals
- **Scalable Processing**: Async operations with batch processing and rate limiting
- **Error Resilience**: Comprehensive error handling with retry logic and transaction rollback
- **Monitoring & Reporting**: Detailed ingestion statistics and progress tracking

## 🏗️ Architecture

### Components

```
folk_ingestion/
├── folk_client.py      # Folk API client with auth & rate limiting
├── folk_models.py      # Pydantic models for data validation
├── folk_ingestion.py   # Main orchestration service
├── config.py           # Configuration management
└── README.md           # This documentation
```

### Data Flow

1. **Authentication**: Multiple Folk API keys for team member access
2. **Data Fetching**: Paginated retrieval of people, companies, groups, deals
3. **Transformation**: Pydantic validation and Neo4j schema mapping
4. **Integration**: Batch insertion with relationship creation
5. **Monitoring**: Statistics tracking and error reporting

## 🚀 Quick Start

### 1. Environment Setup

Add Folk API configuration to your `backend/.env` file:

```env
# Folk API Keys (comma-separated for multiple team members)
FOLK_API_KEYS=folk_key_1,folk_key_2,folk_key_3

# Optional Configuration (defaults provided)
FOLK_API_BASE_URL=https://api.folk.app/v1
FOLK_API_RATE_LIMIT=100
FOLK_API_TIMEOUT=30
FOLK_API_MAX_RETRIES=3
FOLK_API_PAGE_SIZE=100

# Ingestion Configuration
FOLK_INGESTION_DRY_RUN=false
FOLK_INGESTION_BATCH_SIZE=50
FOLK_INGESTION_MAX_CONCURRENT=5
FOLK_INGESTION_DETAILED_LOGGING=false
FOLK_INGESTION_BACKUP=true

# Logging
FOLK_LOG_LEVEL=INFO
FOLK_LOG_FILE=folk_ingestion.log
```

### 2. Install Dependencies

```bash
cd backend
source venv/bin/activate
pip install httpx==0.27.0 pydantic==2.5.3 python-dateutil==2.8.2 tenacity==8.2.3
```

### 3. Run Ingestion

**Command Line Interface:**
```bash
cd backend
python3 -m tools.folk_ingestion.folk_ingestion
```

**Programmatic Usage:**
```python
import asyncio
from tools.folk_ingestion import FolkIngestionService
from tools.folk_ingestion.config import get_config

async def run_ingestion():
    config = get_config()
    
    async with FolkIngestionService(config) as service:
        stats = await service.run_full_ingestion()
        print(f"Processed {stats.people_processed} people")

asyncio.run(run_ingestion())
```

## 📊 Data Mapping

### Node Mappings

| Folk Entity | Neo4j Node | Key Properties | Unique Constraint |
|-------------|------------|----------------|-------------------|
| **Person** | `:Person` | `folkId`, `name`, `email`, `title` | `folkId` |
| **Company** | `:Organization` | `folkId`, `name`, `domain`, `industry` | `folkId` |
| **Group** | `:Group` | `folkId`, `name`, `description` | `folkId` |
| **Deal** | `:Deal` | `folkId`, `name`, `status`, `value` | `folkId` |

### Relationship Mappings

| Relationship | Description | Example |
|--------------|-------------|---------|
| `Person -[:BELONGS_TO]-> Group` | Person is member of group | Contact belongs to "Past Clients" |
| `Deal -[:WITH_CONTACT]-> Person` | Deal has contact person | "Sweet Loren's Deal" with Jane Doe |
| `Deal -[:FOR_ORGANIZATION]-> Organization` | Deal is for organization | Deal for Nike Inc. |
| `Person -[:SOURCED]-> Deal` | Internal user sourced deal | Team member brought in deal |
| `Person -[:OWNS_CONTACT]-> Person/Organization` | Internal user owns contact | Team member manages contact |
| `Deal -[:EVOLVED_INTO]-> Project` | Won deal became project | Deal became active project |

## 🔧 Configuration Options

### API Configuration

```python
# Folk API Settings
FOLK_API_KEYS = "key1,key2,key3"        # Multiple API keys
FOLK_API_BASE_URL = "https://api.folk.app/v1"  # API endpoint
FOLK_API_RATE_LIMIT = 100               # Requests per minute
FOLK_API_TIMEOUT = 30                   # Request timeout (seconds)
FOLK_API_MAX_RETRIES = 3                # Retry attempts
FOLK_API_PAGE_SIZE = 100                # Pagination size
```

### Ingestion Configuration

```python
# Processing Settings
FOLK_INGESTION_DRY_RUN = False          # Preview mode (no DB changes)
FOLK_INGESTION_BATCH_SIZE = 50          # Records per transaction
FOLK_INGESTION_MAX_CONCURRENT = 5       # Concurrent API requests
FOLK_INGESTION_DETAILED_LOGGING = False # Verbose logging
FOLK_INGESTION_BACKUP = True            # Backup before ingestion
```

### Logging Configuration

```python
# Logging Settings
FOLK_LOG_LEVEL = "INFO"                 # DEBUG, INFO, WARNING, ERROR
FOLK_LOG_FILE = "folk_ingestion.log"    # Log file path (optional)
```

## 💡 Usage Examples

### Dry Run Mode

Test the ingestion without making changes:

```bash
# Set environment variable
export FOLK_INGESTION_DRY_RUN=true

# Run ingestion
python3 -m tools.folk_ingestion.folk_ingestion
```

### Batch Processing

Process data in smaller batches for large datasets:

```bash
# Set smaller batch size
export FOLK_INGESTION_BATCH_SIZE=25

# Run ingestion
python3 -m tools.folk_ingestion.folk_ingestion
```

### Detailed Logging

Enable verbose logging for debugging:

```bash
# Enable detailed logging
export FOLK_INGESTION_DETAILED_LOGGING=true
export FOLK_LOG_LEVEL=DEBUG

# Run ingestion
python3 -m tools.folk_ingestion.folk_ingestion
```

## 📈 Monitoring & Statistics

The ingestion process provides comprehensive statistics:

### Timing Metrics
- **Duration**: Total execution time
- **Start/End Times**: Precise timestamps

### API Metrics
- **Requests Made**: Total API calls
- **Keys Processed**: Number of API keys
- **API Errors**: Failed requests

### Data Metrics
- **Records Fetched**: Raw data from Folk
- **Records Processed**: Successfully validated
- **Validation Errors**: Data format issues

### Neo4j Metrics
- **Nodes Created**: New entities in graph
- **Relationships Created**: Connections between entities
- **Transactions Executed**: Database operations
- **Neo4j Errors**: Database operation failures

### Example Output

```
📊 INGESTION COMPLETED
========================
⏱️  Duration: 45.7s
👥 People: 1,234 processed
🏢 Companies: 567 processed
📋 Groups: 23 processed
💼 Deals: 89 processed
🔗 Relationships: 2,456 created
❌ Errors: 0
✅ Ingestion complete!
```

## 🛡️ Error Handling

### API Errors
- **Rate Limiting**: Automatic retry with exponential backoff
- **Authentication**: Clear error messages for invalid API keys
- **Service Unavailable**: Graceful handling of Folk API downtime

### Data Errors
- **Validation**: Pydantic model validation with detailed error messages
- **Duplicate Detection**: Skip already processed entities
- **Malformed Data**: Log and continue with remaining records

### Database Errors
- **Transaction Rollback**: Atomic operations with rollback on failure
- **Connection Issues**: Automatic reconnection attempts
- **Constraint Violations**: Graceful handling of duplicate key errors

## 🔄 Scheduling

### Manual Execution
Run ingestion manually when needed:
```bash
python3 -m tools.folk_ingestion.folk_ingestion
```

### Cron Job (Daily)
Schedule daily ingestion at 2 AM:
```bash
# Add to crontab
0 2 * * * cd /path/to/backend && python3 -m tools.folk_ingestion.folk_ingestion >> /var/log/folk_ingestion.log 2>&1
```

### Systemd Timer (Hourly)
Create systemd service for hourly ingestion:
```ini
# /etc/systemd/system/folk-ingestion.service
[Unit]
Description=Folk CRM Data Ingestion
After=network.target

[Service]
Type=oneshot
User=onevice
WorkingDirectory=/path/to/backend
ExecStart=/path/to/backend/venv/bin/python -m tools.folk_ingestion.folk_ingestion
Environment=FOLK_INGESTION_DRY_RUN=false

# /etc/systemd/system/folk-ingestion.timer
[Unit]
Description=Run Folk Ingestion Hourly
Requires=folk-ingestion.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: `FOLK_API_KEYS environment variable is required`
```bash
# Solution: Add Folk API keys to .env
echo "FOLK_API_KEYS=your_folk_api_key_here" >> backend/.env
```

**Issue**: `Failed to establish Neo4j connection`
```bash
# Solution: Verify Neo4j credentials in .env
# Check NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
```

**Issue**: `Rate limit exceeded`
```bash
# Solution: Reduce rate limit in configuration
export FOLK_API_RATE_LIMIT=50
```

**Issue**: `Timeout during API request`
```bash
# Solution: Increase timeout
export FOLK_API_TIMEOUT=60
```

### Debug Mode

Enable maximum debugging:
```bash
export FOLK_LOG_LEVEL=DEBUG
export FOLK_INGESTION_DETAILED_LOGGING=true
python3 -m tools.folk_ingestion.folk_ingestion
```

### Validation

Validate environment before running:
```python
from tools.folk_ingestion.config import validate_environment

validation = validate_environment()
if not validation["valid"]:
    print("Missing variables:", validation["missing_required"])
```

## 🔧 Advanced Configuration

### Custom Neo4j Connection

```python
from tools.folk_ingestion import FolkIngestionService
from tools.folk_ingestion.config import FolkConfig
from database.neo4j_client import ConnectionConfig

# Custom Neo4j configuration
neo4j_config = ConnectionConfig(
    uri="neo4j+s://custom-host:7687",
    username="custom_user",
    password="custom_password",
    database="custom_database"
)

# Custom Folk configuration
folk_config = FolkConfig(
    api_keys=["your_api_key"],
    batch_size=25,
    max_concurrent_requests=3
)

async with FolkIngestionService(folk_config) as service:
    service.neo4j_client = Neo4jClient(neo4j_config)
    await service.neo4j_client.connect()
    stats = await service.run_full_ingestion()
```

### Custom Processing

```python
# Process specific data types only
service = FolkIngestionService(config)

# Process only people and companies
async with folk_client:
    people = await folk_client.get_all_people_paginated()
    companies = await folk_client.get_all_companies_paginated()
    
    await service._process_people(people, "user_123")
    await service._process_companies(companies, "user_123")
```

## 📚 API Reference

### FolkClient

```python
async with FolkClient(api_key="your_key") as client:
    # Get user profile
    profile = await client.get_user_profile()
    
    # Get data with pagination
    people = await client.get_all_people_paginated(page_size=100)
    companies = await client.get_all_companies_paginated()
    groups = await client.get_all_groups_paginated()
    
    # Get deals for specific group
    deals = await client.get_deals_for_group("group_id")
    
    # Get client statistics
    stats = client.get_stats()
```

### FolkIngestionService

```python
config = FolkConfig.from_environment()

async with FolkIngestionService(config) as service:
    # Run full ingestion
    stats = await service.run_full_ingestion()
    
    # Access statistics
    print(f"Duration: {stats.duration_seconds}s")
    print(f"People processed: {stats.people_processed}")
    print(f"Errors: {len(stats.validation_errors)}")
```

### Data Models

```python
# Create models from Folk API data
person = FolkPerson.from_folk_api(api_response_data)
company = FolkCompany.from_folk_api(api_response_data)
group = FolkGroup.from_folk_api(api_response_data)
deal = FolkDeal.from_folk_api(api_response_data)

# Transform to Neo4j properties
person_props = person.to_neo4j_node(data_owner_id="user_123")
```

## 🤝 Contributing

### Development Setup

1. Install dependencies:
```bash
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest tests/
```

3. Code formatting:
```bash
black folk_ingestion/
isort folk_ingestion/
```

### Adding New Features

1. **New Data Types**: Extend `folk_models.py` with new Pydantic models
2. **API Endpoints**: Add methods to `folk_client.py`
3. **Processing Logic**: Update `folk_ingestion.py` with new processing flows
4. **Configuration**: Add new settings to `config.py`

## 📄 License

This Folk ingestion tool is part of the OneVice platform and is licensed under MIT License.

## 🆘 Support

- **Issues**: Report bugs via GitHub issues
- **Documentation**: See `docs/` directory for additional guides  
- **Team Support**: Contact OneVice development team
- **Folk API**: https://developer.folk.app/api-reference/overview

---

**Last Updated**: 2025-09-04  
**Version**: 1.0.0  
**Maintainer**: OneVice Team