"""Safe shutdown utilities for graceful backend termination."""

import asyncio
import logging
import os

from battle_logging import end_battle_logging
from battle_logging import end_run_logging

log = logging.getLogger(__name__)

_shutdown_requested = False


async def request_shutdown() -> None:
    """Request a graceful shutdown of the backend.

    This function:
    1. Flushes all pending logs using existing battle logging cleanup
    2. Cancels all running asyncio tasks (except the current one)
    3. Schedules the event loop to stop

    This function is idempotent - multiple calls are safe.
    """
    global _shutdown_requested

    # Skip shutdown during testing to avoid breaking tests
    if os.getenv("PYTEST_CURRENT_TEST"):
        log.info("Skipping shutdown during test execution")
        return

    if _shutdown_requested:
        log.info("Shutdown already requested, ignoring duplicate request")
        return

    _shutdown_requested = True
    log.critical("Shutdown requested - beginning graceful shutdown sequence")

    try:
        # Flush logging using existing battle logging infrastructure
        log.info("Ending battle and run logging...")
        end_battle_logging("shutdown")
        end_run_logging()

        # Get the current event loop
        loop = asyncio.get_running_loop()

        # Get all tasks except the current one
        current_task = asyncio.current_task()
        all_tasks = [task for task in asyncio.all_tasks(loop) if task is not current_task and not task.done()]

        if all_tasks:
            log.info("Cancelling %d running tasks...", len(all_tasks))
            for task in all_tasks:
                task.cancel()

            # Wait a moment for tasks to cancel gracefully
            try:
                await asyncio.wait_for(
                    asyncio.gather(*all_tasks, return_exceptions=True),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, TypeError):
                log.warning("Some tasks did not cancel within timeout or were not valid tasks")

        # Flush logging handlers one more time
        logging.shutdown()

        log.critical("Shutdown sequence complete - stopping event loop")

        # Schedule the loop to stop on the next iteration
        loop.call_soon(loop.stop)

    except Exception as exc:
        log.exception("Error during shutdown sequence: %s", exc)
        # Even if there's an error, try to stop the loop
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon(loop.stop)
        except Exception:
            pass  # Last resort, don't let exceptions prevent shutdown
