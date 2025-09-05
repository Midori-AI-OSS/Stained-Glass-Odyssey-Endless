# DOCKER-001: Optimize Communication for Docker Compose Environment

## Objective
Optimize the backend/frontend communication specifically for Docker Compose deployment where both services run together reliably. This includes simplifying service discovery, optimizing networking, and eliminating unnecessary complexity designed for distributed deployments.

## Acceptance Criteria
- [ ] Simplified service discovery optimized for Docker Compose networking
- [ ] Reduced network latency between frontend and backend containers
- [ ] Elimination of complex backend discovery mechanisms
- [ ] Docker Compose networking best practices implemented
- [ ] Health check integration for container orchestration
- [ ] Optimized for local development and production Docker deployments
- [ ] Connection pooling and keepalive optimization for container communication

## Implementation Details

### Current Complex Discovery Pattern:
```javascript
// COMPLEX: Multiple fallback discovery mechanisms
async function getApiBase() {
    if (cached) return cached;
    
    const envBase = import.meta.env && import.meta.env.VITE_API_BASE;
    if (envBase) {
        cached = envBase;
        return cached;
    }
    
    if (browser) {
        try {
            const res = await fetch('/api-base', { cache: 'no-store' });
            cached = await res.text();
            return cached;
        } catch {
            // fall through to default
        }
    }
    
    cached = 'http://localhost:59002';
    return cached;
}
```

### Simplified Docker-Optimized Discovery:
```javascript
// SIMPLE: Docker Compose optimized discovery
function getApiBase() {
    // In Docker Compose, backend is always available at predictable location
    const dockerHost = 'http://backend:59002';
    const devHost = 'http://localhost:59002';
    
    // Use Docker host if available, fall back to dev
    return process.env.NODE_ENV === 'production' ? dockerHost : devHost;
}
```

### Docker Compose Configuration Optimization:
```yaml
# compose.yaml optimizations
version: '3.8'
services:
  backend:
    build: 
      context: .
      dockerfile: Dockerfile.python
    ports:
      - "59002:59002"
    networks:
      - autofighter
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:59002/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    environment:
      - AF_DOCKER_MODE=true
      - AF_INTERNAL_HOST=0.0.0.0
      - AF_CORS_ORIGINS=http://frontend:59001,http://localhost:59001

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.js
    ports:
      - "59001:59001"
    networks:
      - autofighter
    environment:
      - VITE_API_BASE=http://backend:59002
      - NODE_ENV=production
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:59001"]
      interval: 15s
      timeout: 5s
      retries: 3

networks:
  autofighter:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Backend Network Optimization:
```python
# backend/app.py - Docker-optimized configuration
@app.before_serving
async def configure_for_docker():
    if os.getenv('AF_DOCKER_MODE'):
        # Optimize for container networking
        app.config['CORS_ORIGINS'] = os.getenv('AF_CORS_ORIGINS', '').split(',')
        app.config['KEEPALIVE_TIMEOUT'] = 75  # Longer keepalive for containers
        app.config['WORKER_CONNECTIONS'] = 200  # Optimized for Docker
        
        # Pre-warm services for faster response
        await warm_up_services()

async def warm_up_services():
    """Pre-initialize services for faster first response"""
    try:
        # Initialize database connections
        get_save_manager()
        # Pre-load static data
        await load_player_catalog()
        await load_card_catalog()
        logger.info("Services pre-warmed for Docker environment")
    except Exception as e:
        logger.warning(f"Service warm-up failed: {e}")
```

### Frontend Network Optimization:
```javascript
// frontend/src/lib/api.js - Docker-optimized networking
const API_CONFIG = {
    // Longer timeouts for container networking
    timeout: 10000,
    // Connection keepalive for container communication
    keepAlive: true,
    // Retry strategy optimized for containers
    retries: 3,
    retryDelay: 1000
};

class DockerOptimizedClient {
    constructor() {
        this.baseURL = this.getBaseURL();
        this.httpClient = this.createHttpClient();
    }
    
    getBaseURL() {
        // Simple, Docker-first approach
        if (typeof window !== 'undefined') {
            // Browser environment
            return import.meta.env.VITE_API_BASE || 'http://localhost:59002';
        } else {
            // SSR environment (if applicable)
            return process.env.VITE_API_BASE || 'http://backend:59002';
        }
    }
    
