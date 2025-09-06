# Task 5A: Docker Services Configuration

## Overview

This task creates individual Docker configurations for each service using the pixelarch base image with uv package management and volume mounting for development, following the project's standards.

## Goals

- Create Docker configurations for all services (router, backend, frontend, database)
- Use pixelarch base image with uv package management
- Implement volume mounting for development workflow
- Add proper environment variable configuration
- Ensure consistent build and deployment patterns

## Prerequisites

- All service implementations (router, backend, frontend) completed
- Database setup and migration scripts ready
- Docker and Docker Compose available

## Implementation

### Step 1: Router Service Docker Configuration

**File**: `router/Dockerfile`
```dockerfile
FROM lunamidori5/pixelarch:quartz

# Set service-specific OS release info
RUN sudo sed -i 's/Quartz/Router-Service/g' /etc/os-release

# Install system dependencies
RUN yay -Syu --noconfirm && yay -Yccc --noconfirm

# Install uv if not already available
RUN yay -S --noconfirm uv && yay -Yccc --noconfirm

# Environment configuration
ENV PYTHONOPTIMIZE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONPATH="/app"
ENV PATH="/root/.local/bin:${PATH}"

# UV cache directory
ENV UV_CACHE_DIR="/.cache"

# Create app directory
WORKDIR /app

# Setup directories and permissions
RUN sudo chown -R $(whoami):$(whoami) /app
RUN sudo mkdir -p ${UV_CACHE_DIR} && sudo chown -R $(whoami):$(whoami) ${UV_CACHE_DIR} && sudo chmod -R 755 ${UV_CACHE_DIR}
RUN sudo mkdir -p /.venv && sudo chown -R $(whoami):$(whoami) /.venv && sudo chmod -R 755 /.venv

# Expose port
EXPOSE 59000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:59000/health || exit 1

# Entry point script will handle dependency installation and service start
CMD ["bash", "-lc", "cd /app && uv sync --frozen && exec uv run uvicorn app:app --host 0.0.0.0 --port 59000"]
```

**File**: `router/docker-entrypoint.sh`
```bash
#!/bin/bash
set -e

echo "=== Router Service Startup ==="
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "UV version: $(uv --version)"

# Install dependencies
echo "Installing dependencies with uv..."
uv sync --frozen

# Start the service
echo "Starting router service on port 59000..."
exec uv run uvicorn app:app --host 0.0.0.0 --port 59000 --reload
```

**File**: `router/.dockerignore`
```
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
*.log
.env
.venv/
node_modules/
.git/
.gitignore
README.md
```

### Step 2: Backend Service Docker Configuration

**File**: `backend/Dockerfile`
```dockerfile
FROM lunamidori5/pixelarch:quartz

# Set service-specific OS release info
RUN sudo sed -i 's/Quartz/Backend-Service/g' /etc/os-release

# Install system dependencies
RUN yay -Syu --noconfirm && yay -Yccc --noconfirm

# Install uv if not already available
RUN yay -S --noconfirm uv && yay -Yccc --noconfirm

# Environment configuration
ENV PYTHONOPTIMIZE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONPATH="/app"
ENV PATH="/root/.local/bin:${PATH}"

# UV cache directory
ENV UV_CACHE_DIR="/.cache"

# Database configuration
ENV DATABASE_HOST=database
ENV DATABASE_PORT=5432
ENV DATABASE_NAME=autofighter
ENV DATABASE_USER=autofighter
ENV DATABASE_PASSWORD=password

# Backend configuration
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=59002

# Create app directory
WORKDIR /app

# Setup directories and permissions
RUN sudo chown -R $(whoami):$(whoami) /app
RUN sudo mkdir -p ${UV_CACHE_DIR} && sudo chown -R $(whoami):$(whoami) ${UV_CACHE_DIR} && sudo chmod -R 755 ${UV_CACHE_DIR}
RUN sudo mkdir -p /.venv && sudo chown -R $(whoami):$(whoami) /.venv && sudo chmod -R 755 /.venv

# Expose port
EXPOSE 59002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:59002/health || exit 1

# Entry point script will handle dependency installation and service start
CMD ["bash", "-lc", "cd /app && uv sync --frozen && exec uv run python app.py"]
```

