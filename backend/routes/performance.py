"""
Event bus performance monitoring endpoint.
Provides real-time metrics about event bus performance and health.
"""
import time
import tracemalloc

from quart import Blueprint
from quart import jsonify
from runs.lifecycle import cleanup_battle_state
from runs.lifecycle import get_battle_state_sizes

from autofighter.stats import BUS

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None

perf_bp = Blueprint('performance', __name__)


@perf_bp.route('/metrics', methods=['GET'])
async def get_event_bus_metrics():
    """Get event bus performance metrics."""
    try:
        metrics = BUS.get_performance_metrics()

        # Add system health indicators
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'event_bus_active': True
        }

        # Check for concerning performance patterns
        slow_events = []
        total_events = 0
        total_errors = 0

        for event, stats in metrics.items():
            total_events += stats['count']
            total_errors += stats['errors']

            # Flag events that are consistently slow
            if stats['avg_time'] > 0.016:  # >16ms average
                slow_events.append({
                    'event': event,
                    'avg_time_ms': stats['avg_time'] * 1000,
                    'max_time_ms': stats['max_time'] * 1000,
                    'count': stats['count']
                })

        if slow_events:
            health_status['status'] = 'degraded'
            health_status['issues'] = slow_events

        if total_errors > total_events * 0.05:  # >5% error rate
            health_status['status'] = 'unhealthy'
            health_status['error_rate'] = total_errors / total_events if total_events > 0 else 0

        state_sizes = get_battle_state_sizes()
        memory: dict[str, int] = {}
        if psutil is not None:
            process = psutil.Process()
            info = process.memory_info()
            memory = {'rss': info.rss, 'vms': info.vms}
        else:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            current, peak = tracemalloc.get_traced_memory()
            memory = {'current': current, 'peak': peak}

        return jsonify({
            'health': health_status,
            'metrics': metrics,
            'summary': {
                'total_events': total_events,
                'total_errors': total_errors,
                'error_rate': total_errors / total_events if total_events > 0 else 0,
                'slow_events_count': len(slow_events)
            },
            'battle_state': state_sizes,
            'memory': memory,
        })

    except Exception as e:
        return jsonify({
            'health': {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
        }), 500


@perf_bp.route('/health', methods=['GET'])
async def get_backend_health():
    """Simple health check endpoint for ping indicator."""
    try:
        # Basic health checks
        health = {
            'status': 'ok',
            'timestamp': time.time(),
            'services': {
                'event_bus': True,
                'stats_system': True,
                'plugin_system': True
            }
        }

        # Quick performance check
        start = time.perf_counter()
        await BUS.emit_async('health_check_ping')  # Emit a test event
        ping_time = (time.perf_counter() - start) * 1000  # Convert to ms

        health['ping_ms'] = ping_time

        # Flag if event bus is slow
        if ping_time > 50:  # >50ms for a simple event is concerning
            health['status'] = 'degraded'
            health['warning'] = f'Event bus slow: {ping_time:.1f}ms'

        return jsonify(health)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500


@perf_bp.route('/metrics/clear', methods=['POST'])
async def clear_metrics():
    """Clear event bus metrics (useful for testing)."""
    try:
        BUS.clear_metrics()
        return jsonify({
            'status': 'ok',
            'message': 'Metrics cleared',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@perf_bp.route('/gc', methods=['POST'])
async def trigger_cleanup():
    """Trigger manual battle state cleanup."""
    await cleanup_battle_state()
    return jsonify({'status': 'ok'})
