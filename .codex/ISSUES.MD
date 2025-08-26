# Issues Identified in Midori-AI-AutoFighter Repository

## Summary
This document outlines the identified issues with linting and testing infrastructure in the repository.

## Linting Issues

### Status: ✅ FIXED
All linting issues have been resolved:

#### Backend Linting (Fixed)
- **4 errors** identified and fixed in `backend/` directory:
  - ❌ `backend/plugins/dots/abyssal_weakness.py`: Duplicate import of `DamageOverTime` 
  - ❌ `backend/routes/rooms.py`: Unused variable `start` and unused import `time`
  - ❌ `backend/routes/runs.py`: Unused imports `load_party` and `save_party`

#### Legacy Linting (Fixed) 
- **28 errors** identified and fixed in `legacy/` directory:
  - ❌ Multiple unused imports (`random`, `math`, `colorama.Style`, `typing.Tuple`, etc.)
  - ❌ Multiple unused variables (`error`, `music`, `dt`)
  - ❌ Multiple f-string formatting issues (extraneous `f` prefixes)

### Tools Used
- `ruff` linter with automatic fixes via `--fix` flag
- Manual fixes for remaining unsafe changes

## Testing Issues

### Status: ⚠️ PARTIALLY ADDRESSED

#### Missing Test Infrastructure Dependencies
- **Issue**: Tests fail due to missing `uv` and `bun` commands in `run-tests.sh`
- **Impact**: CI/CD pipeline and local test execution fails
- **Root Cause**: Test runner script expects `uv` (Python) and `bun` (Node.js) package managers
- **Workaround**: Manual installation of dependencies with `python3 -m pip install`

#### Backend Tests
- **Status**: Infrastructure exists in `backend/tests/` directory
- **Issues**: 
  - Missing dependencies: `sqlcipher3-binary`, `quart`, `pytest-asyncio`, `pillow`, etc.
  - Tests use complex fixtures and async patterns
  - Some tests failing due to missing environment setup
- **Tests Found**: 47 test files in `backend/tests/`

#### Frontend Tests  
- **Status**: Infrastructure exists in `frontend/tests/` directory
- **Issues**: Missing `bun` package manager for JavaScript/TypeScript tests
- **Tests Found**: 24 test files in `frontend/tests/`

#### Missing Tests Mentioned in Repository Context
The repository context references test files that appear to be missing:
- `tests/test_plugin_loader.py` - ❌ NOT FOUND
- `tests/test_passive_plugins.py` - ❌ NOT FOUND  
- `tests/test_gacha_system.py` - ❌ NOT FOUND (differs from `backend/tests/test_gacha.py`)

**Note**: These may be from a different branch/state or need to be created.

## Recommendations

### Immediate Actions
1. ✅ **COMPLETED**: Fix all linting errors with ruff
2. ⚠️ **IN PROGRESS**: Address test dependency issues
3. 📋 **TODO**: Update `run-tests.sh` to handle missing `uv`/`bun` gracefully
4. 📋 **TODO**: Document proper test setup procedures

### Long-term Improvements
1. **Container-based testing**: Use Docker containers with pre-installed `uv` and `bun`
2. **Dependency documentation**: Clear setup instructions for development environment
3. **Test isolation**: Reduce dependency complexity for unit tests
4. **CI/CD robustness**: Add fallback test runners for missing tools

### Test Environment Setup
For manual testing, install required dependencies:
```bash
# Python dependencies
python3 -m pip install --user ruff pytest sqlcipher3-binary quart pytest-asyncio pillow rich cryptography

# Note: uv and bun installation may require manual setup or CI environment
```

## GitHub Actions Workflow
The existing CI workflow in `.github/workflows/ci.yml` correctly uses:
- `astral-sh/setup-uv@v3` for Python backend testing
- `oven-sh/setup-bun@v1` for Node.js frontend testing
- Matrix strategy for parallel test execution

The workflow should work correctly in GitHub Actions environment.

## Related Files
- **Linting config**: `ruff.toml` (root directory)
- **Test script**: `run-tests.sh` (root directory) 
- **CI workflow**: `.github/workflows/ci.yml`
- **Backend config**: `backend/pyproject.toml`
- **Legacy config**: `legacy/pyproject.toml`