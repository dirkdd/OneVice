# Neo4j Environment Variable Configuration Guide

**Version:** 1.0  
**Date:** September 2, 2025  
**Project:** OneVice Entertainment Intelligence Platform

## Overview

This document provides comprehensive guidance for configuring Neo4j environment variables across different deployment environments (development, staging, production) for the OneVice project.

## Environment Variables Reference

### Core Connection Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEO4J_URI` | ✅ Yes | Neo4j database connection URI | `neo4j+s://db-123.databases.neo4j.io:7687` |
| `NEO4J_USERNAME` | ✅ Yes | Database username | `neo4j` |
| `NEO4J_PASSWORD` | ✅ Yes | Database password | `your-secure-password` |
| `NEO4J_DATABASE` | ⚪ Optional | Target database name | `neo4j` (default) |

### Connection Pool Configuration

| Variable | Required | Description | Default | Range |
|----------|----------|-------------|---------|-------|
| `NEO4J_MAX_CONNECTION_LIFETIME` | ⚪ Optional | Max connection lifetime (seconds) | 3600 | 300-7200 |
| `NEO4J_MAX_CONNECTION_POOL_SIZE` | ⚪ Optional | Max concurrent connections | 100 | 10-500 |
| `NEO4J_CONNECTION_TIMEOUT` | ⚪ Optional | Connection timeout (seconds) | 30 | 5-120 |

### Health Monitoring Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `NEO4J_HEALTH_CHECK_INTERVAL` | ⚪ Optional | Health check frequency (seconds) | 300 |
| `NEO4J_RETRY_ATTEMPTS` | ⚪ Optional | Max retry attempts for failed operations | 3 |
| `NEO4J_RETRY_DELAY` | ⚪ Optional | Delay between retries (seconds) | 1 |

### Security and Compliance

| Variable | Required | Description | Values |
|----------|----------|-------------|--------|
| `NEO4J_ENCRYPTED` | ⚪ Optional | Force encryption (informational) | `true`/`false` |
| `NEO4J_LOG_QUERIES` | ⚪ Optional | Enable query logging | `true`/`false` |
| `NEO4J_LOG_LEVEL` | ⚪ Optional | Neo4j client log level | `INFO`/`DEBUG`/`WARNING` |

## Environment-Specific Configurations

### Development Environment (.env)

**File Location:** `/backend/.env`

```bash
# Neo4j Development Configuration
# ================================

# Core Connection (Neo4j Aura Development Instance)
NEO4J_URI=neo4j+s://dev-12345678.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=development-secure-password-123
NEO4J_DATABASE=neo4j

# Connection Pool - Development Optimized
NEO4J_MAX_CONNECTION_LIFETIME=1800          # 30 minutes
NEO4J_MAX_CONNECTION_POOL_SIZE=20           # Smaller pool for dev
NEO4J_CONNECTION_TIMEOUT=15                 # Faster timeout for dev

# Health Monitoring - Frequent for Development
NEO4J_HEALTH_CHECK_INTERVAL=60              # Check every minute
NEO4J_RETRY_ATTEMPTS=2                      # Fewer retries in dev
NEO4J_RETRY_DELAY=0.5                       # Faster retry for dev

# Development Features
NEO4J_ENCRYPTED=true                        # Informational flag
NEO4J_LOG_QUERIES=true                      # Enable query logging
NEO4J_LOG_LEVEL=DEBUG                       # Verbose logging for debugging

# Development Performance Tuning
NEO4J_QUERY_TIMEOUT=30                      # 30 second query timeout
NEO4J_TX_TIMEOUT=60                         # 60 second transaction timeout
```

### Staging Environment (Render Environment Variables)

```bash
# Neo4j Staging Configuration
# ===========================

# Core Connection (Neo4j Aura Staging Instance)  
NEO4J_URI=neo4j+s://staging-87654321.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=staging-ultra-secure-password-456
NEO4J_DATABASE=neo4j

# Connection Pool - Staging Optimized
NEO4J_MAX_CONNECTION_LIFETIME=3600          # 1 hour
NEO4J_MAX_CONNECTION_POOL_SIZE=50           # Medium pool for staging
NEO4J_CONNECTION_TIMEOUT=30                 # Standard timeout

# Health Monitoring - Moderate for Staging
NEO4J_HEALTH_CHECK_INTERVAL=300             # Check every 5 minutes
NEO4J_RETRY_ATTEMPTS=3                      # Standard retries
NEO4J_RETRY_DELAY=1                         # Standard retry delay

# Staging Features
NEO4J_ENCRYPTED=true                        # Informational flag
NEO4J_LOG_QUERIES=false                     # Disable query logging
NEO4J_LOG_LEVEL=INFO                        # Standard logging

# Staging Performance Tuning
NEO4J_QUERY_TIMEOUT=60                      # 60 second query timeout
NEO4J_TX_TIMEOUT=120                        # 2 minute transaction timeout
```

