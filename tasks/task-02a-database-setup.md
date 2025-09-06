# Task 2A: Database Container Setup

## Overview

This task sets up PostgreSQL and pgAdmin containers as replacements for the embedded SQLite database, providing web-based database administration and better scalability.

## Goals

- Deploy PostgreSQL 15+ container with persistent storage
- Deploy pgAdmin web interface on port 38085
- Configure database authentication and networking
- Create initial database schema structure

## Prerequisites

- Docker and Docker Compose available
- Understanding of database concepts

## Implementation

### Step 1: PostgreSQL Container Configuration

**File**: `database/docker-compose.yml`
```yaml
version: '3.8'

services:
  postgresql:
    image: postgres:15-alpine
    container_name: autofighter-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: autofighter
      POSTGRES_USER: autofighter_user
      POSTGRES_PASSWORD: autofighter_pass
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d
    networks:
      - autofighter-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U autofighter_user -d autofighter"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: autofighter-pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@autofighter.local
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: 'False'
    ports:
      - "38085:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
      - ./pgadmin/servers.json:/pgadmin4/servers.json
    networks:
      - autofighter-network
    depends_on:
      postgresql:
        condition: service_healthy

volumes:
  postgres_data:
    name: autofighter_postgres_data
  pgadmin_data:
    name: autofighter_pgadmin_data

networks:
  autofighter-network:
    name: autofighter-network
    driver: bridge
```

### Step 2: Database Initialization Scripts

**File**: `database/init/01-create-schema.sql`
```sql
-- Midori AutoFighter Database Schema
-- PostgreSQL version of the original SQLite schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Game characters table
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    health INTEGER NOT NULL DEFAULT 100,
    attack INTEGER NOT NULL DEFAULT 10,
    defense INTEGER NOT NULL DEFAULT 5,
    speed INTEGER NOT NULL DEFAULT 10,
    special_abilities JSONB DEFAULT '[]',
    equipment JSONB DEFAULT '{}',
    level INTEGER NOT NULL DEFAULT 1,
    experience INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Battle history table
CREATE TABLE battles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    opponent_character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    winner_id UUID REFERENCES characters(id) ON DELETE SET NULL,
    battle_log JSONB NOT NULL,
    duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Game settings table
CREATE TABLE game_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Player profiles table
CREATE TABLE player_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    preferences JSONB DEFAULT '{}',
    statistics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_characters_name ON characters(name);
CREATE INDEX idx_characters_level ON characters(level);
CREATE INDEX idx_battles_created_at ON battles(created_at);
CREATE INDEX idx_battles_player_character ON battles(player_character_id);
CREATE INDEX idx_game_settings_key ON game_settings(setting_key);
CREATE INDEX idx_player_profiles_username ON player_profiles(username);

-- Create trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_characters_updated_at 
    BEFORE UPDATE ON characters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_settings_updated_at 
    BEFORE UPDATE ON game_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_profiles_updated_at 
    BEFORE UPDATE ON player_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**File**: `database/init/02-initial-data.sql`
```sql
-- Insert default game settings
INSERT INTO game_settings (setting_key, setting_value, description) VALUES
('game_version', '"0.1.0"', 'Current game version'),
('max_character_level', '100', 'Maximum character level'),
('default_health', '100', 'Default character health'),
('default_attack', '10', 'Default character attack'),
('default_defense', '5', 'Default character defense'),
('default_speed', '10', 'Default character speed'),
('battle_timeout_seconds', '300', 'Maximum battle duration'),
('enable_auto_save', 'true', 'Enable automatic game saving');

-- Insert sample characters for testing
INSERT INTO characters (name, health, attack, defense, speed, special_abilities, level) VALUES
('Warrior', 120, 15, 8, 8, '["Power Strike", "Shield Block"]', 1),
('Mage', 80, 20, 3, 12, '["Fireball", "Magic Shield"]', 1),
('Archer', 100, 12, 5, 15, '["Precise Shot", "Quick Draw"]', 1),
('Paladin', 140, 12, 12, 6, '["Divine Protection", "Heal"]', 1);

-- Create default player profile
INSERT INTO player_profiles (username, preferences, statistics) VALUES
('default_player', 
 '{"theme": "dark", "sound_enabled": true, "auto_battle": false}',
 '{"battles_won": 0, "battles_lost": 0, "total_playtime": 0}');
```

### Step 3: pgAdmin Configuration

**File**: `database/pgadmin/servers.json`
```json
{
    "Servers": {
        "1": {
            "Name": "Autofighter Database",
            "Group": "Servers",
            "Host": "postgresql",
            "Port": 5432,
            "MaintenanceDB": "autofighter",
            "Username": "autofighter_user",
            "Password": "autofighter_pass",
            "SSLMode": "prefer",
            "Favorite": true
        }
    }
}
```

### Step 4: Environment Configuration

**File**: `database/.env.example`
```env
# PostgreSQL Configuration
POSTGRES_DB=autofighter
POSTGRES_USER=autofighter_user
POSTGRES_PASSWORD=autofighter_pass

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@autofighter.local
PGADMIN_DEFAULT_PASSWORD=admin
PGADMIN_PORT=38085

