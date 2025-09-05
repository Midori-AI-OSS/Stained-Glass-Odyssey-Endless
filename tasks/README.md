# Architecture Refactoring Tasks

This directory contains detailed, actionable tasks for implementing the complete architecture refactoring to simplify communication between frontend and backend services.

## Overview

The refactoring implements a 4-service Docker Compose architecture:
1. **Frontend** (Svelte) - User interface on port 59001
2. **Router** (FastAPI) - API gateway and service coordinator on port 59000
3. **Backend** (Quart) - Game logic and business rules on port 59002  
4. **Database** (PostgreSQL) - Data persistence with web admin on port 5432/8080

## Task Execution Order

Tasks must be completed in this specific order to maintain system functionality:

1. `task-01-router-service.md` - Create the router service foundation
2. `task-02-database-migration.md` - Move database to separate container
3. `task-03-backend-updates.md` - Update backend for new architecture
4. `task-04-frontend-simplification.md` - Simplify frontend communication
5. `task-05-docker-configuration.md` - Update Docker Compose setup
6. `task-06-testing-validation.md` - Comprehensive testing and validation

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