### Production Environment (Render Environment Variables)

```bash
# Neo4j Production Configuration
# ==============================

# Core Connection (Neo4j Aura Production Instance)
NEO4J_URI=neo4j+s://prod-99887766.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=production-maximum-security-password-789
NEO4J_DATABASE=neo4j

# Connection Pool - Production Optimized
NEO4J_MAX_CONNECTION_LIFETIME=7200          # 2 hours
NEO4J_MAX_CONNECTION_POOL_SIZE=100          # Large pool for production
NEO4J_CONNECTION_TIMEOUT=45                 # Conservative timeout

# Health Monitoring - Conservative for Production
NEO4J_HEALTH_CHECK_INTERVAL=600             # Check every 10 minutes
NEO4J_RETRY_ATTEMPTS=5                      # More retries in production
NEO4J_RETRY_DELAY=2                         # Longer retry delay

# Production Security
NEO4J_ENCRYPTED=true                        # Informational flag
NEO4J_LOG_QUERIES=false                     # Disable query logging
NEO4J_LOG_LEVEL=WARNING                     # Minimal logging

# Production Performance Tuning
NEO4J_QUERY_TIMEOUT=120                     # 2 minute query timeout
NEO4J_TX_TIMEOUT=300                        # 5 minute transaction timeout

# Production Monitoring
NEO4J_METRICS_ENABLED=true                  # Enable metrics collection
NEO4J_PERFORMANCE_MONITORING=true           # Enable performance tracking
```

## Environment Variable Validation

### Validation Script

Create `/backend/scripts/validate_neo4j_env.py`:

