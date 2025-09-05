# Task 05: Docker Configuration Update

## Objective
Update the Docker Compose configuration to implement the new 4-service architecture: frontend, router, backend, and database.

## Requirements

### 1. Four-Service Architecture
- **Frontend**: Svelte UI on port 59001
- **Router**: FastAPI gateway on port 59000  
- **Backend**: Quart game logic on port 59002
- **Database**: PostgreSQL with pgAdmin on ports 5432/8080

### 2. Service Communication
- Frontend → Router → Backend
- Backend → Database
- Router ↔ Health checks for all services
- pgAdmin → Database (admin interface)

### 3. Environment Configuration
- Service discovery via Docker network
- Environment-based configuration
- Volume management for data persistence
- Development and production variants

## Implementation Tasks

### Task 5.1: Main Docker Compose Configuration
**File**: `compose.yaml` (Replace existing)
```yaml
version: '3.8'

# Midori AutoFighter - 4-Service Architecture
# Frontend → Router → Backend → Database

services:
  # ============================================================================
  # DATABASE SERVICE - PostgreSQL with pgAdmin
  # ============================================================================
  database:
    image: postgres:15-alpine
    container_name: autofighter-database
    restart: unless-stopped
    environment:
      POSTGRES_DB: autofighter
      POSTGRES_USER: autofighter
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:-autofighter_dev_password}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=en_US.UTF-8 --lc-ctype=en_US.UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d:ro
    ports:
      - "${DATABASE_PORT:-5432}:5432"
    networks:
      - autofighter-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U autofighter -d autofighter"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  # Database Administration Interface
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: autofighter-pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@autofighter.local}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
      PGADMIN_CONFIG_SERVER_MODE: 'False'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
    volumes:
      - pgadmin_data:/var/lib/pgadmin
      - ./database/pgadmin:/pgadmin4/config:ro
    ports:
      - "${PGADMIN_PORT:-8080}:80"
    networks:
      - autofighter-network
    depends_on:
      database:
        condition: service_healthy
    profiles:
      - admin
      - dev

  # ============================================================================
  # BACKEND SERVICE - Game Logic and Business Rules
  # ============================================================================
  backend:
    build:
      context: ./backend
      dockerfile: ../Dockerfile.python
      args:
        UV_EXTRA: ${UV_EXTRA:-}
    container_name: autofighter-backend
    restart: unless-stopped
    environment:
      # Database connection
      DATABASE_URL: postgresql://autofighter:${DATABASE_PASSWORD:-autofighter_dev_password}@database:5432/autofighter
      AF_DB_KEY: ${AF_DB_KEY:-development-key-not-secure}
      
      # Service configuration
      BACKEND_HOST: 0.0.0.0
      BACKEND_PORT: 59002
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      
      # Feature flags
      UV_EXTRA: ${UV_EXTRA:-}
      ENABLE_LLM: ${ENABLE_LLM:-false}
      
      # Router communication
      ROUTER_HOST: router
      ROUTER_PORT: 59000
    volumes:
      - ./backend:/app:delegated
      - backend_cache:/.cache
    ports:
      - "${BACKEND_PORT:-59002}:59002"
    networks:
      - autofighter-network
    depends_on:
      database:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:59002/health/live')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # ============================================================================
  # ROUTER SERVICE - API Gateway and Service Coordinator
  # ============================================================================
  router:
    build:
      context: ./router
      dockerfile: Dockerfile
    container_name: autofighter-router
    restart: unless-stopped
    environment:
      # Router configuration
      ROUTER_HOST: 0.0.0.0
      ROUTER_PORT: 59000
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      
      # Backend service discovery
      BACKEND_HOST: backend
      BACKEND_PORT: 59002
      BACKEND_TIMEOUT: 30
      
      # Frontend service discovery  
      FRONTEND_HOST: frontend
      FRONTEND_PORT: 59001
      
      # Database service discovery
      DATABASE_HOST: database
      DATABASE_PORT: 5432
    ports:
      - "${ROUTER_PORT:-59000}:59000"
    networks:
      - autofighter-network
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:59000/health/')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # ============================================================================
  # FRONTEND SERVICE - User Interface
  # ============================================================================
  frontend:
    build:
      context: ./frontend
      dockerfile: ../Dockerfile.js
    container_name: autofighter-frontend
    restart: unless-stopped
    environment:
      # Router configuration
      VITE_ROUTER_BASE: http://router:59000
      
      # Development settings
      VITE_DEV_MODE: ${DEV_MODE:-false}
      VITE_LOG_LEVEL: ${LOG_LEVEL:-info}
      
      # Feature flags
      VITE_ENABLE_DEBUG: ${ENABLE_DEBUG:-false}
    volumes:
      - ./frontend:/app:delegated
      - frontend_node_modules:/app/node_modules
    ports:
      - "${FRONTEND_PORT:-59001}:59001"
    networks:
      - autofighter-network
    depends_on:
      router:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:59001/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================
networks:
  autofighter-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# ============================================================================
# VOLUME CONFIGURATION
# ============================================================================
volumes:
  # Database persistence
  postgres_data:
    driver: local
    
  # Admin interface persistence
  pgadmin_data:
    driver: local
    
  # Development caches (performance optimization)
  backend_cache:
    driver: local
  frontend_node_modules:
    driver: local
```

