# Contributing to Midori AI AutoFighter

Thank you for your interest in contributing to Midori AI AutoFighter! This document provides guidelines for contributors.

## Development Setup

### Prerequisites

Install the required tools:

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install bun (JavaScript package manager) 
curl -fsSL https://bun.sh/install | bash
```

### Setting Up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Midori-AI-OSS/Midori-AI-AutoFighter.git
   cd Midori-AI-AutoFighter
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   uv sync --group dev  # Install dependencies including development tools
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   bun install
   ```

## Development Workflow

### Running the Application

**Backend (in one terminal):**
```bash
cd backend
uv run app.py
```

**Frontend (in another terminal):**
```bash
cd frontend
bun run dev
```

The application will be available at `http://localhost:59001`.

### Code Quality and Testing

We maintain high code quality standards. Please run these commands before submitting changes:

#### Linting and Formatting

```bash
# Backend linting and formatting
cd backend
uv run black .                    # Format code
uv run mypy .                     # Type checking
uv tool run ruff check . --fix    # Linting with auto-fixes

# Frontend linting
cd frontend
bun run lint                      # Check for issues
bun run lint:fix                  # Auto-fix issues
```

#### Running Tests

```bash
# Run all tests (recommended)
./run-tests.sh

# Backend tests only
cd backend
uv run pytest tests/

# Frontend tests only
cd frontend
bun test tests/

# Run specific test file
cd backend
uv run pytest tests/test_specific_file.py -v
```

### Making Changes

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following these guidelines:
   - Write clear, documented code
   - Add type annotations for new functions
   - Include tests for new functionality
   - Follow existing code patterns and conventions

3. **Test your changes:**
   ```bash
   ./run-tests.sh  # Run full test suite
   ```

4. **Check code quality:**
   ```bash
   cd backend && uv run black . && uv run mypy . && uv tool run ruff check . --fix
   cd ../frontend && bun run lint:fix
   ```

## Code Style Guidelines

### Python (Backend)

- **Formatting:** We use [Black](https://black.readthedocs.io/) with 88-character line length
- **Linting:** We use [Ruff](https://docs.astral.sh/ruff/) for fast Python linting
- **Type Checking:** We use [mypy](https://mypy.readthedocs.io/) for static type checking
- **Imports:** Keep imports sorted and organized (handled by ruff)

**Key conventions:**
- Use type annotations for all new functions
- Follow existing patterns for async/await usage
- Use descriptive variable and function names
- Add docstrings for public functions and classes

### JavaScript/Svelte (Frontend)

- **Linting:** We use ESLint for JavaScript/Svelte code
- **Formatting:** Follow project conventions for indentation and style

## Testing Guidelines

### Backend Testing

- **Framework:** We use pytest with pytest-asyncio for async testing
- **Structure:** Tests are located in `backend/tests/`
- **Naming:** Test files should be named `test_*.py`
- **Coverage:** Aim for good test coverage of new functionality

**Example test structure:**
```python
import pytest
from your_module import your_function

@pytest.mark.asyncio
async def test_your_feature():
    # Arrange
    expected = "expected_result"
    
    # Act
    result = await your_function()
    
    # Assert
    assert result == expected
```

### Frontend Testing

- **Framework:** We use the testing framework provided by Bun
- **Structure:** Tests are located in `frontend/tests/`

## Building the Application

### Development Builds

```bash
# Quick non-LLM build (recommended for testing)
./build.sh non-llm

# Platform-specific builds
./build.sh non-llm linux
./build.sh non-llm windows
```

### LLM-Enhanced Builds (Advanced)

⚠️ **Warning:** LLM builds take 10+ minutes due to large dependencies.

```bash
./build.sh llm-cpu    # CPU-only LLM support
./build.sh llm-cuda   # NVIDIA GPU support
./build.sh llm-amd    # AMD GPU support
```

## Pull Request Process

1. **Ensure your changes pass all checks:**
   - All tests pass (`./run-tests.sh`)
   - Code is properly formatted and linted
   - Type checking passes (mypy)

2. **Create a clear pull request:**
   - Use a descriptive title
   - Explain what your changes do and why
   - Reference any related issues
   - Include testing instructions

3. **Review checklist:**
   - [ ] Tests pass
   - [ ] Code is properly formatted (black, eslint)
   - [ ] Linting passes (ruff, eslint)
   - [ ] Type checking passes (mypy)
   - [ ] Documentation updated if needed
   - [ ] No merge conflicts

## Troubleshooting

### Common Issues

**Virtual environment issues:**
```bash
cd backend
rm -rf .venv
uv sync --group dev
```

**Build failures:**
```bash
# Clean build artifacts
rm -rf backend/build backend/dist
./build.sh non-llm
```

**Test failures:**
```bash
# Run specific failing test with verbose output
cd backend
uv run pytest tests/test_failing_file.py -v -s
```

### Getting Help

- **Documentation:** Check the README.md and other documentation files
- **Issues:** Search existing [GitHub Issues](../../issues) for similar problems
- **Community:** Join discussions in GitHub Discussions

## Project Structure

```
├── backend/           # Python Quart backend
│   ├── app.py        # Main application entry point
│   ├── game.py       # Core game logic
│   ├── autofighter/  # Game mechanics modules
│   ├── plugins/      # Character and ability plugins
│   ├── routes/       # API endpoint definitions
│   └── tests/        # Backend test suite
├── frontend/         # Svelte frontend
│   ├── src/         # Frontend source code
│   ├── static/      # Static assets
│   └── tests/       # Frontend test suite
├── autofighter/     # Shared game logic modules
├── build/           # Build scripts and configuration
└── .github/         # GitHub Actions workflows
```

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.