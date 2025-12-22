"""Tests for standardized error handling with persistence."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
import json
from pathlib import Path
import uuid

import pytest


class TestErrorModels:
    """Tests for Pydantic error models."""

    def test_error_severity_enum(self):
        """Test ErrorSeverity enum values."""
        from models.errors import ErrorSeverity

        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_error_source_model(self):
        """Test ErrorSource model creation."""
        from models.errors import ErrorSource

        source = ErrorSource(line=42, code="x = 1", highlight=True)
        assert source.line == 42
        assert source.code == "x = 1"
        assert source.highlight is True

        source_default = ErrorSource(line=10, code="y = 2")
        assert source_default.highlight is False

    def test_error_context_model(self):
        """Test ErrorContext model creation."""
        from models.errors import ErrorContext
        from models.errors import ErrorSource

        source_lines = [
            ErrorSource(line=10, code="  x = 1", highlight=False),
            ErrorSource(line=11, code="  y = x + 1", highlight=True),
            ErrorSource(line=12, code="  return y", highlight=False),
        ]

        ctx = ErrorContext(
            file="/path/to/file.py",
            line=11,
            function="my_function",
            source=source_lines,
        )

        assert ctx.file == "/path/to/file.py"
        assert ctx.line == 11
        assert ctx.function == "my_function"
        assert len(ctx.source) == 3
        assert ctx.source[1].highlight is True

    def test_error_response_model(self):
        """Test ErrorResponse model creation with defaults."""
        from models.errors import ErrorResponse
        from models.errors import ErrorSeverity

        error = ErrorResponse(message="Test error occurred")

        assert error.message == "Test error occurred"
        assert error.severity == ErrorSeverity.ERROR
        assert error.id is not None
        assert uuid.UUID(error.id)  # Validates UUID format
        assert error.timestamp is not None
        assert error.traceback is None
        assert error.context is None
        assert error.metadata == {}

    def test_error_response_full(self):
        """Test ErrorResponse with all fields populated."""
        from models.errors import ErrorContext
        from models.errors import ErrorResponse
        from models.errors import ErrorSeverity
        from models.errors import ErrorSource

        error = ErrorResponse(
            severity=ErrorSeverity.CRITICAL,
            message="Critical failure",
            traceback="Traceback (most recent call last):\n  ...",
            context=ErrorContext(
                file="app.py",
                line=100,
                function="main",
                source=[ErrorSource(line=100, code="raise ValueError()", highlight=True)],
            ),
            metadata={"type": "ValueError", "extra": "info"},
        )

        assert error.severity == ErrorSeverity.CRITICAL
        assert error.message == "Critical failure"
        assert "Traceback" in error.traceback
        assert error.context.file == "app.py"
        assert error.metadata["type"] == "ValueError"

    def test_error_response_json_serialization(self):
        """Test ErrorResponse JSON serialization."""
        from models.errors import ErrorResponse
        from models.errors import ErrorSeverity

        error = ErrorResponse(
            severity=ErrorSeverity.WARNING,
            message="Warning message",
        )

        json_data = error.model_dump(mode="json")
        assert json_data["severity"] == "warning"
        assert json_data["message"] == "Warning message"
        assert "timestamp" in json_data
        assert "id" in json_data

    def test_persisted_errors_model(self):
        """Test PersistedErrors model."""
        from models.errors import ErrorResponse
        from models.errors import PersistedErrors

        errors = PersistedErrors()
        assert errors.errors == []
        assert errors.last_crash is None

        error1 = ErrorResponse(message="Error 1")
        error2 = ErrorResponse(message="Error 2")

        errors = PersistedErrors(
            errors=[error1, error2],
            last_crash=datetime.now(timezone.utc),
        )

        assert len(errors.errors) == 2
        assert errors.last_crash is not None

    def test_error_context_from_dict(self):
        """Test error_context_from_dict helper function."""
        from models.errors import error_context_from_dict

        ctx_dict = {
            "file": "/test/file.py",
            "line": 50,
            "function": "test_func",
            "source": [
                {"line": 49, "code": "# comment", "highlight": False},
                {"line": 50, "code": "raise Error()", "highlight": True},
            ],
        }

        ctx = error_context_from_dict(ctx_dict)
        assert ctx is not None
        assert ctx.file == "/test/file.py"
        assert ctx.line == 50
        assert ctx.function == "test_func"
        assert len(ctx.source) == 2
        assert ctx.source[1].highlight is True

        # Test with None input
        assert error_context_from_dict(None) is None

        # Test with empty source
        ctx_empty = error_context_from_dict({"file": "x.py", "line": 1})
        assert ctx_empty.source == []

    def test_create_error_response_helper(self):
        """Test create_error_response helper function."""
        from models.errors import ErrorSeverity
        from models.errors import create_error_response

        error = create_error_response(
            message="Test message",
            traceback_text="Some traceback",
            context={"file": "test.py", "line": 10, "function": "foo"},
            severity=ErrorSeverity.WARNING,
            exc_type="ValueError",
        )

        assert error.message == "Test message"
        assert error.traceback == "Some traceback"
        assert error.context.file == "test.py"
        assert error.severity == ErrorSeverity.WARNING
        assert error.metadata["type"] == "ValueError"


class TestErrorStorage:
    """Tests for error persistence service."""

    @pytest.fixture
    def temp_error_file(self, tmp_path, monkeypatch):
        """Create a temporary error file for testing."""
        error_file = tmp_path / "data" / "errors.json"
        import services.error_storage as storage_module

        monkeypatch.setattr(storage_module, "ERROR_FILE", error_file)
        yield error_file

    def test_persist_and_load_error(self, temp_error_file):
        """Test persisting and loading errors."""
        from models.errors import ErrorResponse
        from services.error_storage import load_errors
        from services.error_storage import persist_error

        error = ErrorResponse(message="Test error")
        persist_error(error)

        loaded = load_errors()
        assert len(loaded.errors) == 1
        assert loaded.errors[0].message == "Test error"
        assert loaded.last_crash is not None

    def test_multiple_errors_persisted(self, temp_error_file):
        """Test multiple errors are persisted correctly."""
        from models.errors import ErrorResponse
        from services.error_storage import load_errors
        from services.error_storage import persist_error

        for i in range(3):
            persist_error(ErrorResponse(message=f"Error {i}"))

        loaded = load_errors()
        assert len(loaded.errors) == 3
        assert loaded.errors[2].message == "Error 2"

    def test_max_errors_limit(self, temp_error_file, monkeypatch):
        """Test that only last N errors are kept."""
        from models.errors import ErrorResponse
        import services.error_storage as storage_module
        from services.error_storage import load_errors
        from services.error_storage import persist_error

        monkeypatch.setattr(storage_module, "MAX_PERSISTED_ERRORS", 3)

        for i in range(5):
            persist_error(ErrorResponse(message=f"Error {i}"))

        loaded = load_errors()
        assert len(loaded.errors) == 3
        # Should have errors 2, 3, 4 (last 3)
        assert loaded.errors[0].message == "Error 2"
        assert loaded.errors[2].message == "Error 4"

    def test_clear_errors(self, temp_error_file):
        """Test clearing persisted errors."""
        from models.errors import ErrorResponse
        from services.error_storage import clear_errors
        from services.error_storage import load_errors
        from services.error_storage import persist_error

        persist_error(ErrorResponse(message="Test error"))
        assert load_errors().errors != []

        clear_errors()
        assert not temp_error_file.exists()
        assert load_errors().errors == []

    def test_load_errors_no_file(self, temp_error_file):
        """Test loading when no error file exists."""
        from services.error_storage import load_errors

        loaded = load_errors()
        assert loaded.errors == []
        assert loaded.last_crash is None

    def test_load_errors_corrupted_file(self, temp_error_file):
        """Test loading with corrupted JSON file."""
        from services.error_storage import load_errors

        temp_error_file.parent.mkdir(parents=True, exist_ok=True)
        temp_error_file.write_text("not valid json {{{")

        loaded = load_errors()
        assert loaded.errors == []

    def test_get_previous_errors(self, temp_error_file):
        """Test get_previous_errors returns serialized data."""
        from models.errors import ErrorResponse
        from services.error_storage import get_previous_errors
        from services.error_storage import persist_error

        persist_error(ErrorResponse(message="API error"))

        errors = get_previous_errors()
        assert len(errors) == 1
        assert errors[0]["message"] == "API error"
        assert "id" in errors[0]
        assert "timestamp" in errors[0]

    def test_has_previous_errors(self, temp_error_file):
        """Test has_previous_errors check."""
        from models.errors import ErrorResponse
        from services.error_storage import has_previous_errors
        from services.error_storage import persist_error

        assert has_previous_errors() is False

        persist_error(ErrorResponse(message="Test"))
        assert has_previous_errors() is True


class TestAppErrorHandler:
    """Tests for the app-level error handler integration."""

    @pytest.fixture()
    def app_client(self, tmp_path, monkeypatch):
        """Create test client with error storage configured."""
        import importlib.util
        import sys

        # Configure test database path
        db_path = tmp_path / "save.db"
        monkeypatch.setenv("AF_DB_PATH", str(db_path))
        monkeypatch.setenv("AF_DB_KEY", "testkey")

        # Configure error storage path
        error_file = tmp_path / "data" / "errors.json"
        import services.error_storage as storage_module

        monkeypatch.setattr(storage_module, "ERROR_FILE", error_file)

        # Clear game module cache
        if "game" in sys.modules:
            del sys.modules["game"]

        # Load app module
        monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
        spec = importlib.util.spec_from_file_location(
            "app",
            Path(__file__).resolve().parents[1] / "app.py",
        )
        app_module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(app_module)
        app_module.app.testing = True

        # Mock shutdown to avoid stopping the test
        called = {"flag": False}

        async def fake_shutdown() -> None:
            called["flag"] = True

        monkeypatch.setattr(app_module, "request_shutdown", fake_shutdown)

        # Add test route that raises an exception
        @app_module.app.route("/test-error")
        async def test_error() -> None:
            raise ValueError("Test error for persistence")

        return app_module.app.test_client(), called, error_file

    @pytest.mark.asyncio
    async def test_error_handler_returns_standardized_format(self, app_client):
        """Test error handler returns standardized JSON format."""
        client, called, _ = app_client
        response = await client.get("/test-error")

        assert response.status_code == 500
        data = await response.get_json()

        # Check standardized format fields
        assert "id" in data
        assert "timestamp" in data
        assert "severity" in data
        assert data["severity"] == "critical"
        assert "message" in data
        assert data["message"] == "Test error for persistence"
        assert "traceback" in data
        assert "ValueError" in data["traceback"]
        assert "status" in data
        assert data["status"] == "error"
        assert called["flag"] is True

    @pytest.mark.asyncio
    async def test_error_handler_persists_error(self, app_client):
        """Test error handler persists error to file."""
        client, _, error_file = app_client

        await client.get("/test-error")

        # Check error was persisted
        assert error_file.exists()
        content = json.loads(error_file.read_text())
        assert len(content["errors"]) == 1
        assert content["errors"][0]["message"] == "Test error for persistence"

    @pytest.mark.asyncio
    async def test_previous_errors_endpoint(self, app_client):
        """Test GET /api/previous-errors endpoint."""
        client, _, _ = app_client

        # First trigger an error
        await client.get("/test-error")

        # Then check previous errors endpoint
        response = await client.get("/api/previous-errors")
        assert response.status_code == 200

        data = await response.get_json()
        assert data["has_errors"] is True
        assert len(data["errors"]) == 1
        assert data["errors"][0]["message"] == "Test error for persistence"

    @pytest.mark.asyncio
    async def test_acknowledge_errors_endpoint(self, app_client):
        """Test POST /api/acknowledge-errors endpoint."""
        client, _, error_file = app_client

        # First trigger an error
        await client.get("/test-error")
        assert error_file.exists()

        # Acknowledge errors
        response = await client.post("/api/acknowledge-errors")
        assert response.status_code == 200

        data = await response.get_json()
        assert data["status"] == "ok"

        # Verify errors were cleared
        assert not error_file.exists()

        # Verify previous errors endpoint returns empty
        response = await client.get("/api/previous-errors")
        data = await response.get_json()
        assert data["has_errors"] is False
        assert data["errors"] == []

    @pytest.mark.asyncio
    async def test_http_exception_not_persisted(self, app_client):
        """Test HTTP exceptions are not persisted."""
        client, called, error_file = app_client

        response = await client.get("/nonexistent-route")
        assert response.status_code == 404

        # HTTP exceptions should not trigger error persistence
        assert not error_file.exists()
        assert called["flag"] is False