**File**: `backend/docker-entrypoint.sh`
```bash
#!/bin/bash
set -e

echo "=== Backend Service Startup ==="
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "UV version: $(uv --version)"

# Wait for database to be ready
echo "Waiting for database to be ready..."
until PGPASSWORD=$DATABASE_PASSWORD psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -c '\q'; do
  echo "Database is unavailable - sleeping..."
  sleep 2
done
echo "Database is ready!"

# Install dependencies
echo "Installing dependencies with uv..."
uv sync --frozen

# Start the service
echo "Starting backend service on port 59002..."
exec uv run python app.py
```

**File**: `backend/.dockerignore`
```
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
*.log
.env
.venv/
save.db
save.db-*
migrations/
tests/
node_modules/
.git/
.gitignore
README.md
dist/
build/
```

### Step 3: Frontend Service Docker Configuration

**File**: `frontend/Dockerfile`
```dockerfile
FROM lunamidori5/pixelarch:quartz

# Set service-specific OS release info
RUN sudo sed -i 's/Quartz/Frontend-Service/g' /etc/os-release

# Install system dependencies
RUN yay -Syu --noconfirm && yay -Yccc --noconfirm

# Install Node.js and bun
RUN yay -S --noconfirm nodejs npm && yay -Yccc --noconfirm
RUN curl -fsSL https://bun.sh/install | bash

# Environment configuration
ENV NODE_ENV=development
ENV PATH="/root/.bun/bin:${PATH}"

# Frontend configuration
ENV FRONTEND_HOST=0.0.0.0
ENV FRONTEND_PORT=59001
ENV ROUTER_URL=http://router:59000

# Create app directory
WORKDIR /app

# Setup directories and permissions
RUN sudo chown -R $(whoami):$(whoami) /app

# Expose port
EXPOSE 59001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:59001 || exit 1

# Entry point script will handle dependency installation and service start
CMD ["bash", "-lc", "cd /app && bun install && exec bun run dev --host 0.0.0.0 --port 59001"]
```

**File**: `frontend/docker-entrypoint.sh`
```bash
#!/bin/bash
set -e

echo "=== Frontend Service Startup ==="
echo "Working directory: $(pwd)"
echo "Node version: $(node --version)"
echo "Bun version: $(bun --version)"

# Install dependencies
echo "Installing dependencies with bun..."
bun install

# Build for production if needed
if [ "$NODE_ENV" = "production" ]; then
    echo "Building frontend for production..."
    bun run build
    exec bun run preview --host 0.0.0.0 --port 59001
else
    echo "Starting frontend development server on port 59001..."
    exec bun run dev --host 0.0.0.0 --port 59001
fi
```

**File**: `frontend/.dockerignore`
```
node_modules/
.svelte-kit/
build/
.env
.env.*
!.env.example
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.git/
.gitignore
README.md
```

### Step 4: Database Service Configuration

**File**: `database/Dockerfile`
```dockerfile
FROM postgres:15-alpine

# Install pgAdmin dependencies
RUN apk add --no-cache python3 py3-pip

# Set environment variables
ENV POSTGRES_DB=autofighter
ENV POSTGRES_USER=autofighter  
ENV POSTGRES_PASSWORD=password
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Create directories for initialization scripts
COPY init/ /docker-entrypoint-initdb.d/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1

# Expose PostgreSQL port
EXPOSE 5432
```

