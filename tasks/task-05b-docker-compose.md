# Task 5B: Docker Compose Orchestration

## Overview

This task creates a comprehensive Docker Compose configuration that orchestrates all services (frontend, router, backend, database, pgAdmin) with proper networking, dependencies, and volume management.

## Goals

- Create Docker Compose configuration for all services
- Set up proper service dependencies and startup order
- Configure networking between services
- Implement volume management for data persistence and development
- Add environment-based configuration

## Prerequisites

- Task 5A (Docker Services Configuration) must be completed
- All individual service Dockerfiles created
- Development environment setup scripts ready

## Implementation

### Step 1: Main Docker Compose Configuration

**File**: `compose.yaml`
```yaml
version: '3.8'

# Define named volumes for data persistence
volumes:
  postgres_data:
    driver: local
  pgadmin_data:
    driver: local

# Define custom network for service communication
networks:
  autofighter_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  # PostgreSQL Database Service
  database:
    build:
      context: ./database
      dockerfile: Dockerfile
    container_name: autofighter_database
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-autofighter}
      POSTGRES_USER: ${POSTGRES_USER:-autofighter}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d:ro
    ports:
      - "${DATABASE_PORT:-5432}:5432"
    networks:
      autofighter_network:
        ipv4_address: 172.20.0.10
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-autofighter} -d ${POSTGRES_DB:-autofighter}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # pgAdmin Web Interface
  pgadmin:
    build:
      context: ./pgadmin
      dockerfile: Dockerfile
    container_name: autofighter_pgadmin
    restart: unless-stopped
    depends_on:
      database:
        condition: service_healthy
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL:-admin@autofighter.local}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD:-admin}
      PGADMIN_LISTEN_PORT: ${PGADMIN_LISTEN_PORT:-38085}
      PGADMIN_CONFIG_SERVER_MODE: 'False'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
    volumes:
      - pgadmin_data:/var/lib/pgadmin
      - ./pgadmin/servers.json:/pgadmin4/servers.json:ro
    ports:
      - "${PGADMIN_PORT:-38085}:38085"
    networks:
      autofighter_network:
        ipv4_address: 172.20.0.11
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:38085"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Backend Service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: autofighter_backend
    restart: unless-stopped
    depends_on:
      database:
        condition: service_healthy
    environment:
      # Database configuration
      DATABASE_HOST: database
      DATABASE_PORT: 5432
      DATABASE_NAME: ${POSTGRES_DB:-autofighter}
      DATABASE_USER: ${POSTGRES_USER:-autofighter}
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD:-password}
      DATABASE_POOL_SIZE: 10
      DATABASE_SSL_MODE: prefer
      
      # Backend configuration
      BACKEND_HOST: 0.0.0.0
      BACKEND_PORT: 59002
      DEBUG: ${DEBUG:-true}
      
      # Python environment
      PYTHONPATH: /app
      PYTHONUNBUFFERED: 1
    volumes:
      # Mount source code for development
      - ./backend:/app:rw
      # Exclude cache and build directories
      - /app/__pycache__
      - /app/.pytest_cache
      - /app/dist
      - /app/build
    ports:
      - "${BACKEND_PORT:-59002}:59002"
    networks:
      autofighter_network:
        ipv4_address: 172.20.0.20
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:59002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Router Service
  router:
    build:
      context: ./router
      dockerfile: Dockerfile
    container_name: autofighter_router
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    environment:
      # Router configuration
      ROUTER_HOST: 0.0.0.0
      ROUTER_PORT: 59000
      
      # Backend service discovery
      BACKEND_HOST: backend
      BACKEND_PORT: 59002
      
      # CORS configuration
      CORS_ORIGINS: http://localhost:59001,http://frontend:59001
      
      # Python environment
      PYTHONPATH: /app
      PYTHONUNBUFFERED: 1
      
      # Debug mode
      DEBUG: ${DEBUG:-true}
    volumes:
      # Mount source code for development
      - ./router:/app:rw
      # Exclude cache directories
      - /app/__pycache__
      - /app/.pytest_cache
    ports:
      - "${ROUTER_PORT:-59000}:59000"
    networks:
      autofighter_network:
        ipv4_address: 172.20.0.30
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:59000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Frontend Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: autofighter_frontend
    restart: unless-stopped
    depends_on:
      router:
        condition: service_healthy
    environment:
      # Frontend configuration
      NODE_ENV: ${NODE_ENV:-development}
      FRONTEND_HOST: 0.0.0.0
      FRONTEND_PORT: 59001
      
      # API configuration
      VITE_ROUTER_URL: http://localhost:59000
      VITE_API_BASE_URL: http://localhost:59000/api
      
      # Development configuration
      VITE_DEV_SERVER_HOST: 0.0.0.0
      VITE_DEV_SERVER_PORT: 59001
    volumes:
      # Mount source code for development
      - ./frontend:/app:rw
      # Exclude node_modules and build directories
      - /app/node_modules
      - /app/.svelte-kit
      - /app/build
    ports:
      - "${FRONTEND_PORT:-59001}:59001"
    networks:
      autofighter_network:
        ipv4_address: 172.20.0.40
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:59001"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Step 2: Development Environment Configuration

**File**: `.env.example`
```bash
# ==============================================
# AutoFighter Docker Compose Configuration
# ==============================================

