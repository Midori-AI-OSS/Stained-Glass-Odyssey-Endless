# REAL-TIME-001: Add WebSocket Support for Live Updates

## Objective
Implement WebSocket support to enable real-time state updates between backend and frontend, eliminating the need for polling and providing immediate feedback for live events like battles, notifications, and state changes.

## Acceptance Criteria
- [ ] WebSocket server implementation in backend using Quart/WebSocket
- [ ] WebSocket client integration in frontend unified store
- [ ] Real-time state updates for battle events, room transitions, notifications
- [ ] Graceful fallback to HTTP polling if WebSocket connection fails
- [ ] Connection management (reconnection, heartbeat, error handling)
- [ ] Docker Compose compatible WebSocket networking
- [ ] Performance improvement over polling approach

## Implementation Details

### Backend WebSocket Server:
```python
# backend/websocket/manager.py
from quart import websocket
import asyncio
import json
import logging

class WebSocketManager:
    def __init__(self):
        self.connections = set()
        self.connection_states = {}  # connection_id -> user_state
        
    async def register(self, websocket_conn):
        """Register new WebSocket connection"""
        self.connections.add(websocket_conn)
        connection_id = id(websocket_conn)
        self.connection_states[connection_id] = {
            'connected_at': time.time(),
            'last_ping': time.time(),
            'subscriptions': set()
        }
        
    async def unregister(self, websocket_conn):
        """Clean up WebSocket connection"""
        self.connections.discard(websocket_conn)
        connection_id = id(websocket_conn)
        self.connection_states.pop(connection_id, None)
        
    async def broadcast_state_update(self, state_update):
        """Broadcast state changes to all connected clients"""
        if not self.connections:
            return
            
        message = {
            'type': 'state_update',
            'data': state_update,
            'timestamp': time.time()
        }
        
        # Send to all connected clients
        disconnected = set()
        for conn in self.connections:
            try:
                await conn.send(json.dumps(message))
            except Exception:
                disconnected.add(conn)
                
        # Clean up disconnected clients
        for conn in disconnected:
            await self.unregister(conn)
            
    async def send_to_connection(self, websocket_conn, message):
        """Send message to specific connection"""
        try:
            await websocket_conn.send(json.dumps(message))
        except Exception:
            await self.unregister(websocket_conn)

# Global WebSocket manager instance
ws_manager = WebSocketManager()
```

### WebSocket Routes:
```python
# backend/routes/websocket.py
from quart import Blueprint, websocket
from websocket.manager import ws_manager
from services.state_service import StateService

ws_bp = Blueprint('websocket', __name__)

@ws_bp.websocket('/ws')
async def websocket_endpoint():
    """Main WebSocket endpoint for real-time communication"""
    await ws_manager.register(websocket.websocket)
    
    try:
        # Send initial state
        state_service = StateService()
        initial_state = await state_service.get_complete_state()
        await websocket.websocket.send(json.dumps({
            'type': 'initial_state',
            'data': initial_state
        }))
        
        # Handle incoming messages
        async for message in websocket.websocket:
            try:
                data = json.loads(message)
                await handle_websocket_message(data)
            except json.JSONDecodeError:
                await websocket.websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
                
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
    finally:
        await ws_manager.unregister(websocket.websocket)

async def handle_websocket_message(data):
    """Process incoming WebSocket messages"""
    message_type = data.get('type')
    
    if message_type == 'ping':
        await websocket.websocket.send(json.dumps({'type': 'pong'}))
    elif message_type == 'subscribe':
        # Handle subscription to specific events
        await handle_subscription(data.get('events', []))
    elif message_type == 'action':
        # Handle user actions via WebSocket
        await handle_websocket_action(data)
```

### Frontend WebSocket Client:
```javascript
// frontend/src/lib/websocket.js
class WebSocketClient {
    constructor(apiBase, store) {
        this.apiBase = apiBase;
        this.store = store;
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
    }
    
    connect() {
        const wsUrl = this.apiBase.replace('http', 'ws') + '/ws';
        
        try {
            this.websocket = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.fallbackToPolling();
        }
    }
    
    setupEventHandlers() {
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            this.store.setConnectionStatus('connected');
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        this.websocket.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.stopHeartbeat();
            this.store.setConnectionStatus('disconnected');
            
            if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            } else {
                this.fallbackToPolling();
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.store.setConnectionStatus('error');
        };
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'initial_state':
            case 'state_update':
                this.store.updateState(message.data);
                break;
                
            case 'battle_update':
                this.store.updateBattleState(message.data);
                break;
                
            case 'notification':
                this.store.addNotification(message.data);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.warn('Unknown WebSocket message type:', message.type);
        }
    }
    
    send(message) {
        if (this.websocket?.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, falling back to HTTP');
            this.fallbackToPolling();
        }
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.send({ type: 'ping' });
        }, 30000); // 30 second heartbeat
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        setTimeout(() => {
            console.log(`Attempting WebSocket reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            this.connect();
        }, delay);
    }
    
    fallbackToPolling() {
        console.log('Falling back to HTTP polling');
        this.store.enablePollingFallback();
    }
    
    disconnect() {
        this.stopHeartbeat();
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
}

