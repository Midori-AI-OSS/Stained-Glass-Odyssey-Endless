# Standardize Backend Error Handling with Persistence

## Task ID
`d9cd4bd4-standardize-backend-errors`

## Priority
High

## Status
COMPLETE

## Description
When the backend crashes, the WebUI shows a 404 error instead of the actual error from the backend. This task aims to:
1. Standardize all backend errors to use JSON/Pydantic responses
2. Persist errors to disk so they survive crashes
3. Load persisted errors on startup and display them to users
4. Recommend users open a GitHub issue via the feedback button on the main menu

## Context
Currently:
- Backend crashes result in lost error context
- Frontend shows generic 404 instead of helpful error information
- Users have no way to report issues with proper error details
- The error context system exists (`backend/error_context.py`) but isn't fully utilized
- Frontend has `ErrorOverlay.svelte` which can display rich error information
- Feedback button exists but isn't connected to the error flow

## Current Implementation

### Error Context (`backend/error_context.py`)
```python
def format_exception_with_context(exc: BaseException) -> tuple[str, dict[str, Any] | None]:
    """Return a formatted traceback string and context for the innermost frame."""
    # Returns (formatted_traceback, context_dict)
```

### Error Overlay (`frontend/src/lib/components/ErrorOverlay.svelte`)
```svelte
export let message = '';
export let traceback = '';
export let context = null;  // { file, line, function, source }
```

### Feedback System
- `FEEDBACK_URL` in `frontend/src/lib/systems/constants.js`
- Feedback button on main menu

## Problem Analysis
1. **No error persistence**: Crashes lose error details
2. **No standard error format**: Different endpoints return different error shapes
3. **No error loading on startup**: Even if persisted, errors aren't shown
4. **Disconnected feedback flow**: Users see 404, not actionable error info
5. **No automatic issue template**: Users have to manually describe errors

## Objectives
1. Create standardized error response format using Pydantic
2. Persist errors to JSON file on disk
3. Load and display errors on backend startup
4. Connect error display to feedback/issue reporting
5. Improve frontend error handling for backend crashes

## Implementation Plan

### Part 1: Standardized Error Format

#### Create Error Models
```python
# backend/models/errors.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional
from enum import Enum

class ErrorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorSource(BaseModel):
    line: int
    code: str
    highlight: bool = False

class ErrorContext(BaseModel):
    file: str
    line: int
    function: Optional[str] = None
    source: list[ErrorSource] = []

class ErrorResponse(BaseModel):
    """Standardized error response format."""
    id: str  # UUID for tracking
    timestamp: datetime
    severity: ErrorSeverity
    message: str
    traceback: Optional[str] = None
    context: Optional[ErrorContext] = None
    metadata: dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PersistedErrors(BaseModel):
    """Collection of errors persisted to disk."""
    errors: list[ErrorResponse] = []
    last_crash: Optional[datetime] = None
```

### Part 2: Error Persistence

#### Error Storage Service
```python
# backend/services/error_storage.py
import json
from pathlib import Path
from datetime import datetime
from models.errors import ErrorResponse, PersistedErrors

ERROR_FILE = Path("data/errors.json")

class ErrorStorage:
    @staticmethod
    def persist_error(error: ErrorResponse) -> None:
        """Save error to persistent storage."""
        ERROR_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        existing = ErrorStorage.load_errors()
        existing.errors.append(error)
        existing.last_crash = datetime.now()
        
        # Keep only last 10 errors
        existing.errors = existing.errors[-10:]
        
        ERROR_FILE.write_text(existing.json(indent=2))
    
    @staticmethod
    def load_errors() -> PersistedErrors:
        """Load errors from persistent storage."""
        if not ERROR_FILE.exists():
            return PersistedErrors()
        try:
            return PersistedErrors.parse_file(ERROR_FILE)
        except Exception:
            return PersistedErrors()
    
    @staticmethod
    def clear_errors() -> None:
        """Clear persisted errors after user acknowledgment."""
        if ERROR_FILE.exists():
            ERROR_FILE.unlink()
```

### Part 3: Global Error Handler

