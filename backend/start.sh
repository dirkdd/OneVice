#!/bin/bash

# OneVice Backend Startup Script
# Production-ready FastAPI server with comprehensive authentication system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"
DEFAULT_WORKERS="4"
DEFAULT_LOG_LEVEL="info"

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is available
port_available() {
    ! nc -z localhost $1 >/dev/null 2>&1
}

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=0
    
    print_info "Waiting for $service to be available at $host:$port..."
    
    while ! nc -z $host $port >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            print_error "$service is not available after $max_attempts attempts"
            return 1
        fi
        sleep 1
    done
    
    print_success "$service is available"
    return 0
}

# Function to check environment variables
check_environment() {
    print_info "Checking environment configuration..."
    
    local missing_vars=()
    
    # Required environment variables
    required_vars=(
        "DATABASE_URL"
        "JWT_SECRET_KEY"
        "ENCRYPTION_KEY"
    )
    
    # Recommended environment variables
    recommended_vars=(
        "REDIS_URL"
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
        "CLERK_SECRET_KEY"
        "NEO4J_URI"
        "NEO4J_USERNAME"
        "NEO4J_PASSWORD"
    )
    
    # Check required variables
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        print_error "Please set these variables and try again."
        exit 1
    fi
    
    # Check recommended variables
    local missing_recommended=()
    for var in "${recommended_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_recommended+=("$var")
        fi
    done
    
    if [ ${#missing_recommended[@]} -ne 0 ]; then
        print_warning "Missing recommended environment variables:"
        for var in "${missing_recommended[@]}"; do
            print_warning "  - $var"
        done
        print_warning "Some features may not be available."
    fi
    
    print_success "Environment configuration checked"
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking system dependencies..."
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! command_exists pip3; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found, creating one..."
        python3 -m venv venv
    fi
    
    print_success "System dependencies checked"
}

# Function to install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    print_success "Python dependencies installed"
}

# Function to check database connectivity
check_databases() {
    print_info "Checking database connectivity..."
    
    # Test database connections using the test script
    if [ -f "test_connections.py" ]; then
        python test_connections.py
        if [ $? -ne 0 ]; then
            print_warning "Database connectivity test failed"
            print_warning "The server will start but some features may not work"
        else
            print_success "Database connectivity verified"
        fi
    else
        print_warning "Database connectivity test not found"
    fi
}

# Function to initialize database schema
init_database() {
    print_info "Initializing database schema..."
    
    # Run database initialization
    python -c "
import asyncio
from database import initialize_database
from auth.database import initialize_postgres_schema
import asyncpg
import os

async def init_schema():
    try:
        # Initialize main database
        result = await initialize_database(ensure_schema=True)
        if result['success']:
            print('✓ Database initialized successfully')
        else:
            print('✗ Database initialization failed:', result.get('error'))
            
        # Initialize PostgreSQL schema for auth
        if os.getenv('DATABASE_URL'):
            try:
                postgres_pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
                await initialize_postgres_schema(postgres_pool)
                await postgres_pool.close()
                print('✓ PostgreSQL auth schema initialized')
            except Exception as e:
                print('✗ PostgreSQL schema initialization failed:', e)
                
    except Exception as e:
        print('✗ Schema initialization failed:', e)

if __name__ == '__main__':
    asyncio.run(init_schema())
"
    
    print_success "Database schema initialization completed"
}

# Function to run tests
run_tests() {
    print_info "Running test suite..."
    
    if command_exists pytest; then
        pytest tests/ -v --tb=short
        if [ $? -eq 0 ]; then
            print_success "All tests passed"
        else
            print_warning "Some tests failed - check output above"
        fi
    else
        print_warning "pytest not available, skipping tests"
    fi
}

# Function to start the server
start_server() {
    local host=${HOST:-$DEFAULT_HOST}
    local port=${PORT:-$DEFAULT_PORT}
    local workers=${WORKERS:-$DEFAULT_WORKERS}
    local log_level=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
    local reload=${RELOAD:-false}
    
    print_info "Starting OneVice Backend Server..."
    print_info "Host: $host"
    print_info "Port: $port"
    print_info "Workers: $workers"
    print_info "Log Level: $log_level"
    print_info "Reload: $reload"
    
    # Check if port is available
    if ! port_available $port; then
        print_error "Port $port is already in use"
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start server based on environment
    if [ "$ENVIRONMENT" = "development" ] || [ "$reload" = "true" ]; then
        print_info "Starting development server with auto-reload..."
        uvicorn main:app \
            --host $host \
            --port $port \
            --reload \
            --log-level $log_level \
            --access-log
    else
        print_info "Starting production server with Gunicorn..."
        gunicorn main:app \
            -w $workers \
            -k uvicorn.workers.UvicornWorker \
            --bind $host:$port \
            --log-level $log_level \
            --access-logfile - \
            --error-logfile - \
            --preload
    fi
}

# Function to display help
show_help() {
    echo "OneVice Backend Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start                 Start the server (default)"
    echo "  check                 Check configuration and dependencies"
    echo "  install               Install dependencies only"
    echo "  test                  Run test suite only"
    echo "  init-db               Initialize database schema only"
    echo "  help                  Show this help message"
    echo ""
    echo "Options:"
    echo "  --host HOST           Server host (default: $DEFAULT_HOST)"
    echo "  --port PORT           Server port (default: $DEFAULT_PORT)"
    echo "  --workers WORKERS     Number of workers (default: $DEFAULT_WORKERS)"
    echo "  --log-level LEVEL     Log level (default: $DEFAULT_LOG_LEVEL)"
    echo "  --reload              Enable auto-reload (development mode)"
    echo "  --skip-checks         Skip dependency and database checks"
    echo "  --skip-tests          Skip test execution"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL          PostgreSQL connection string (required)"
    echo "  NEO4J_URI             Neo4j connection URI"
    echo "  REDIS_URL             Redis connection string"
    echo "  JWT_SECRET_KEY        JWT signing secret (required)"
    echo "  CLERK_SECRET_KEY      Clerk API secret key"
    echo "  ENVIRONMENT           Environment (development/production)"
    echo ""
    echo "Examples:"
    echo "  $0                              # Start server with defaults"
    echo "  $0 --host 127.0.0.1 --port 8080  # Custom host and port"
    echo "  $0 --reload                     # Development mode with auto-reload"
    echo "  $0 check                        # Check configuration only"
    echo "  $0 test                         # Run tests only"
}

# Parse command line arguments
COMMAND="start"
SKIP_CHECKS=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            export HOST="$2"
            shift 2
            ;;
        --port)
            export PORT="$2"
            shift 2
            ;;
        --workers)
            export WORKERS="$2"
            shift 2
            ;;
        --log-level)
            export LOG_LEVEL="$2"
            shift 2
            ;;
        --reload)
            export RELOAD=true
            shift
            ;;
        --skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        start|check|install|test|init-db|help)
            COMMAND="$1"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_success "OneVice Backend Startup Script"
    print_info "Command: $COMMAND"
    echo ""
    
    case $COMMAND in
        check)
            check_environment
            check_dependencies
            check_databases
            print_success "Configuration check completed"
            ;;
        install)
            check_dependencies
            install_dependencies
            print_success "Dependencies installation completed"
            ;;
        test)
            check_dependencies
            install_dependencies
            run_tests
            ;;
        init-db)
            check_environment
            check_dependencies
            install_dependencies
            init_database
            ;;
        start)
            if [ "$SKIP_CHECKS" = false ]; then
                check_environment
                check_dependencies
                install_dependencies
                check_databases
                init_database
            fi
            
            if [ "$SKIP_TESTS" = false ] && [ "$ENVIRONMENT" != "production" ]; then
                run_tests
            fi
            
            start_server
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main