```python
#!/usr/bin/env python3
"""
Neo4j Environment Variables Validation Script
Validates configuration across different environments
"""

import os
import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from dotenv import load_dotenv

class EnvironmentValidator:
    """Validates Neo4j environment configuration"""
    
    REQUIRED_VARS = [
        'NEO4J_URI',
        'NEO4J_USERNAME', 
        'NEO4J_PASSWORD'
    ]
    
    OPTIONAL_VARS = {
        'NEO4J_DATABASE': {'default': 'neo4j', 'type': str},
        'NEO4J_MAX_CONNECTION_LIFETIME': {'default': 3600, 'type': int, 'range': (300, 7200)},
        'NEO4J_MAX_CONNECTION_POOL_SIZE': {'default': 100, 'type': int, 'range': (10, 500)},
        'NEO4J_CONNECTION_TIMEOUT': {'default': 30, 'type': int, 'range': (5, 120)},
        'NEO4J_HEALTH_CHECK_INTERVAL': {'default': 300, 'type': int, 'range': (60, 3600)},
        'NEO4J_RETRY_ATTEMPTS': {'default': 3, 'type': int, 'range': (1, 10)},
        'NEO4J_RETRY_DELAY': {'default': 1, 'type': float, 'range': (0.1, 10)},
        'NEO4J_LOG_LEVEL': {'default': 'INFO', 'type': str, 'values': ['DEBUG', 'INFO', 'WARNING', 'ERROR']}
    }
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.errors = []
        self.warnings = []
        self.config = {}
    
    def validate(self) -> Tuple[bool, Dict]:
        """Validate all environment variables"""
        
        # Load environment variables
        if self.environment == 'development':
            load_dotenv()
        
        # Validate required variables
        self._validate_required_vars()
        
        # Validate optional variables
        self._validate_optional_vars()
        
        # Validate URI format and security
        self._validate_uri()
        
        # Validate password strength
        self._validate_password_strength()
        
        # Environment-specific validations
        self._validate_environment_specific()
        
        return len(self.errors) == 0, {
            'environment': self.environment,
            'config': self.config,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def _validate_required_vars(self):
        """Validate required environment variables"""
        for var in self.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required variable: {var}")
            else:
                # Mask password in config
                display_value = value if var != 'NEO4J_PASSWORD' else '*' * len(value)
                self.config[var] = display_value
    
    def _validate_optional_vars(self):
        """Validate optional environment variables"""
        for var, settings in self.OPTIONAL_VARS.items():
            value = os.getenv(var)
            
            if value:
                # Type validation
                try:
                    if settings['type'] == int:
                        parsed_value = int(value)
                    elif settings['type'] == float:
                        parsed_value = float(value)
                    else:
                        parsed_value = value
                    
                    # Range validation
                    if 'range' in settings:
                        min_val, max_val = settings['range']
                        if not (min_val <= parsed_value <= max_val):
                            self.errors.append(
                                f"{var} value {parsed_value} outside valid range {min_val}-{max_val}"
                            )
                    
                    # Value validation
                    if 'values' in settings and parsed_value not in settings['values']:
                        self.errors.append(
                            f"{var} value '{parsed_value}' not in valid values: {settings['values']}"
                        )
                    
                    self.config[var] = parsed_value
                    
                except ValueError:
                    self.errors.append(f"{var} has invalid {settings['type'].__name__} value: {value}")
            else:
                # Use default value
                self.config[var] = settings['default']
                self.warnings.append(f"{var} not set, using default: {settings['default']}")
    
    def _validate_uri(self):
        """Validate Neo4j URI format and security"""
        uri = os.getenv('NEO4J_URI')
        if not uri:
            return
        
        try:
            parsed = urlparse(uri)
            
            # Validate scheme
            valid_schemes = ['neo4j', 'neo4j+s', 'bolt', 'bolt+s']
            if parsed.scheme not in valid_schemes:
                self.errors.append(f"Invalid URI scheme: {parsed.scheme}. Valid schemes: {valid_schemes}")
            
            # Security recommendations
            if parsed.scheme in ['neo4j', 'bolt']:
                if self.environment == 'production':
                    self.errors.append("Unencrypted connection scheme in production environment")
                else:
                    self.warnings.append("Using unencrypted connection scheme")
            
            # Validate hostname
            if not parsed.hostname:
                self.errors.append("Missing hostname in NEO4J_URI")
            
            # Validate port
            if parsed.port and not (1 <= parsed.port <= 65535):
                self.errors.append(f"Invalid port number: {parsed.port}")
            
            # Aura-specific validations
            if 'databases.neo4j.io' in uri:
                if not parsed.scheme.endswith('+s'):
                    self.errors.append("Neo4j Aura requires encrypted connection (use neo4j+s://)")
                if parsed.port and parsed.port != 7687:
                    self.warnings.append("Neo4j Aura typically uses port 7687")
            
        except Exception as e:
            self.errors.append(f"Invalid URI format: {e}")
    
    def _validate_password_strength(self):
        """Validate password strength requirements"""
        password = os.getenv('NEO4J_PASSWORD')
        if not password:
            return
        
        if len(password) < 8:
            self.errors.append("Password must be at least 8 characters long")
        
        if self.environment == 'production':
            # Production password requirements
            if len(password) < 16:
                self.warnings.append("Production password should be at least 16 characters")
            
            if not re.search(r'[A-Z]', password):
                self.warnings.append("Password should contain uppercase letters")
            
            if not re.search(r'[a-z]', password):
                self.warnings.append("Password should contain lowercase letters")
            
            if not re.search(r'\d', password):
                self.warnings.append("Password should contain numbers")
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                self.warnings.append("Password should contain special characters")
    
    def _validate_environment_specific(self):
        """Environment-specific validations"""
        
        if self.environment == 'development':
            # Development-specific checks
            if self.config.get('NEO4J_MAX_CONNECTION_POOL_SIZE', 0) > 50:
                self.warnings.append("Large connection pool size for development environment")
            
            if not self.config.get('NEO4J_LOG_QUERIES'):
                self.warnings.append("Consider enabling NEO4J_LOG_QUERIES=true for development")
        
        elif self.environment == 'production':
            # Production-specific checks
            if self.config.get('NEO4J_MAX_CONNECTION_POOL_SIZE', 0) < 50:
                self.warnings.append("Consider increasing connection pool size for production")
            
            if self.config.get('NEO4J_LOG_QUERIES'):
                self.warnings.append("Query logging enabled in production (performance impact)")
            
            if self.config.get('NEO4J_LOG_LEVEL') == 'DEBUG':
                self.errors.append("DEBUG logging not recommended for production")

def main():
    """Run environment validation"""
    import sys
    
    # Detect environment
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    print(f"🔍 Validating Neo4j Environment Configuration")
    print(f"📋 Environment: {environment.title()}")
    print('=' * 60)
    
    validator = EnvironmentValidator(environment)
    is_valid, result = validator.validate()
    
    # Display results
    print(f"\n📊 Configuration Summary:")
    for key, value in result['config'].items():
        print(f"   {key}: {value}")
    
    if result['warnings']:
        print(f"\n⚠️  Warnings ({len(result['warnings'])}):")
        for warning in result['warnings']:
            print(f"   • {warning}")
    
    if result['errors']:
        print(f"\n❌ Errors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"   • {error}")
    else:
        print(f"\n✅ No configuration errors found!")
    
    print('=' * 60)
    
    if is_valid:
        print("🎉 Environment configuration is valid!")
        if result['warnings']:
            print("📋 Review warnings above for optimization opportunities")
    else:
        print("❌ Environment configuration has errors that must be fixed")
    
    return is_valid

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

### Quick Validation Command

```bash
# Validate development environment
cd backend && python scripts/validate_neo4j_env.py