#### App-Level Error Handling
```python
# backend/app.py (modifications)
from quart import Quart, jsonify
from services.error_storage import ErrorStorage
from error_context import format_exception_with_context
from models.errors import ErrorResponse, ErrorSeverity
import uuid
from datetime import datetime

app = Quart(__name__)

@app.errorhandler(Exception)
async def handle_exception(e):
    """Global error handler that persists and returns errors."""
    traceback_str, context = format_exception_with_context(e)
    
    error = ErrorResponse(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        severity=ErrorSeverity.ERROR,
        message=str(e),
        traceback=traceback_str,
        context=context,
        metadata={"type": type(e).__name__}
    )
    
    # Persist for crash recovery
    ErrorStorage.persist_error(error)
    
    return jsonify(error.dict()), 500
```

### Part 4: Startup Error Check

#### Check for Previous Crash
```python
# backend/app.py (startup hook)
@app.before_serving
async def check_previous_crash():
    """Check for errors from previous crash and make them available."""
    persisted = ErrorStorage.load_errors()
    if persisted.errors:
        app.config['PREVIOUS_CRASH_ERRORS'] = persisted.errors
        log.warning(
            "Found %d errors from previous session",
            len(persisted.errors)
        )

@app.route('/api/previous-errors')
async def get_previous_errors():
    """Return errors from previous crash for display."""
    errors = app.config.get('PREVIOUS_CRASH_ERRORS', [])
    return jsonify({
        "errors": [e.dict() for e in errors],
        "has_errors": len(errors) > 0
    })

@app.route('/api/acknowledge-errors', methods=['POST'])
async def acknowledge_errors():
    """Clear persisted errors after user acknowledges."""
    ErrorStorage.clear_errors()
    app.config['PREVIOUS_CRASH_ERRORS'] = []
    return jsonify({"status": "ok"})
```

### Part 5: Frontend Integration

#### Check for Crash Errors on Load
```javascript
// frontend/src/routes/+page.svelte (or appropriate location)
import { onMount } from 'svelte';

let previousCrashErrors = [];
let showCrashRecovery = false;

onMount(async () => {
    try {
        const res = await fetch('/api/previous-errors');
        const data = await res.json();
        if (data.has_errors) {
            previousCrashErrors = data.errors;
            showCrashRecovery = true;
        }
    } catch (e) {
        // Backend not available yet
    }
});
```

#### Crash Recovery Modal
```svelte
<!-- frontend/src/lib/components/CrashRecoveryOverlay.svelte -->
<script>
  import ErrorOverlay from './ErrorOverlay.svelte';
  import { FEEDBACK_URL } from '../systems/constants.js';
  
  export let errors = [];
  
  $: latestError = errors[errors.length - 1];
  $: issueUrl = buildIssueUrl(latestError);
  
  function buildIssueUrl(error) {
    const title = encodeURIComponent(`[Crash] ${error?.message || 'Unknown error'}`);
    const body = encodeURIComponent(formatIssueBody(error));
    return `${FEEDBACK_URL}?title=${title}&body=${body}`;
  }
  
  function formatIssueBody(error) {
    return `## Crash Report
    
**Error:** ${error?.message}

**Timestamp:** ${error?.timestamp}

### Traceback
\`\`\`
${error?.traceback || 'No traceback available'}
\`\`\`

### Context
- File: ${error?.context?.file}
- Line: ${error?.context?.line}
- Function: ${error?.context?.function}
`;
  }
  
  async function acknowledgeAndClose() {
    await fetch('/api/acknowledge-errors', { method: 'POST' });
    dispatch('close');
  }
</script>

<div class="crash-recovery">
  <h2>Previous Session Crashed</h2>
  <p>The game encountered an error in your last session.</p>
  
  <ErrorOverlay 
    message={latestError?.message}
    traceback={latestError?.traceback}
    context={latestError?.context}
  />
  
  <div class="actions">
    <a href={issueUrl} target="_blank" rel="noopener" class="btn primary">
      Report on GitHub
    </a>
    <button on:click={acknowledgeAndClose} class="btn secondary">
      Dismiss
    </button>
  </div>
