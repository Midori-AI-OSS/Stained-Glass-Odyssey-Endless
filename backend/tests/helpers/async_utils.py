from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Generator
from typing import Any, TypeVar

T = TypeVar("T")


class _ImmediateAwaitable(Awaitable[T]):
    def __init__(self, value: T) -> None:
        self._value = value

    def __await__(self) -> Generator[Any, None, T]:
        if False:
            yield
        return self._value


async def call_maybe_async(
    func: Callable[..., T | Awaitable[T]], *args: Any, **kwargs: Any
) -> T:
    """Invoke ``func`` and await the result when necessary."""
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


def ensure_coroutine(result: T | Awaitable[T]) -> Awaitable[T]:
    """Return ``result`` as an awaitable without changing side effects."""
    if inspect.isawaitable(result):
        return result  # type: ignore[return-value]

    return _ImmediateAwaitable(result)