# Validate specific environment
ENVIRONMENT=production python scripts/validate_neo4j_env.py
```

## Environment-Specific Setup Instructions

### Development Setup

1. **Create `.env` file:**
```bash
cd backend
cp .env.example .env  # If template exists
```

2. **Configure development variables:**
```bash
# Edit .env with your development values
nano .env
```

3. **Validate configuration:**
```bash
python scripts/validate_neo4j_env.py
```

4. **Test connection:**
```bash
python test_connections_fixed.py
```

### Staging/Production Setup (Render)

1. **Set environment variables in Render Dashboard:**
   - Go to your service in Render Dashboard
   - Navigate to "Environment" tab
   - Add each variable individually

2. **Use environment-specific values:**
   - Use separate Neo4j Aura instances for staging/production
   - Use stronger passwords for production
   - Configure appropriate connection pool sizes

3. **Validate deployment:**
```bash
# After deployment, check logs for validation results
render logs tail --service your-service-name
```

## Security Best Practices

### Password Management

**Development:**
- Use descriptive but secure passwords
- Include environment identifier in password
- Minimum 12 characters with mixed case and numbers

**Production:**
- Minimum 20 characters
- Include uppercase, lowercase, numbers, and symbols
- Use password manager or secure generation tool
- Rotate passwords quarterly

### Connection Security

**Always Use Encrypted Connections:**
```bash
# ✅ CORRECT - Encrypted connection
NEO4J_URI=neo4j+s://database.databases.neo4j.io:7687

# ❌ WRONG - Unencrypted in production
NEO4J_URI=neo4j://database.databases.neo4j.io:7687
```

**Network Security:**
- Use Neo4j Aura for managed security
- Implement IP allowlisting if supported
- Monitor connection attempts and failures
- Use VPN for additional security layers

### Environment Isolation

**Separate Instances:**
- Development: `dev-xxx.databases.neo4j.io`
- Staging: `staging-xxx.databases.neo4j.io`  
- Production: `prod-xxx.databases.neo4j.io`

**Access Control:**
- Use different credentials for each environment
- Implement least-privilege access
- Regular credential rotation
- Monitor and audit access patterns

## Environment Variable Templates

### .env Template for Development

```bash
# ===============================================
# OneVice Neo4j Development Configuration
# ===============================================

# Core Connection Settings
NEO4J_URI=neo4j+s://YOUR_DEV_DATABASE.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-development-password
NEO4J_DATABASE=neo4j

# Connection Pool Configuration
NEO4J_MAX_CONNECTION_LIFETIME=1800
NEO4J_MAX_CONNECTION_POOL_SIZE=20
NEO4J_CONNECTION_TIMEOUT=15

# Health Monitoring
NEO4J_HEALTH_CHECK_INTERVAL=60
NEO4J_RETRY_ATTEMPTS=2
NEO4J_RETRY_DELAY=0.5

# Development Features
NEO4J_ENCRYPTED=true
NEO4J_LOG_QUERIES=true
NEO4J_LOG_LEVEL=DEBUG

# ===============================================
# Other OneVice Services
# ===============================================
# (Add other service configurations here)
```

### Render Environment Variables (Production)

Copy these to your Render service environment variables:

```
NEO4J_URI=neo4j+s://YOUR_PROD_DATABASE.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-production-ultra-secure-password
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_LIFETIME=7200
NEO4J_MAX_CONNECTION_POOL_SIZE=100
NEO4J_CONNECTION_TIMEOUT=45
NEO4J_HEALTH_CHECK_INTERVAL=600
NEO4J_RETRY_ATTEMPTS=5
NEO4J_RETRY_DELAY=2
NEO4J_ENCRYPTED=true
NEO4J_LOG_QUERIES=false
NEO4J_LOG_LEVEL=WARNING
```

## Troubleshooting Environment Issues

### Common Environment Problems

**Problem:** Variables not loading
```bash
# Check if .env file exists and is readable
ls -la .env
cat .env | grep NEO4J

# Check if dotenv is loading correctly
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('NEO4J_URI'))"
```

**Problem:** Variable values not updating
```bash
# Clear environment and reload
unset NEO4J_URI NEO4J_USERNAME NEO4J_PASSWORD
source .env  # If using shell source
# or restart application
```

**Problem:** Variables work locally but not in deployment
```bash
# Check deployment environment variables
render env list --service your-service-name

# Verify variables are set correctly
render shell --service your-service-name
echo $NEO4J_URI
```

### Environment Debugging Commands

```bash
# List all Neo4j-related environment variables
env | grep NEO4J

# Validate environment configuration
python scripts/validate_neo4j_env.py

# Test connection with current environment
python test_connections_fixed.py

# Debug comprehensive Neo4j setup
python debug_neo4j_connection.py
```

---

*This configuration should be reviewed and updated when deploying to new environments or when Neo4j connection requirements change.*