**File**: `database/init/001_schema.sql`
```sql
-- PostgreSQL schema for AutoFighter
-- This will be executed when the database container starts

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Runs table
CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE,
    party JSONB NOT NULL DEFAULT '{}',
    map JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Owned players table
CREATE TABLE IF NOT EXISTS owned_players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE,
    player_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gacha items table
CREATE TABLE IF NOT EXISTS gacha_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE,
    item_id TEXT NOT NULL,
    type TEXT NOT NULL,
    star_level INTEGER NOT NULL DEFAULT 1,
    obtained_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gacha rolls table
CREATE TABLE IF NOT EXISTS gacha_rolls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE,
    player_id TEXT NOT NULL DEFAULT 'player',
    items JSONB NOT NULL DEFAULT '[]',
    rolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Upgrade points table
CREATE TABLE IF NOT EXISTS upgrade_points (
    player_id TEXT PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 0,
    hp INTEGER NOT NULL DEFAULT 0,
    atk INTEGER NOT NULL DEFAULT 0,
    def INTEGER NOT NULL DEFAULT 0,
    crit_rate INTEGER NOT NULL DEFAULT 0,
    crit_damage INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Damage types table (if needed)
CREATE TABLE IF NOT EXISTS damage_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id TEXT UNIQUE,
    type TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_runs_legacy_id ON runs(legacy_id);
CREATE INDEX IF NOT EXISTS idx_runs_updated_at ON runs(updated_at);
CREATE INDEX IF NOT EXISTS idx_owned_players_legacy_id ON owned_players(legacy_id);
CREATE INDEX IF NOT EXISTS idx_gacha_items_item_id ON gacha_items(item_id);
CREATE INDEX IF NOT EXISTS idx_gacha_items_obtained_at ON gacha_items(obtained_at);
CREATE INDEX IF NOT EXISTS idx_gacha_rolls_player_id ON gacha_rolls(player_id);
CREATE INDEX IF NOT EXISTS idx_gacha_rolls_rolled_at ON gacha_rolls(rolled_at);

-- Insert sample data for testing
INSERT INTO owned_players (legacy_id, player_data) VALUES 
    ('starter_warrior', '{"name": "Starter Warrior", "class": "warrior", "level": 1}'),
    ('starter_mage', '{"name": "Starter Mage", "class": "mage", "level": 1}')
ON CONFLICT (legacy_id) DO NOTHING;

-- Grant permissions (if needed for specific users)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO autofighter;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO autofighter;

-- Update function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_runs_updated_at 
    BEFORE UPDATE ON runs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_upgrade_points_updated_at 
    BEFORE UPDATE ON upgrade_points 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'AutoFighter database schema initialized successfully';
END $$;
```

### Step 5: pgAdmin Service Configuration

**File**: `pgadmin/Dockerfile`
```dockerfile
FROM dpage/pgadmin4:7

# Custom configuration
ENV PGADMIN_DEFAULT_EMAIL=admin@autofighter.local
ENV PGADMIN_DEFAULT_PASSWORD=admin
ENV PGADMIN_LISTEN_PORT=38085

# Copy server configuration
COPY servers.json /pgadmin4/servers.json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:38085 || exit 1

# Expose pgAdmin port
EXPOSE 38085
```

**File**: `pgadmin/servers.json`
```json
{
    "Servers": {
        "1": {
            "Name": "AutoFighter Database",
            "Group": "Servers",
            "Host": "database",
            "Port": 5432,
            "MaintenanceDB": "autofighter",
            "Username": "autofighter",
            "Password": "password",
            "SSLMode": "prefer",
            "Comment": "AutoFighter PostgreSQL Database"
        }
    }
}
```

### Step 6: Build Scripts