# Database Configuration
POSTGRES_DB=autofighter
POSTGRES_USER=autofighter
POSTGRES_PASSWORD=password
DATABASE_PORT=5432

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@autofighter.local
PGADMIN_DEFAULT_PASSWORD=admin
PGADMIN_LISTEN_PORT=38085
PGADMIN_PORT=38085

# Service Ports
ROUTER_PORT=59000
BACKEND_PORT=59002
FRONTEND_PORT=59001

# Development Configuration
NODE_ENV=development
DEBUG=true

# Optional: Custom network configuration
# COMPOSE_PROJECT_NAME=autofighter
# COMPOSE_FILE=compose.yaml:compose.override.yaml
```

**File**: `compose.override.yaml`
```yaml
# Development overrides for Docker Compose
# This file is automatically loaded in development

version: '3.8'

services:
  # Development-specific backend configuration
  backend:
    environment:
      DEBUG: "true"
      LOG_LEVEL: DEBUG
    volumes:
      # Additional development volumes
      - ./backend/logs:/app/logs:rw
    command: ["bash", "-lc", "cd /app && uv sync && exec uv run python app.py --reload"]

  # Development-specific router configuration
  router:
    environment:
      DEBUG: "true"
      LOG_LEVEL: DEBUG
    volumes:
      # Additional development volumes
      - ./router/logs:/app/logs:rw
    command: ["bash", "-lc", "cd /app && uv sync && exec uv run uvicorn app:app --host 0.0.0.0 --port 59000 --reload"]

  # Development-specific frontend configuration
  frontend:
    environment:
      NODE_ENV: development
      VITE_DEV_MODE: "true"
    command: ["bash", "-lc", "cd /app && bun install && exec bun run dev --host 0.0.0.0 --port 59001"]

  # Development database with additional logging
  database:
    command: 
      - "postgres"
      - "-c"
      - "log_statement=all"
      - "-c"
      - "log_destination=stderr"
      - "-c"
      - "logging_collector=on"
      - "-c"
      - "log_directory=/var/log/postgresql"
```

### Step 3: Production Environment Configuration

**File**: `compose.prod.yaml`
```yaml
# Production configuration for Docker Compose
# Use with: docker-compose -f compose.yaml -f compose.prod.yaml up

version: '3.8'

