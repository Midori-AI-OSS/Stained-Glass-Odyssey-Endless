"""Test torch checker centralized behavior."""

import logging

import pytest


def test_torch_checker_functions():
    """Test torch checker functions work correctly."""
    import llms.torch_checker

    # Test that functions return expected types
    available = llms.torch_checker.is_torch_available()
    assert isinstance(available, bool)

    error = llms.torch_checker.get_torch_import_error()
    assert error is None or isinstance(error, Exception)

    # If torch is not available, error should be set and require_torch should raise
    if not available:
        assert error is not None
        with pytest.raises(RuntimeError, match="LLM dependencies are not installed"):
            llms.torch_checker.require_torch()
    else:
        # If torch is available, require_torch should not raise
        llms.torch_checker.require_torch()  # Should not raise


def test_torch_checker_consistency():
    """Test that torch checker functions return consistent results."""
    import llms.torch_checker

    # Multiple calls should return the same results
    available1 = llms.torch_checker.is_torch_available()
    available2 = llms.torch_checker.is_torch_available()
    assert available1 == available2

    error1 = llms.torch_checker.get_torch_import_error()
    error2 = llms.torch_checker.get_torch_import_error()
    # Errors should be the same (both None or both the same exception)
    if error1 is None:
        assert error2 is None
    else:
        assert str(error1) == str(error2)


def test_torch_checker_logging(caplog):
    """Test that torch checker logs appropriate messages."""
    import sys

    # Remove the module if it was already imported to test fresh import
    if "llms.torch_checker" in sys.modules:
        del sys.modules["llms.torch_checker"]

    with caplog.at_level(logging.INFO):
        import llms.torch_checker  # noqa: F401

    # Should have logged the torch availability status
    log_messages = [record.message for record in caplog.records]
    torch_logs = [
        msg
        for msg in log_messages
        if "Torch" in msg and ("available" in msg or "not available" in msg)
    ]
    assert (
        len(torch_logs) >= 1
    ), f"Expected torch availability log message, got: {log_messages}"