### Task 5.2: Development Override Configuration
**File**: `compose.dev.yaml` (New file)
```yaml
# Development overrides for Docker Compose
# Usage: docker-compose -f compose.yaml -f compose.dev.yaml up

version: '3.8'

services:
  # Development-specific overrides
  database:
    ports:
      - "5432:5432"  # Expose database for local development
    environment:
      POSTGRES_PASSWORD: dev_password_not_secure

  pgadmin:
    ports:
      - "8080:80"
    profiles:
      - dev  # Always include in development

  backend:
    build:
      target: development  # Use development stage in Dockerfile
    environment:
      LOG_LEVEL: DEBUG
      ENABLE_DEBUG: true
      UV_EXTRA: ""  # No LLM for faster development
    volumes:
      - ./backend:/app:delegated
      - backend_dev_cache:/.cache
    command: ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "59002", "--reload"]
    develop:
      watch:
        - action: sync
          path: ./backend
          target: /app
          ignore:
            - __pycache__/
            - .pytest_cache/
            - .venv/

  router:
    build:
      target: development
    environment:
      LOG_LEVEL: DEBUG
    volumes:
      - ./router:/app:delegated
    command: ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "59000", "--reload"]
    develop:
      watch:
        - action: sync
          path: ./router
          target: /app

  frontend:
    build:
      target: development
    environment:
      VITE_DEV_MODE: true
      VITE_ENABLE_DEBUG: true
      VITE_ROUTER_BASE: http://localhost:59000  # For local development
    volumes:
      - ./frontend:/app:delegated
      - frontend_dev_node_modules:/app/node_modules
    command: ["bun", "run", "dev", "--host", "0.0.0.0"]
    develop:
      watch:
        - action: sync
          path: ./frontend/src
          target: /app/src
        - action: sync
          path: ./frontend/static
          target: /app/static

volumes:
  backend_dev_cache:
  frontend_dev_node_modules:
```

### Task 5.3: Production Configuration
**File**: `compose.prod.yaml` (New file)
```yaml
# Production overrides for Docker Compose
# Usage: docker-compose -f compose.yaml -f compose.prod.yaml up

version: '3.8'

services:
  database:
    environment:
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}  # Must be set in production
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  backend:
    build:
      target: production
    environment:
      LOG_LEVEL: WARNING
      ENABLE_DEBUG: false
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3
        window: 120s

  router:
    build:
      target: production
    environment:
      LOG_LEVEL: WARNING
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3

  frontend:
    build:
      target: production
    environment:
      VITE_DEV_MODE: false
      VITE_ENABLE_DEBUG: false
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

# Remove development volumes and use only production-ready configs
volumes:
  postgres_data:
    driver: local
  pgadmin_data:
    driver: local
```

### Task 5.4: LLM Variants Configuration
**File**: `compose.llm.yaml` (New file)
```yaml
# LLM variants for Docker Compose
# Usage: docker-compose -f compose.yaml -f compose.llm.yaml up

version: '3.8'

services:
  # LLM CPU Backend
  backend-llm-cpu:
    extends:
      service: backend
    container_name: autofighter-backend-llm-cpu
    build:
      args:
        UV_EXTRA: llm-cpu
    environment:
      UV_EXTRA: llm-cpu
      ENABLE_LLM: true
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G
    profiles:
      - llm-cpu

  # LLM CUDA Backend  
  backend-llm-cuda:
    extends:
      service: backend
    container_name: autofighter-backend-llm-cuda
    build:
      args:
        UV_EXTRA: llm-cuda
    environment:
      UV_EXTRA: llm-cuda
      ENABLE_LLM: true
    deploy:
      resources:
        limits:
          memory: 6G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    profiles:
      - llm-cuda

  # LLM AMD Backend
  backend-llm-amd:
    extends:
      service: backend
    container_name: autofighter-backend-llm-amd
    build:
      args:
        UV_EXTRA: llm-amd
    environment:
      UV_EXTRA: llm-amd
      ENABLE_LLM: true
    deploy:
      resources:
        limits:
          memory: 6G
    profiles:
      - llm-amd
```

