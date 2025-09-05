# API-003: Add Backward Compatibility Layer

## Objective
Implement a compatibility layer that maintains all existing API endpoints while internally routing them through the new unified system. This ensures zero downtime during migration and allows gradual adoption of the new API patterns.

## Acceptance Criteria
- [ ] All existing API endpoints continue to work unchanged
- [ ] Internal routing to unified state and action services
- [ ] Performance parity with current direct service calls
- [ ] Comprehensive logging for migration tracking
- [ ] Feature flag system to enable/disable unified backend
- [ ] Zero breaking changes to existing tests
- [ ] Migration metrics and monitoring

## Implementation Details

### Compatibility Layer Architecture
```python
# backend/compatibility/legacy_router.py
class LegacyAPIRouter:
    def __init__(self, state_service, action_dispatcher):
        self.state_service = state_service
        self.action_dispatcher = action_dispatcher
        self.feature_flags = FeatureFlags()
    
    async def route_legacy_request(self, endpoint, method, params):
        """Route legacy API calls through new system"""
        if self.feature_flags.use_unified_backend:
            return await self._route_through_unified(endpoint, method, params)
        else:
            return await self._route_through_legacy(endpoint, method, params)
```

### Endpoint Mapping Strategy
```python
# Map legacy endpoints to unified actions
ENDPOINT_MAPPINGS = {
    'POST /run/start': {
        'action': 'start_run',
        'param_transform': lambda data: {
            'party': data.get('party', ['player']),
            'damage_type': data.get('damage_type', ''),
            'pressure': data.get('pressure', 0)
        }
    },
    'POST /run/{run_id}/next': {
        'action': 'advance_room',
        'param_transform': lambda data: {}
    },
    'GET /map/{run_id}': {
        'state_selector': lambda state: {
            'map': state['game_state']['run']['map'],
            'party': state['game_state']['party'],
            'current_state': state['game_state']['run']['current_state']
        }
    }
    # ... mapping for all existing endpoints
}
```

### Response Format Translation
```python
async def translate_unified_to_legacy(self, unified_response, legacy_format):
    """Convert unified response back to expected legacy format"""
    if legacy_format == 'map_response':
        return {
            'map': unified_response['game_state']['run']['map'],
            'party': unified_response['game_state']['party'],
            'current_state': unified_response['game_state']['run']['current_state']
        }
    elif legacy_format == 'action_response':
        return {
            'success': unified_response['success'],
            'result': unified_response['result'],
            'error': unified_response.get('errors', [])
        }
    # ... other format translations
```

## Testing Requirements

### Compatibility Tests
- [ ] Run full existing test suite with compatibility layer enabled
- [ ] Test all legacy endpoints produce identical responses
- [ ] Performance benchmarks comparing legacy vs unified routing
- [ ] Test concurrent access through both API styles

### Migration Tests
- [ ] Test feature flag switching between legacy and unified
- [ ] Test gradual migration scenarios
- [ ] Test rollback procedures
- [ ] Test mixed usage patterns (some clients using new, some old API)

### Integration Tests
- [ ] Test with existing frontend code unchanged
- [ ] Test with existing automated scripts and tools
- [ ] Test Docker Compose setup with compatibility layer

## Dependencies
- **API-001**: Requires unified state service
- **API-002**: Requires unified action dispatcher
- All existing service layer code

## Risk Assessment

### Potential Issues
1. **Performance overhead**: Additional routing layer
   - *Mitigation*: Implement direct passthrough for hot paths, profile carefully
2. **Response format mismatches**: Subtle differences in unified vs legacy responses
   - *Mitigation*: Comprehensive response comparison testing
3. **Transaction boundaries**: Legacy endpoints may have different transaction expectations
   - *Mitigation*: Maintain original transaction patterns in compatibility layer

### Rollback Plan
- Feature flag allows instant rollback to pure legacy mode
- Compatibility layer can be disabled per-endpoint basis
- No changes to underlying legacy service code

## Estimated Effort
**Large** (5-7 days)
- Endpoint mapping and routing: 3 days
- Response format translation: 2 days
- Testing and performance optimization: 2 days

## Implementation Phases

### Phase 1: Core Routing Infrastructure
```python
# Implement basic routing framework
@app.route('/legacy/<path:legacy_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def route_legacy_endpoint(legacy_path):
    router = LegacyAPIRouter(state_service, action_dispatcher)
    return await router.handle_request(legacy_path, request.method, await request.get_json())
```

### Phase 2: Endpoint-by-Endpoint Migration
- Start with simple endpoints (GET /players, GET /gacha)
- Add complex endpoints (battle actions, room actions)
- Test each endpoint thoroughly before moving to next

### Phase 3: Feature Flag Integration
```python
# Environment-based feature flags
FEATURE_FLAGS = {
    'unified_backend': os.getenv('AF_USE_UNIFIED_BACKEND', 'false').lower() == 'true',
    'unified_endpoints': os.getenv('AF_UNIFIED_ENDPOINTS', '').split(','),
    'legacy_fallback': os.getenv('AF_LEGACY_FALLBACK', 'true').lower() == 'true'
}
```

### Phase 4: Monitoring and Metrics
```python
# Track migration progress
class MigrationMetrics:
    def track_endpoint_usage(self, endpoint, method, backend_type):
        # Log which backend was used for analytics
        
    def track_performance(self, endpoint, response_time, backend_type):
        # Compare performance between legacy and unified
        
    def track_errors(self, endpoint, error_type, backend_type):
        # Monitor for compatibility issues
```

## Feature Flag Configuration

### Environment Variables
```bash
# Enable unified backend for specific endpoints
AF_USE_UNIFIED_BACKEND=true
AF_UNIFIED_ENDPOINTS=/ui,/ui/action,/players
AF_LEGACY_FALLBACK=true

# Migration monitoring
AF_LOG_BACKEND_USAGE=true
AF_MIGRATION_METRICS=true
```

### Runtime Configuration
```python
# Runtime feature flag updates
@app.route('/admin/feature-flags', methods=['POST'])
async def update_feature_flags():
    # Allow runtime toggling for gradual migration
```

## Success Metrics
- 100% of existing tests pass with compatibility layer
- Performance within 10% of direct legacy calls
- Zero user-facing breaking changes during migration
- Smooth gradual migration path to unified API

## Migration Checklist
- [ ] Map all existing endpoints to unified actions/state
- [ ] Implement response format translations
- [ ] Add comprehensive compatibility tests
- [ ] Implement feature flag system
- [ ] Add migration monitoring and metrics
- [ ] Test with all existing client code
- [ ] Document migration procedures
- [ ] Create rollback procedures