# Network Configuration
POSTGRES_PORT=5432
POSTGRES_HOST=localhost
```

### Step 5: Management Scripts

**File**: `database/manage.sh`
```bash
#!/bin/bash
set -e

DB_COMPOSE_FILE="docker-compose.yml"

case "$1" in
    start)
        echo "Starting database services..."
        docker-compose -f $DB_COMPOSE_FILE up -d
        echo "Waiting for services to be ready..."
        sleep 10
        echo "Database services started!"
        echo "PostgreSQL: localhost:5432"
        echo "pgAdmin: http://localhost:38085"
        ;;
    stop)
        echo "Stopping database services..."
        docker-compose -f $DB_COMPOSE_FILE down
        echo "Database services stopped!"
        ;;
    restart)
        echo "Restarting database services..."
        docker-compose -f $DB_COMPOSE_FILE restart
        echo "Database services restarted!"
        ;;
    logs)
        docker-compose -f $DB_COMPOSE_FILE logs -f
        ;;
    status)
        docker-compose -f $DB_COMPOSE_FILE ps
        ;;
    backup)
        if [ -z "$2" ]; then
            echo "Usage: $0 backup <filename>"
            exit 1
        fi
        echo "Creating database backup..."
        docker exec autofighter-postgres pg_dump -U autofighter_user autofighter > "$2"
        echo "Backup created: $2"
        ;;
    restore)
        if [ -z "$2" ]; then
            echo "Usage: $0 restore <filename>"
            exit 1
        fi
        echo "Restoring database from backup..."
        docker exec -i autofighter-postgres psql -U autofighter_user -d autofighter < "$2"
        echo "Database restored from: $2"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|backup|restore}"
        echo ""
        echo "Commands:"
        echo "  start   - Start database services"
        echo "  stop    - Stop database services"
        echo "  restart - Restart database services"
        echo "  logs    - Show service logs"
        echo "  status  - Show service status"
        echo "  backup  - Create database backup"
        echo "  restore - Restore from backup"
        exit 1
        ;;
esac
```

### Step 6: Health Check Script

**File**: `database/health-check.py`
```python
#!/usr/bin/env python3
"""Health check script for database services."""
import psycopg2
import requests
import sys
import os
from time import sleep

def check_postgresql():
    """Check PostgreSQL connectivity."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autofighter",
            user="autofighter_user",
            password="autofighter_pass"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"✓ PostgreSQL: Connected - {version[0]}")
        return True
    except Exception as e:
        print(f"✗ PostgreSQL: Failed - {e}")
        return False

def check_pgadmin():
    """Check pgAdmin web interface."""
    try:
        response = requests.get("http://localhost:38085", timeout=10)
        if response.status_code == 200:
            print("✓ pgAdmin: Web interface accessible")
            return True
        else:
            print(f"✗ pgAdmin: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ pgAdmin: Failed - {e}")
        return False

def check_database_schema():
    """Check if database schema is properly created."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autofighter",
            user="autofighter_user",
            password="autofighter_pass"
        )
        cursor = conn.cursor()
        
        # Check if main tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['characters', 'battles', 'game_settings', 'player_profiles']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"✗ Schema: Missing tables - {missing_tables}")
            return False
        else:
            print(f"✓ Schema: All tables present - {tables}")
            
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Schema: Failed - {e}")
        return False

def main():
    """Run all health checks."""
    print("Database Health Check")
    print("=" * 30)
    
    checks = [
        check_postgresql,
        check_pgadmin,
        check_database_schema
    ]
    
    results = []
    for check in checks:
        results.append(check())
        sleep(1)
    
    print("\nSummary:")
    if all(results):
        print("✓ All database services are healthy!")
        sys.exit(0)
    else:
        print("✗ Some database services have issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Validation

### Step 1: Container Startup

```bash
cd database

# Make scripts executable
chmod +x manage.sh
chmod +x health-check.py

# Start database services
./manage.sh start

# Check status
./manage.sh status
```

### Step 2: Health Checks

```bash
# Install psycopg2 and requests for health check
pip install psycopg2-binary requests

# Run health check
python health-check.py

# Should show all services as healthy
```

### Step 3: Manual Verification

```bash
# Test PostgreSQL connection
psql -h localhost -p 5432 -U autofighter_user -d autofighter

# In psql, run:
# \dt  -- List tables
# SELECT * FROM characters LIMIT 5;
# \q

# Test pgAdmin web interface
# Open http://localhost:38085 in browser
# Login: admin@autofighter.local / admin
```

### Step 4: Data Validation

```bash
# Check sample data exists
psql -h localhost -p 5432 -U autofighter_user -d autofighter -c "SELECT name, level FROM characters;"

# Should show 4 sample characters
```

## Completion Criteria

- [ ] PostgreSQL container running and accessible on port 5432
- [ ] pgAdmin web interface accessible on port 38085
- [ ] Database schema created with all required tables
- [ ] Sample data inserted successfully
- [ ] Health check script passes all tests
- [ ] Management scripts working properly
- [ ] Database authentication configured correctly

## Next Steps

After completing this task, proceed to **Task 2B: Database Migration** to migrate existing SQLite data to PostgreSQL.