</div>
```

## Files to Create
- `backend/models/errors.py` - Pydantic error models
- `backend/services/error_storage.py` - Error persistence service
- `frontend/src/lib/components/CrashRecoveryOverlay.svelte` - Crash recovery UI

## Files to Modify
- `backend/app.py` - Global error handler, startup check, API endpoints
- `backend/error_context.py` - May need updates to work with Pydantic
- `frontend/src/routes/+page.svelte` - Check for previous crash on load
- `frontend/src/lib/components/ErrorOverlay.svelte` - Enhance for crash recovery

## Acceptance Criteria
- [x] All backend errors return standardized JSON format
- [x] Errors are persisted to `data/errors.json` on crash
- [x] Errors are loaded and checked on backend startup
- [x] Frontend checks for previous crash errors on load
- [x] Crash recovery modal shows error details
- [x] "Report on GitHub" button opens issue with pre-filled details
- [x] Users can dismiss the modal and clear persisted errors
- [x] Works for both API errors and unhandled exceptions
- [x] Error format includes traceback and source context
- [x] Linting passes for both backend and frontend

## Completion Notes (Auditor Verified 2025-11-29)

### Implementation Verified:
- `backend/models/errors.py` - Pydantic error models (ErrorResponse, PersistedErrors, etc.)
- `backend/services/error_storage.py` - Error persistence service with atexit handler
- `backend/app.py` - Global error handler, `/api/previous-errors`, `/api/acknowledge-errors`
- `frontend/src/lib/components/CrashRecoveryOverlay.svelte` - Crash recovery UI
- `backend/tests/test_error_persistence.py` - 22 comprehensive tests
- `backend/tests/test_error_handler.py` - 2 additional tests

### Tests Verified:
```bash
uv run pytest tests/test_error_persistence.py tests/test_error_handler.py -v
# Result: 24 passed
```

## Final Audit Review (2025-12-03)

### Audit Verification Performed:
✅ **Code Implementation Review**
- Verified all files exist and contain expected implementations
- `backend/models/errors.py` - Complete with ErrorResponse, PersistedErrors, error_context_from_dict, create_error_response
- `backend/services/error_storage.py` - Complete with persist_error, load_errors, clear_errors, atexit handler
- `backend/app.py` - Global error handler integrated (lines 114+), endpoints at /api/previous-errors and /api/acknowledge-errors
- `frontend/src/lib/components/CrashRecoveryOverlay.svelte` - Crash recovery UI complete
- `frontend/src/routes/+page.svelte` - Integration verified with checkPreviousCrash() function

✅ **Test Coverage**
- All 24 tests passing (22 in test_error_persistence.py, 2 in test_error_handler.py)
- Tests cover: error models, persistence, loading, API endpoints, atexit handler
- Test execution time: 0.92s (excellent performance)

✅ **Code Quality**
- Linting passes for all task-related files
- No violations in backend/models/errors.py, backend/services/error_storage.py
- Code follows repository standards

✅ **Acceptance Criteria Met**
- All 10 acceptance criteria verified as complete
- Standardized JSON error format implemented
- Persistence to data/errors.json working
- Startup error loading functional
- Frontend crash recovery modal integrated
- API endpoints functional

### Recommendation: **APPROVED FOR TASKMASTER REVIEW**
Task is complete, well-tested, and production-ready. Ready for final sign-off.

## Testing Requirements

### Backend Tests
- Test error format matches Pydantic model
- Test error persistence to file
- Test error loading on startup
- Test API endpoint responses

### Frontend Tests
- Test crash recovery modal display
- Test issue URL generation
- Test acknowledgment flow

### Integration Tests
- Simulate crash, restart, verify error shown
- Test full flow from crash to GitHub issue

## Notes for Coder
- Use UUID for error IDs to enable tracking
- Keep only last 10 errors to prevent file bloat
- Consider adding error categorization for better filtering
- The feedback button hint suggests connecting to existing feedback flow
- Error persistence file should be in a data directory, not in code
- Consider adding system info (version, platform) to error reports
- Handle case where backend dies before persisting error (atexit?)
- Test with actual crashes, not just simulated errors