export default WebSocketClient;
```

### Store Integration:
```javascript
// frontend/src/lib/store.js - WebSocket integration
import WebSocketClient from './websocket.js';

class UnifiedStore {
    constructor() {
        this.state = writable(initialState);
        this.websocketClient = null;
        this.pollingFallback = false;
        this.pollingInterval = null;
    }
    
    async initialize() {
        // Try WebSocket first
        try {
            const apiBase = await getApiBase();
            this.websocketClient = new WebSocketClient(apiBase, this);
            this.websocketClient.connect();
        } catch (error) {
            console.warn('WebSocket initialization failed, using polling:', error);
            this.enablePollingFallback();
        }
    }
    
    updateState(newState) {
        this.state.update(currentState => ({
            ...currentState,
            ...newState,
            last_updated: Date.now()
        }));
    }
    
    updateBattleState(battleData) {
        this.state.update(currentState => ({
            ...currentState,
            live_data: {
                ...currentState.live_data,
                battle_snapshot: battleData
            }
        }));
    }
    
    setConnectionStatus(status) {
        this.state.update(currentState => ({
            ...currentState,
            connection_status: status
        }));
    }
    
    enablePollingFallback() {
        if (this.pollingFallback) return;
        
        this.pollingFallback = true;
        this.pollingInterval = setInterval(async () => {
            try {
                const newState = await api.getState();
                this.updateState(newState);
            } catch (error) {
                console.error('Polling failed:', error);
            }
        }, 2000); // 2 second polling fallback
    }
    
    disablePollingFallback() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.pollingFallback = false;
    }
}
```

## Testing Requirements

### WebSocket Tests
- [ ] Test WebSocket connection establishment and handshake
- [ ] Test real-time state updates and message handling
- [ ] Test reconnection logic and error recovery
- [ ] Test heartbeat mechanism and connection persistence
- [ ] Test concurrent connections and scaling

### Integration Tests
- [ ] Test WebSocket with unified state service
- [ ] Test fallback to HTTP polling when WebSocket fails
- [ ] Test Docker Compose networking with WebSocket
- [ ] Test real-time battle updates and user interactions

### Performance Tests
- [ ] Compare WebSocket vs polling performance
- [ ] Test WebSocket overhead and memory usage
- [ ] Test message throughput and latency
- [ ] Test connection limits and scalability

## Dependencies
- **API-001**: Requires unified state service for state broadcasting
- **STATE-001**: Requires unified frontend store for WebSocket integration
- **DOCKER-001**: Should work with Docker Compose networking

## Risk Assessment

### Potential Issues
1. **Connection reliability**: WebSocket connections can be unstable
   - *Mitigation*: Robust reconnection logic and HTTP polling fallback
2. **Docker networking**: WebSocket proxying through containers
   - *Mitigation*: Test thoroughly in Docker environment, configure proxy correctly
3. **Browser compatibility**: WebSocket support varies
   - *Mitigation*: Feature detection and graceful fallback

### Rollback Plan
- WebSocket is additive feature, can be disabled
- HTTP polling fallback ensures functionality without WebSocket
- Feature flag to enable/disable WebSocket support

## Estimated Effort
**Medium** (4-5 days)
- Backend WebSocket implementation: 2 days
- Frontend WebSocket client: 2 days
- Testing and Docker integration: 1 day

## Docker Compose Integration
```yaml
# Update compose.yaml for WebSocket support
services:
  backend:
    ports:
      - "59002:59002"  # HTTP and WebSocket on same port
    environment:
      - AF_WEBSOCKET_ENABLED=true
      
  frontend:
    environment:
      - VITE_WEBSOCKET_ENABLED=true
```

## Success Metrics
- Real-time state updates with <100ms latency
- Successful WebSocket connection establishment >95% of the time
- Graceful fallback to polling in <1 second on connection failure
- Reduced network traffic compared to continuous polling
- Improved user experience with immediate feedback