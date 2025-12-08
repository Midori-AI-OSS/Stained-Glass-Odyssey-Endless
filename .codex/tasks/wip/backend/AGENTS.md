# Backend Tasks Category

This category contains tasks related to backend system changes, refactoring, and infrastructure improvements.

## Current Tasks

### LRM/LLM Management Migration
Migration from custom LLM loader implementation to the Midori AI Agent Framework for better standardization, easier maintenance, and improved features.

## Task Priority Guidelines

- **High Priority**: Core functionality, blocking other tasks, critical bugs
- **Medium Priority**: Feature enhancements, non-blocking improvements
- **Low Priority**: Documentation, minor optimizations, quality of life improvements

## Testing Requirements

All backend tasks must:
1. Pass existing test suite
2. Add new tests for new functionality
3. Pass linting (`uv tool run ruff check backend --fix`)
4. Not break existing API contracts
5. Include performance testing for critical paths

## Related Documentation

- `.codex/implementation/` - Technical implementation details
- `backend/README.md` - Backend service documentation
- `AGENTS.md` - Repository-wide contributor guide