### Task 5.5: Environment Configuration
**File**: `.env.example` (Update existing)
```env
# ============================================================================
# MIDORI AUTOFIGHTER - ENVIRONMENT CONFIGURATION
# ============================================================================

# Database Configuration
DATABASE_PASSWORD=your-secure-database-password
DATABASE_PORT=5432
AF_DB_KEY=your-32-character-encryption-key-here

# Service Ports
FRONTEND_PORT=59001
ROUTER_PORT=59000
BACKEND_PORT=59002
PGADMIN_PORT=8080

# Admin Interface
PGADMIN_EMAIL=admin@autofighter.local
PGADMIN_PASSWORD=your-secure-admin-password

# Feature Configuration
UV_EXTRA=                    # Options: "", "llm-cpu", "llm-cuda", "llm-amd"
ENABLE_LLM=false
ENABLE_DEBUG=false
DEV_MODE=false

# Logging
LOG_LEVEL=INFO               # Options: DEBUG, INFO, WARNING, ERROR

# Development Settings (for compose.dev.yaml)
COMPOSE_PROFILES=dev         # Options: dev, admin, llm-cpu, llm-cuda, llm-amd
```

### Task 5.6: Service Management Scripts
**File**: `scripts/docker-management.sh` (New file)
```bash
#!/bin/bash
# Docker Compose management scripts for Midori AutoFighter

set -e

# Configuration
COMPOSE_FILES="-f compose.yaml"
PROJECT_NAME="midori-autofighter"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker and Docker Compose are available
check_requirements() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available"
        exit 1
    fi
}

# Start services based on profile
start_services() {
    local profile=${1:-dev}
    
    log_info "Starting Midori AutoFighter services with profile: $profile"
    
    case $profile in
        "dev")
            COMPOSE_FILES="$COMPOSE_FILES -f compose.dev.yaml"
            export COMPOSE_PROFILES="dev,admin"
            ;;
        "prod")
            COMPOSE_FILES="$COMPOSE_FILES -f compose.prod.yaml"
            ;;
        "llm-cpu")
            COMPOSE_FILES="$COMPOSE_FILES -f compose.llm.yaml"
            export COMPOSE_PROFILES="llm-cpu"
            ;;
        "llm-cuda")
            COMPOSE_FILES="$COMPOSE_FILES -f compose.llm.yaml"
            export COMPOSE_PROFILES="llm-cuda"
            ;;
        "llm-amd")
            COMPOSE_FILES="$COMPOSE_FILES -f compose.llm.yaml"
            export COMPOSE_PROFILES="llm-amd"
            ;;
        *)
            log_error "Unknown profile: $profile"
            log_info "Available profiles: dev, prod, llm-cpu, llm-cuda, llm-amd"
            exit 1
            ;;
    esac
    
    docker compose $COMPOSE_FILES --project-name $PROJECT_NAME up -d
    log_success "Services started successfully"
    
    # Show service status
    show_status
}

# Stop services
stop_services() {
    log_info "Stopping Midori AutoFighter services..."
    docker compose --project-name $PROJECT_NAME down
    log_success "Services stopped successfully"
}

# Show service status
show_status() {
    log_info "Service Status:"
    docker compose --project-name $PROJECT_NAME ps
    
    echo ""
    log_info "Service URLs:"
    echo "  Frontend:  http://localhost:59001"
    echo "  Router:    http://localhost:59000"
    echo "  Backend:   http://localhost:59002"
    echo "  pgAdmin:   http://localhost:8080"
    echo "  Database:  postgresql://autofighter@localhost:5432/autofighter"
}

# Show logs
show_logs() {
    local service=${1:-}
    
    if [ -z "$service" ]; then
        docker compose --project-name $PROJECT_NAME logs -f
    else
        docker compose --project-name $PROJECT_NAME logs -f "$service"
    fi
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    # Check each service
    services=("frontend" "router" "backend" "database")
    
    for service in "${services[@]}"; do
        if docker compose --project-name $PROJECT_NAME ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
        fi
    done
    
    # Test connectivity
    log_info "Testing service connectivity..."
    
    # Frontend
    if curl -s -f http://localhost:59001/ > /dev/null; then
        log_success "Frontend is responding"
    else
        log_warning "Frontend is not responding"
    fi
    
    # Router
    if curl -s -f http://localhost:59000/health/ > /dev/null; then
        log_success "Router is responding"
    else
        log_warning "Router is not responding"
    fi
    
    # Backend (through router)
    if curl -s -f http://localhost:59000/api/ > /dev/null; then
        log_success "Backend is responding through router"
    else
        log_warning "Backend is not responding through router"
    fi
}

# Reset all data
reset_data() {
    read -p "⚠️  This will delete all game data. Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Stopping services and removing data..."
        docker compose --project-name $PROJECT_NAME down -v
        docker volume rm -f "${PROJECT_NAME}_postgres_data" "${PROJECT_NAME}_pgadmin_data" 2>/dev/null || true
        log_success "All data reset successfully"
    else
        log_info "Reset cancelled"
    fi
}

# Main command dispatcher
case "${1:-help}" in
    "start")
        check_requirements
        start_services "${2:-dev}"
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services "${2:-dev}"
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "health")
        health_check
        ;;
    "reset")
        reset_data
        ;;
    "help"|*)
        echo "Midori AutoFighter Docker Management"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start [profile]  Start services with specified profile (dev, prod, llm-cpu, llm-cuda, llm-amd)"
        echo "  stop             Stop all services"
        echo "  restart [profile] Restart services with specified profile"
        echo "  status           Show service status and URLs"
        echo "  logs [service]   Show logs for all services or specific service"
        echo "  health           Perform health checks on all services"
        echo "  reset            Reset all data (destructive operation)"
        echo "  help             Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start dev                # Start development environment"
        echo "  $0 start prod               # Start production environment"
        echo "  $0 start llm-cuda          # Start with CUDA LLM support"
        echo "  $0 logs backend            # Show backend logs"
        echo "  $0 health                  # Check all services"
        ;;
esac
```