**File**: `scripts/build-services.sh`
```bash
#!/bin/bash
set -e

echo "=== Building AutoFighter Services ==="

# Function to build service
build_service() {
    local service=$1
    local context=$2
    
    echo "Building $service service..."
    docker build -t "autofighter-$service:latest" "$context"
    echo "✅ Built $service service"
}

# Build router service
build_service "router" "router/"

# Build backend service  
build_service "backend" "backend/"

# Build frontend service
build_service "frontend" "frontend/"

# Build database service
build_service "database" "database/"

# Build pgAdmin service
build_service "pgadmin" "pgadmin/"

echo "🎉 All services built successfully!"

# Show built images
echo ""
echo "Built images:"
docker images | grep autofighter
```

**File**: `scripts/clean-services.sh`
```bash
#!/bin/bash
set -e

echo "=== Cleaning AutoFighter Services ==="

# Stop and remove containers
echo "Stopping containers..."
docker-compose down --remove-orphans

# Remove images
echo "Removing images..."
docker rmi $(docker images "autofighter-*" -q) 2>/dev/null || echo "No AutoFighter images to remove"

# Remove volumes (optional)
read -p "Remove persistent volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing volumes..."
    docker volume rm $(docker volume ls -q | grep autofighter) 2>/dev/null || echo "No AutoFighter volumes to remove"
fi

# Clean up dangling images and containers
echo "Cleaning up Docker system..."
docker system prune -f

echo "✅ Cleanup complete!"
```

**File**: `scripts/dev-setup.sh`
```bash
#!/bin/bash
set -e

echo "=== AutoFighter Development Setup ==="

# Check dependencies
echo "Checking dependencies..."
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Create necessary directories
echo "Creating directories..."
mkdir -p database/data
mkdir -p pgadmin/data
mkdir -p logs

# Set permissions
echo "Setting permissions..."
chmod +x scripts/*.sh
chmod +x */docker-entrypoint.sh 2>/dev/null || true

# Build services
echo "Building services..."
./scripts/build-services.sh

# Create development environment file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Database Configuration
POSTGRES_DB=autofighter
POSTGRES_USER=autofighter
POSTGRES_PASSWORD=password
DATABASE_HOST=database
DATABASE_PORT=5432

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@autofighter.local
PGADMIN_DEFAULT_PASSWORD=admin
PGADMIN_LISTEN_PORT=38085

# Service Ports
ROUTER_PORT=59000
BACKEND_PORT=59002
FRONTEND_PORT=59001
DATABASE_PORT=5432
PGADMIN_PORT=38085

# Environment
NODE_ENV=development
DEBUG=true
EOF
    echo "✅ Created .env file"
fi

echo ""
echo "🎉 Development setup complete!"
echo ""
echo "To start services:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f [service-name]"
echo ""
echo "Services will be available at:"
echo "  Frontend:  http://localhost:59001"
echo "  Router:    http://localhost:59000"
echo "  Backend:   http://localhost:59002"
echo "  pgAdmin:   http://localhost:38085"
echo "  Database:  localhost:5432"
```

## Validation Criteria

### Success Criteria
1. **Docker Images**: All services build successfully using pixelarch base
2. **Volume Mounting**: Source code is mounted for development workflow
3. **Environment Variables**: Proper configuration through environment variables
4. **Health Checks**: All services have working health checks
5. **Dependencies**: Services install dependencies correctly at runtime

### Validation Commands
```bash
# Setup development environment
chmod +x scripts/*.sh
./scripts/dev-setup.sh

# Build all services
./scripts/build-services.sh

# Test individual service builds
docker build -t test-router router/
docker build -t test-backend backend/
docker build -t test-frontend frontend/

# Check images
docker images | grep autofighter
```

### Expected Results
- All Docker images build without errors
- Services use pixelarch base image correctly
- UV package management works in containers
- Health checks respond appropriately
- Volume mounting preserves development workflow
- Environment variables are properly configured

## Notes

- All services use pixelarch:quartz base image as specified
- UV package management used for Python services
- Bun package manager used for frontend service
- Volume mounting enables live development without rebuilds
- Health checks ensure service availability
- PostgreSQL and pgAdmin configured with proper networking
- Build scripts automate the development setup process