services:
  # Production backend configuration
  backend:
    restart: always
    environment:
      DEBUG: "false"
      LOG_LEVEL: INFO
      PYTHONOPTIMIZE: 2
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
    # Remove volume mount in production - use built image
    volumes: []

  # Production router configuration
  router:
    restart: always
    environment:
      DEBUG: "false"
      LOG_LEVEL: INFO
      PYTHONOPTIMIZE: 2
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
    # Remove volume mount in production
    volumes: []

  # Production frontend configuration
  frontend:
    restart: always
    environment:
      NODE_ENV: production
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
    # Build and serve static files
    command: ["bash", "-lc", "cd /app && bun install && bun run build && exec bun run preview --host 0.0.0.0 --port 59001"]
    # Remove volume mount in production
    volumes: []

  # Production database configuration
  database:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    # Optimized PostgreSQL configuration for production
    command:
      - "postgres"
      - "-c"
      - "max_connections=100"
      - "-c"
      - "shared_buffers=256MB"
      - "-c"
      - "effective_cache_size=1GB"
      - "-c"
      - "work_mem=4MB"
      - "-c"
      - "maintenance_work_mem=64MB"

  # Production pgAdmin configuration
  pgadmin:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
```

### Step 4: Service Management Scripts

**File**: `scripts/compose-dev.sh`
```bash
#!/bin/bash
set -e

# Development Docker Compose management script

COMPOSE_FILES="-f compose.yaml"
if [ -f "compose.override.yaml" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f compose.override.yaml"
fi

case "$1" in
    "up")
        echo "Starting AutoFighter development environment..."
        docker-compose $COMPOSE_FILES up -d
        echo ""
        echo "🎉 Services started successfully!"
        echo ""
        echo "Available services:"
        echo "  Frontend:  http://localhost:59001"
        echo "  Router:    http://localhost:59000" 
        echo "  Backend:   http://localhost:59002"
        echo "  pgAdmin:   http://localhost:38085"
        echo "  Database:  localhost:5432"
        echo ""
        echo "To view logs: docker-compose logs -f [service-name]"
        echo "To stop:      ./scripts/compose-dev.sh down"
        ;;
    "down")
        echo "Stopping AutoFighter development environment..."
        docker-compose $COMPOSE_FILES down
        echo "✅ Services stopped"
        ;;
    "restart")
        echo "Restarting AutoFighter development environment..."
        docker-compose $COMPOSE_FILES restart
        echo "✅ Services restarted"
        ;;
    "logs")
        if [ -z "$2" ]; then
            docker-compose $COMPOSE_FILES logs -f
        else
            docker-compose $COMPOSE_FILES logs -f "$2"
        fi
        ;;
    "status")
        docker-compose $COMPOSE_FILES ps
        ;;
    "shell")
        if [ -z "$2" ]; then
            echo "Usage: $0 shell <service-name>"
            echo "Available services: frontend, router, backend, database, pgadmin"
            exit 1
        fi
        docker-compose $COMPOSE_FILES exec "$2" /bin/bash
        ;;
    "build")
        echo "Building AutoFighter services..."
        docker-compose $COMPOSE_FILES build --parallel
        echo "✅ Build complete"
        ;;
    "clean")
        echo "Cleaning up AutoFighter environment..."
        docker-compose $COMPOSE_FILES down -v --remove-orphans
        docker-compose $COMPOSE_FILES rm -f
        echo "✅ Cleanup complete"
        ;;
    *)
        echo "AutoFighter Development Environment Manager"
        echo ""
        echo "Usage: $0 {up|down|restart|logs|status|shell|build|clean}"
        echo ""
        echo "Commands:"
        echo "  up       - Start all services"
        echo "  down     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - View logs (optionally specify service)"
        echo "  status   - Show service status"
        echo "  shell    - Open shell in service container"
        echo "  build    - Build all services"
        echo "  clean    - Stop and remove all containers and volumes"
        echo ""
        echo "Examples:"
        echo "  $0 up"
        echo "  $0 logs backend"
        echo "  $0 shell frontend"
        exit 1
        ;;
esac
```

**File**: `scripts/compose-prod.sh`
```bash
#!/bin/bash
set -e

# Production Docker Compose management script

COMPOSE_FILES="-f compose.yaml -f compose.prod.yaml"