### Task 5.7: Validation Script
**File**: `scripts/validate_docker_setup.py`
```python
#!/usr/bin/env python3
"""Validate Docker Compose setup for Midori AutoFighter"""

import subprocess
import time
import requests
import json
import sys
from pathlib import Path

def run_command(cmd, capture_output=True, timeout=30):
    """Run a shell command with error handling"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)

def check_docker_setup():
    """Check if Docker and Docker Compose are properly set up"""
    print("🐳 Checking Docker setup...")
    
    # Check Docker
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print(f"    ❌ Docker not available: {stderr}")
        return False
    print(f"    ✓ Docker: {stdout.strip()}")
    
    # Check Docker Compose
    success, stdout, stderr = run_command("docker compose version")
    if not success:
        print(f"    ❌ Docker Compose not available: {stderr}")
        return False
    print(f"    ✓ Docker Compose: {stdout.strip()}")
    
    return True

def check_compose_files():
    """Check if all required compose files exist"""
    print("📄 Checking Compose files...")
    
    required_files = [
        "compose.yaml",
        "compose.dev.yaml", 
        "compose.prod.yaml",
        "compose.llm.yaml"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"    ✓ {file} exists")
        else:
            print(f"    ❌ {file} missing")
            return False
    
    return True

def validate_compose_syntax():
    """Validate Docker Compose file syntax"""
    print("🔍 Validating Compose syntax...")
    
    configs = [
        ("compose.yaml", ""),
        ("compose.yaml -f compose.dev.yaml", "development"),
        ("compose.yaml -f compose.prod.yaml", "production"),
        ("compose.yaml -f compose.llm.yaml", "LLM")
    ]
    
    for compose_files, description in configs:
        cmd = f"docker compose -f {compose_files} config"
        success, stdout, stderr = run_command(cmd)
        
        if success:
            print(f"    ✓ {description or 'base'} configuration valid")
        else:
            print(f"    ❌ {description or 'base'} configuration invalid: {stderr}")
            return False
    
    return True

def test_service_startup():
    """Test that services can start up"""
    print("🚀 Testing service startup...")
    
    # Start services
    cmd = "docker compose -f compose.yaml -f compose.dev.yaml up -d"
    success, stdout, stderr = run_command(cmd, timeout=120)
    
    if not success:
        print(f"    ❌ Failed to start services: {stderr}")
        return False
    
    print("    ✓ Services started successfully")
    
    # Wait for services to be ready
    print("    ⏳ Waiting for services to be ready...")
    time.sleep(30)
    
    # Check service health
    services_healthy = True
    
    # Check database
    cmd = "docker compose exec -T database pg_isready -U autofighter"
    success, stdout, stderr = run_command(cmd, timeout=10)
    if success:
        print("    ✓ Database is ready")
    else:
        print("    ❌ Database is not ready")
        services_healthy = False
    
    # Check backend through router
    try:
        response = requests.get("http://localhost:59000/api/", timeout=10)
        if response.status_code == 200:
            print("    ✓ Backend is responding through router")
        else:
            print(f"    ❌ Backend not responding: HTTP {response.status_code}")
            services_healthy = False
    except Exception as e:
        print(f"    ❌ Backend not reachable: {e}")
        services_healthy = False
    
    # Check router health
    try:
        response = requests.get("http://localhost:59000/health/", timeout=10)
        if response.status_code == 200:
            print("    ✓ Router health check passed")
        else:
            print(f"    ❌ Router health check failed: HTTP {response.status_code}")
            services_healthy = False
    except Exception as e:
        print(f"    ❌ Router health check failed: {e}")
        services_healthy = False
    
    # Check frontend
    try:
        response = requests.get("http://localhost:59001/", timeout=10)
        if response.status_code == 200:
            print("    ✓ Frontend is responding")
        else:
            print(f"    ❌ Frontend not responding: HTTP {response.status_code}")
            services_healthy = False
    except Exception as e:
        print(f"    ❌ Frontend not reachable: {e}")
        services_healthy = False
    
    return services_healthy

def cleanup_test_environment():
    """Clean up test environment"""
    print("🧹 Cleaning up test environment...")
    
    cmd = "docker compose down -v"
    success, stdout, stderr = run_command(cmd, timeout=60)
    
    if success:
        print("    ✓ Test environment cleaned up")
    else:
        print(f"    ⚠️  Cleanup may have failed: {stderr}")

def main():
    """Main validation function"""
    print("🔍 Validating Docker setup for Midori AutoFighter...")
    print("=" * 60)
    
    validation_steps = [
        ("Docker setup", check_docker_setup),
        ("Compose files", check_compose_files), 
        ("Compose syntax", validate_compose_syntax),
        ("Service startup", test_service_startup)
    ]
    
    all_passed = True
    
    for step_name, step_func in validation_steps:
        try:
            if not step_func():
                all_passed = False
                break
        except Exception as e:
            print(f"    ❌ {step_name} validation failed with exception: {e}")
            all_passed = False
            break
    
    # Always try to cleanup
    try:
        cleanup_test_environment()
    except Exception as e:
        print(f"    ⚠️  Cleanup failed: {e}")
    
    print("=" * 60)
    if all_passed:
        print("✅ Docker setup validation passed!")
        return True
    else:
        print("❌ Docker setup validation failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## Testing Commands

```bash
# Make scripts executable
chmod +x scripts/docker-management.sh
chmod +x scripts/validate_docker_setup.py

# Validate Docker setup
python scripts/validate_docker_setup.py

# Start development environment
./scripts/docker-management.sh start dev

# Check status
./scripts/docker-management.sh status

# View logs
./scripts/docker-management.sh logs

# Health check
./scripts/docker-management.sh health

# Stop services
./scripts/docker-management.sh stop
```

## Completion Criteria

- [ ] All Docker Compose configurations created and validated
- [ ] Four services start successfully in correct order
- [ ] Service-to-service communication working
- [ ] Health checks pass for all services
- [ ] Environment configuration properly implemented
- [ ] Management scripts working correctly
- [ ] Validation script passes all tests
- [ ] Database persistence maintained across restarts
- [ ] LLM variants available via profiles

## Notes for Task Master Review

- Four-service architecture provides clear separation of concerns
- Health checks enable monitoring and automated recovery
- Multiple configuration variants support different deployment scenarios
- Management scripts simplify operations for developers and operations teams
- Volume management ensures data persistence and performance optimization

**Next Task**: After completion and review, proceed to `task-06-testing-validation.md`