    createHttpClient() {
        // Optimized fetch wrapper for container networking
        return {
            async request(url, options = {}) {
                const fullURL = `${this.baseURL}${url}`;
                const config = {
                    ...API_CONFIG,
                    ...options,
                    headers: {
                        'Keep-Alive': 'timeout=60, max=100',
                        'Connection': 'keep-alive',
                        ...options.headers
                    }
                };
                
                return await this.fetchWithRetry(fullURL, config);
            }
        };
    }
}
```

## Testing Requirements

### Docker Compose Tests
- [ ] Test service startup and discovery in Docker environment
- [ ] Test network communication performance between containers
- [ ] Test health checks and dependency management
- [ ] Test production-like deployment scenarios

### Network Performance Tests
- [ ] Measure request latency within Docker network
- [ ] Test connection pooling and keepalive effectiveness
- [ ] Compare performance vs. complex discovery mechanisms
- [ ] Test concurrent request handling in containers

### Reliability Tests
- [ ] Test container restart scenarios
- [ ] Test network partition recovery
- [ ] Test backend/frontend startup order dependencies
- [ ] Test resource constraints and scaling

## Dependencies
- **CLIENT-001**: Benefits from simplified API client
- **API-003**: Backward compatibility helps during Docker optimization
- Current Docker Compose setup and container configuration

## Risk Assessment

### Potential Issues
1. **Service discovery failures**: Simplified discovery might be too rigid
   - *Mitigation*: Retain localhost fallback for development, add health checks
2. **Network performance**: Container networking overhead
   - *Mitigation*: Optimize networking stack, use Docker networking best practices
3. **Development vs production differences**: Different configs for different environments
   - *Mitigation*: Environment-specific configuration, comprehensive testing

### Rollback Plan
- Can revert to complex discovery mechanisms if needed
- Docker Compose changes are non-breaking and reversible
- Network optimizations can be disabled via environment variables

## Estimated Effort
**Small** (2-3 days)
- Docker Compose optimization: 1 day
- Network and discovery simplification: 1 day
- Testing and documentation: 1 day

## Implementation Strategy

### Phase 1: Docker Compose Optimization
```yaml
# Update compose.yaml for optimal networking
services:
  backend:
    # Add health checks
    # Optimize networking configuration
    # Add Docker-specific environment variables
  
  frontend:
    # Add backend dependency with health check
    # Configure API base for Docker networking
    # Add health checks
```

### Phase 2: Simplified Service Discovery
```javascript
// Replace complex discovery with Docker-optimized approach
export function getApiBase() {
    // Docker Compose: backend service always available at 'backend:59002'
    // Development: localhost fallback
    const dockerBackend = 'http://backend:59002';
    const localBackend = 'http://localhost:59002';
    
    // Use environment variable or detect container environment
    return import.meta.env.VITE_API_BASE || 
           (isDockerEnvironment() ? dockerBackend : localBackend);
}

function isDockerEnvironment() {
    // Simple detection: check if running in container
    return import.meta.env.MODE === 'production' || 
           typeof window !== 'undefined' && window.location.hostname !== 'localhost';
}
```

### Phase 3: Network Performance Optimization
```python
# Backend optimizations for container networking
from quart import Quart
from hypercorn.config import Config

app = Quart(__name__)

if os.getenv('AF_DOCKER_MODE'):
    # Container-optimized configuration
    app.config.update({
        'KEEPALIVE_TIMEOUT': 75,
        'WORKER_CONNECTIONS': 200,
        'WORKER_CLASS': 'uvloop',  # Faster event loop
        'PRELOAD_APP': True,       # Pre-load for faster startup
    })
```

### Phase 4: Health Check Integration
```python
# Enhanced health check for Docker orchestration
@app.route('/api/health')
async def docker_health_check():
    """Comprehensive health check for Docker containers"""
    checks = {
        'database': await check_database_connection(),
        'services': await check_service_availability(),
        'memory': check_memory_usage(),
        'dependencies': await check_external_dependencies()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': time.time()
    }), status_code
```

## Docker Compose Best Practices

### Networking:
- Use custom bridge network for service isolation
- Set explicit subnet for predictable IP allocation
- Use service names for internal communication
- Expose minimal ports to host

### Dependencies:
- Use health checks for service readiness
- Configure proper startup dependencies
- Implement graceful shutdown handling
- Add restart policies for reliability

### Environment:
- Use environment variables for configuration
- Separate development and production configs
- Implement proper secrets management
- Add resource limits and monitoring

## Success Metrics
- 50%+ reduction in service discovery complexity
- Improved container startup time and reliability
- Reduced network latency between frontend and backend
- Simplified development and deployment experience
- Robust health checking and dependency management

## Documentation Updates
- [ ] Update Docker Compose setup documentation
- [ ] Document environment variable configuration
- [ ] Add container networking troubleshooting guide
- [ ] Create production deployment checklist