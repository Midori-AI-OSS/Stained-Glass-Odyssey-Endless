"""
Async database utilities for improved event loop compatibility.

This module provides helper functions to wrap database operations
in asyncio.to_thread() calls, preventing blocking of the event loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any
from typing import TypeVar

from autofighter.save_manager import SaveManager

T = TypeVar("T")


async def async_db_operation(
    save_manager: SaveManager, operation: Callable[[Any], T]
) -> T:
    """
    Execute a database operation asynchronously.

    Args:
        save_manager: The SaveManager instance
        operation: A callable that takes a database connection and returns a result

    Returns:
        The result of the operation
    """

    def db_wrapper():
        with save_manager.connection() as conn:
            return operation(conn)

    return await asyncio.to_thread(db_wrapper)


async def async_query(
    save_manager: SaveManager, query: str, params: tuple | None = None
) -> list[tuple]:
    """
    Execute a SELECT query asynchronously.

    Args:
        save_manager: The SaveManager instance
        query: SQL query string
        params: Optional query parameters

    Returns:
        List of result tuples
    """

    def execute_query(conn):
        if params:
            return conn.execute(query, params).fetchall()
        return conn.execute(query).fetchall()

    return await async_db_operation(save_manager, execute_query)


async def async_execute(
    save_manager: SaveManager, query: str, params: tuple | None = None
) -> int:
    """
    Execute an INSERT/UPDATE/DELETE query asynchronously.

    Args:
        save_manager: The SaveManager instance
        query: SQL query string
        params: Optional query parameters

    Returns:
        Number of affected rows
    """

    def execute_query(conn):
        if params:
            return conn.execute(query, params).rowcount
        return conn.execute(query).rowcount

    return await async_db_operation(save_manager, execute_query)


# Example usage patterns:
#
# # Instead of:
# with get_save_manager().connection() as conn:
#     cur = conn.execute("SELECT id FROM owned_players")
#     owned = {row[0] for row in cur.fetchall()}
#
# # Use:
# rows = await async_query(get_save_manager(), "SELECT id FROM owned_players")
# owned = {row[0] for row in rows}
#
# # Instead of:
# with get_save_manager().connection() as conn:
#     conn.execute("INSERT INTO runs (id, party) VALUES (?, ?)", (run_id, data))
#
# # Use:
# await async_execute(get_save_manager(), "INSERT INTO runs (id, party) VALUES (?, ?)", (run_id, data))
