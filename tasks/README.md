# Architecture Refactoring Tasks

This directory contains detailed, actionable tasks for implementing the complete architecture refactoring to simplify communication between frontend and backend services.

## Overview

The refactoring implements a 4-service Docker Compose architecture:
1. **Frontend** (Svelte) - User interface on port 59001
2. **Router** (FastAPI) - API gateway and service coordinator on port 59000
3. **Backend** (Quart) - Game logic and business rules on port 59002  
4. **Database** (PostgreSQL) - Data persistence with web admin on port 5432/38085

## Task Execution Order

Tasks are broken down into smaller, manageable phases. Complete sequentially:

### Phase 1: Router Service Foundation (Tasks 1A-1C)
1. `task-01a-router-setup.md` - Basic router service setup and structure (~200 lines)
2. `task-01b-router-api.md` - API implementation and routing logic (~200 lines)  
3. `task-01c-router-integration.md` - Service discovery and health checks (~150 lines)

### Phase 2: Database Migration (Tasks 2A-2C)  
4. `task-02a-database-setup.md` - PostgreSQL container and pgAdmin setup (~250 lines)
5. `task-02b-database-migration.md` - Data migration from SQLite to PostgreSQL (~300 lines)
6. `task-02c-database-integration.md` - Backend PostgreSQL integration (~200 lines)

### Phase 3: Backend Updates (Tasks 3A-3B)
7. `task-03a-backend-database.md` - Replace SaveManager with PostgreSQL (~300 lines)
8. `task-03b-backend-api.md` - Standardize API responses and health checks (~200 lines)

### Phase 4: Frontend Simplification (Tasks 4A-4B)
9. `task-04a-frontend-client.md` - Replace discovery system with router client (~300 lines)
10. `task-04b-frontend-ui.md` - Update UI components for new communication pattern (~200 lines)

### Phase 5: Docker & Testing (Tasks 5A-6B)
11. `task-05a-docker-services.md` - Individual service Docker configurations (~250 lines)
12. `task-05b-docker-compose.md` - Multi-service orchestration setup (~200 lines)  
13. `task-06a-integration-tests.md` - Service communication and API tests (~300 lines)
14. `task-06b-system-validation.md` - End-to-end testing and performance validation (~250 lines)

**Original large tasks preserved as `legacy-task-XX.md` for reference.**

## Task Review Process

After completing each task:
1. Run the provided validation scripts
2. Document any issues or deviations in `task-XX-completion-notes.md`
3. Tag the Task Master for review before proceeding to next task

## Architecture Goals

- **Single Entry Point**: Frontend only communicates with router service
- **Service Isolation**: Clear boundaries between business logic (backend) and coordination (router)
- **Database Accessibility**: Web-based admin interface for database management
- **Simplified Configuration**: Environment-based service discovery
- **Consistent APIs**: Standardized REST patterns and error handling