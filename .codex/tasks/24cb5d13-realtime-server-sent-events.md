# REAL-TIME-002: Implement Server-Sent Events for Live Data

## Objective
Implement Server-Sent Events (SSE) as an alternative to WebSocket for real-time updates, providing better compatibility with proxies and firewalls while maintaining live communication. SSE is simpler than WebSocket and works well for one-way server-to-client updates.

## Acceptance Criteria
- [ ] SSE endpoint implementation in backend for streaming live updates
- [ ] Frontend EventSource integration with automatic reconnection
- [ ] Support for battle updates, notifications, and state changes via SSE
- [ ] Graceful fallback between WebSocket, SSE, and HTTP polling
- [ ] Better proxy/firewall compatibility than WebSocket
- [ ] Docker Compose and production environment compatibility
- [ ] Performance comparable to WebSocket for read-only updates

## Implementation Details

### Backend SSE Implementation:
```python
# backend/routes/sse.py
from quart import Blueprint, Response, request
import asyncio
import json
import time
from services.state_service import StateService
from websocket.manager import ws_manager  # Reuse event broadcasting

sse_bp = Blueprint('sse', __name__)

class SSEManager:
    def __init__(self):
        self.connections = set()
        self.connection_queues = {}  # connection_id -> asyncio.Queue
        
    async def add_connection(self, connection_id, queue):
        """Register new SSE connection"""
        self.connections.add(connection_id)
        self.connection_queues[connection_id] = queue
        
    async def remove_connection(self, connection_id):
        """Remove SSE connection"""
        self.connections.discard(connection_id)
        self.connection_queues.pop(connection_id, None)
        
    async def broadcast_event(self, event_type, data):
        """Broadcast event to all SSE connections"""
        if not self.connection_queues:
            return
            
        message = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        # Add to all connection queues
        disconnected = set()
        for connection_id, queue in self.connection_queues.items():
            try:
                await queue.put(message)
            except Exception:
                disconnected.add(connection_id)
                
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.remove_connection(connection_id)

# Global SSE manager
sse_manager = SSEManager()

@sse_bp.route('/events')
async def event_stream():
    """Server-Sent Events endpoint"""
    connection_id = f"sse_{time.time()}_{id(request)}"
    queue = asyncio.Queue()
    
    async def generate():
        try:
            # Register connection
            await sse_manager.add_connection(connection_id, queue)
            
            # Send initial state
            state_service = StateService()
            initial_state = await state_service.get_complete_state()
            
            yield f"data: {json.dumps({'type': 'initial_state', 'data': initial_state})}\n\n"
            
            # Send heartbeat and queued events
            while True:
                try:
                    # Wait for events with timeout for heartbeat
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                    
        except Exception as e:
            logger.exception(f"SSE connection error: {e}")
        finally:
            await sse_manager.remove_connection(connection_id)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

# Integration with existing event system
async def broadcast_to_sse(event_type, data):
    """Broadcast events to both WebSocket and SSE connections"""
    await sse_manager.broadcast_event(event_type, data)
    # Also broadcast to WebSocket if available
    if hasattr(ws_manager, 'broadcast_state_update'):
        await ws_manager.broadcast_state_update(data)
```

### Frontend SSE Client:
```javascript
// frontend/src/lib/sse.js
class SSEClient {
    constructor(apiBase, store) {
        this.apiBase = apiBase;
        this.store = store;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
    }
    
    connect() {
        const sseUrl = `${this.apiBase}/events`;
        
        try {
            this.eventSource = new EventSource(sseUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('SSE connection failed:', error);
            this.fallbackToPolling();
        }
    }
    
    setupEventHandlers() {
        this.eventSource.onopen = () => {
            console.log('SSE connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.store.setConnectionStatus('connected');
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Failed to parse SSE message:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            this.isConnected = false;
            this.store.setConnectionStatus('error');
            
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            } else {
                this.fallbackToPolling();
            }
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
                
            case 'heartbeat':
                // Connection is alive, no action needed
                break;
                
            default:
                console.warn('Unknown SSE message type:', message.type);
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        setTimeout(() => {
            console.log(`Attempting SSE reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            this.disconnect();
            this.connect();
        }, delay);
    }
    
    fallbackToPolling() {
        console.log('SSE failed, falling back to HTTP polling');
        this.store.enablePollingFallback();
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isConnected = false;
    }
}

export default SSEClient;
```

### Unified Real-Time Client Strategy:
```javascript
// frontend/src/lib/realtime.js
import WebSocketClient from './websocket.js';
import SSEClient from './sse.js';

class RealTimeManager {
    constructor(apiBase, store) {
        this.apiBase = apiBase;
        this.store = store;
        this.currentClient = null;
        this.connectionStrategy = this.determineStrategy();
    }
    
