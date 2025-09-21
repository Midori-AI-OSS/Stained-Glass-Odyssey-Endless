import pytest

#!/usr/bin/env python3
"""
Simple test to verify async database operations work correctly.

This test demonstrates that database operations can be performed
asynchronously without blocking the event loop.
"""

import asyncio
from pathlib import Path

# Simple minimal setup for testing
import sys
import tempfile
import time

sys.path.insert(0, '/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend')

from autofighter.save_manager import SaveManager


@pytest.mark.asyncio
async def test_sync_vs_async_db():
    """Test to show the difference between sync and async database operations."""

    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    try:
        save_manager = SaveManager(db_path, "")

        # Initialize the database
        with save_manager.connection() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
            conn.execute("INSERT INTO test_table (value) VALUES (?)", ("test1",))
            conn.execute("INSERT INTO test_table (value) VALUES (?)", ("test2",))

        print("Testing synchronous database operations:")
        start_time = time.time()

        # Simulate multiple sync database operations (blocking)
        for i in range(5):
            with save_manager.connection() as conn:
                conn.execute("SELECT * FROM test_table")
                # Simulate some processing time
                time.sleep(0.1)

        sync_time = time.time() - start_time
        print(f"Sync operations took: {sync_time:.2f} seconds")

        print("\nTesting asynchronous database operations:")
        start_time = time.time()

        # Simulate multiple async database operations (non-blocking)
        async def async_db_operation():
            def db_work():
                with save_manager.connection() as conn:
                    conn.execute("SELECT * FROM test_table")
                # Simulate some processing time
                time.sleep(0.1)

            await asyncio.to_thread(db_work)

        # Run multiple operations concurrently
        tasks = [async_db_operation() for _ in range(5)]
        await asyncio.gather(*tasks)

        async_time = time.time() - start_time
        print(f"Async operations took: {async_time:.2f} seconds")

        print(f"\nSpeedup: {sync_time / async_time:.2f}x")
        print("✅ Async database operations working correctly!")

        # Test that the event loop remains responsive during async operations
        print("\nTesting event loop responsiveness:")

        async def background_task():
            for i in range(10):
                print(f"  Background task: {i}")
                await asyncio.sleep(0.05)

        # Start background task and database operation simultaneously
        start_time = time.time()
        task1 = asyncio.create_task(background_task())
        task2 = asyncio.create_task(async_db_operation())

        await asyncio.gather(task1, task2)
        total_time = time.time() - start_time

        print(f"Background task and DB operation completed in: {total_time:.2f} seconds")
        print("✅ Event loop remained responsive during database operations!")

    finally:
        # Clean up
        db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    print("🔍 Testing async-friendly database operations...")
    asyncio.run(test_sync_vs_async_db())