case "$1" in
    "up")
        echo "Starting AutoFighter production environment..."
        docker-compose $COMPOSE_FILES up -d
        echo "✅ Production services started"
        ;;
    "down")
        echo "Stopping AutoFighter production environment..."
        docker-compose $COMPOSE_FILES down
        echo "✅ Production services stopped"
        ;;
    "deploy")
        echo "Deploying AutoFighter to production..."
        
        # Build services
        echo "Building services..."
        docker-compose $COMPOSE_FILES build --parallel
        
        # Stop existing services
        echo "Stopping existing services..."
        docker-compose $COMPOSE_FILES down
        
        # Start new services
        echo "Starting updated services..."
        docker-compose $COMPOSE_FILES up -d
        
        echo "🚀 Deployment complete!"
        ;;
    "status")
        docker-compose $COMPOSE_FILES ps
        ;;
    "logs")
        if [ -z "$2" ]; then
            docker-compose $COMPOSE_FILES logs --tail=100
        else
            docker-compose $COMPOSE_FILES logs --tail=100 "$2"
        fi
        ;;
    *)
        echo "AutoFighter Production Environment Manager"
        echo ""
        echo "Usage: $0 {up|down|deploy|status|logs}"
        echo ""
        echo "Commands:"
        echo "  up       - Start production services"
        echo "  down     - Stop production services"
        echo "  deploy   - Full production deployment"
        echo "  status   - Show service status"
        echo "  logs     - View recent logs"
        exit 1
        ;;
esac
```

### Step 5: Health Check and Monitoring

**File**: `scripts/health-check.sh`
```bash
#!/bin/bash
set -e

echo "=== AutoFighter Services Health Check ==="
echo ""

# Service endpoints
declare -A services=(
    ["Frontend"]="http://localhost:59001"
    ["Router"]="http://localhost:59000/health"
    ["Backend"]="http://localhost:59002/health"
    ["pgAdmin"]="http://localhost:38085"
)

# Database check
echo "🔍 Checking Database..."
if docker-compose exec -T database pg_isready -U autofighter -d autofighter >/dev/null 2>&1; then
    echo "  ✅ Database is ready"
else
    echo "  ❌ Database is not ready"
fi

echo ""

# HTTP services check
for service in "${!services[@]}"; do
    url=${services[$service]}
    echo "🔍 Checking $service..."
    
    if curl -f -s "$url" >/dev/null 2>&1; then
        echo "  ✅ $service is healthy ($url)"
    else
        echo "  ❌ $service is not responding ($url)"
    fi
done

echo ""

# Container status
echo "📊 Container Status:"
docker-compose ps

echo ""

# Resource usage
echo "💾 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose ps -q) 2>/dev/null || echo "Unable to get resource stats"

echo ""
echo "Health check complete!"
```

## Validation Criteria

### Success Criteria
1. **Service Orchestration**: All services start in proper dependency order
2. **Network Communication**: Services can communicate through custom network
3. **Volume Management**: Data persistence and development volumes work correctly
4. **Health Checks**: All services pass health checks
5. **Environment Configuration**: Different environments (dev/prod) work properly

### Validation Commands
```bash
# Setup and start development environment
chmod +x scripts/*.sh
./scripts/compose-dev.sh build
./scripts/compose-dev.sh up

# Check service health
./scripts/health-check.sh

# View service logs
./scripts/compose-dev.sh logs

# Test individual services
curl http://localhost:59001      # Frontend
curl http://localhost:59000/health  # Router
curl http://localhost:59002/health  # Backend
curl http://localhost:38085      # pgAdmin

# Test database connection
docker-compose exec database psql -U autofighter -d autofighter -c '\l'
```

### Expected Results
- All services start successfully in dependency order
- Health checks pass for all services
- Frontend can communicate with router
- Router can communicate with backend
- Backend can communicate with database
- pgAdmin can connect to database
- Volume mounting preserves development workflow
- Services can be stopped and restarted cleanly

## Notes

- Custom network enables reliable service-to-service communication
- Volume mounting supports both development and data persistence
- Health checks ensure services are ready before dependent services start
- Environment-specific configurations support different deployment scenarios
- Resource limits prevent services from consuming excessive resources
- Logging configuration prevents log files from growing too large