    determineStrategy() {
        // Try WebSocket first, then SSE, then polling
        const strategies = ['websocket', 'sse', 'polling'];
        
        // Check browser support and environment
        if (!window.WebSocket) {
            return strategies.filter(s => s !== 'websocket');
        }
        
        if (!window.EventSource) {
            return strategies.filter(s => s !== 'sse');
        }
        
        return strategies;
    }
    
    async connect() {
        for (const strategy of this.connectionStrategy) {
            try {
                await this.tryStrategy(strategy);
                console.log(`Connected using ${strategy}`);
                return;
            } catch (error) {
                console.warn(`${strategy} connection failed:`, error);
                continue;
            }
        }
        
        console.error('All real-time connection strategies failed');
        this.store.setConnectionStatus('failed');
    }
    
    async tryStrategy(strategy) {
        this.disconnect(); // Clean up previous attempt
        
        switch (strategy) {
            case 'websocket':
                this.currentClient = new WebSocketClient(this.apiBase, this.store);
                this.currentClient.connect();
                break;
                
            case 'sse':
                this.currentClient = new SSEClient(this.apiBase, this.store);
                this.currentClient.connect();
                break;
                
            case 'polling':
                this.store.enablePollingFallback();
                break;
                
            default:
                throw new Error(`Unknown strategy: ${strategy}`);
        }
        
        // Wait a bit to see if connection succeeds
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error(`${strategy} connection timeout`));
            }, 5000);
            
            // Monitor connection status
            const checkInterval = setInterval(() => {
                const status = this.store.getConnectionStatus();
                if (status === 'connected') {
                    clearTimeout(timeout);
                    clearInterval(checkInterval);
                    resolve();
                } else if (status === 'error' || status === 'failed') {
                    clearTimeout(timeout);
                    clearInterval(checkInterval);
                    reject(new Error(`${strategy} connection failed`));
                }
            }, 100);
        });
    }
    
    disconnect() {
        if (this.currentClient && typeof this.currentClient.disconnect === 'function') {
            this.currentClient.disconnect();
        }
        this.currentClient = null;
    }
}

export default RealTimeManager;
```

## Testing Requirements

### SSE-Specific Tests
- [ ] Test SSE connection establishment and event streaming
- [ ] Test SSE reconnection logic and error handling
- [ ] Test proxy and firewall compatibility
- [ ] Test SSE performance vs WebSocket vs polling

### Integration Tests
- [ ] Test fallback strategy (WebSocket → SSE → Polling)
- [ ] Test concurrent real-time connections
- [ ] Test Docker Compose networking with SSE
- [ ] Test production environment compatibility

### Browser Compatibility Tests
- [ ] Test SSE in different browsers and versions
- [ ] Test with various proxy configurations
- [ ] Test with corporate firewalls and security software
- [ ] Test mobile browser compatibility

## Dependencies
- **REAL-TIME-001**: Can work alongside WebSocket as alternative
- **STATE-001**: Requires unified frontend store
- **API-001**: Requires unified state service for event broadcasting

## Risk Assessment

### Potential Issues
1. **Proxy compatibility**: Some proxies may buffer SSE streams
   - *Mitigation*: Configure proper headers, test with common proxy setups
2. **Browser limits**: SSE has connection limits per domain
   - *Mitigation*: Monitor connection usage, implement connection sharing
3. **One-way communication**: SSE is server-to-client only
   - *Mitigation*: Combine with HTTP POST for client-to-server actions

### Rollback Plan
- SSE is additive feature, can be disabled
- WebSocket and HTTP polling remain as fallbacks
- Can prioritize different strategies based on environment

## Estimated Effort
**Small-Medium** (2-3 days)
- Backend SSE implementation: 1 day
- Frontend integration and fallback strategy: 1 day
- Testing and optimization: 1 day

## Implementation Benefits

### Over WebSocket:
- Better proxy and firewall compatibility
- Simpler implementation (no bidirectional complexity)
- Better support in restrictive network environments
- Automatic reconnection built into browser EventSource

### Over HTTP Polling:
- Real-time updates without polling overhead
- Server can push updates immediately
- More efficient bandwidth usage
- Better user experience with immediate feedback

### Combined Strategy:
```javascript
// Optimal connection strategy
const connectionPriority = [
    'websocket',  // Best performance, full bidirectional
    'sse',        // Good performance, better compatibility
    'polling'     // Fallback, works everywhere
];
```

## Docker Compose Configuration:
```yaml
services:
  backend:
    environment:
      - AF_SSE_ENABLED=true
      - AF_SSE_HEARTBEAT_INTERVAL=30
    # SSE uses same HTTP port as regular API
    
  frontend:
    environment:
      - VITE_REALTIME_STRATEGY=auto  # Try WebSocket, then SSE, then polling
```

## Success Metrics
- SSE connection success rate >98% in various network environments
- Real-time updates delivered within 200ms
- Successful fallback between connection types
- Reduced polling traffic when real-time connection active
- Better compatibility in corporate/restricted networks