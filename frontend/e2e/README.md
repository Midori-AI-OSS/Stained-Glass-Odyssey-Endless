# End-to-End Tests

This directory contains Playwright-based end-to-end tests for the Midori AI AutoFighter game.

## Test Files

### battle-start.spec.js
Tests the complete flow of starting a battle in the game:
- **Battle Start Test**: Navigates to the home page, clicks the Run button, starts a new run, and verifies battle UI appears
- **Smoke Test**: Verifies the application loads without errors and displays the viewport

## Running Tests Locally

### Prerequisites
```bash
# Install dependencies
cd frontend
bun install

# Install Playwright browsers
bunx playwright install --with-deps chromium
```

### Start the Backend
In one terminal:
```bash
cd backend
uv run app.py
```

The backend should start on http://localhost:59002

### Run Tests
In another terminal:
```bash
cd frontend
bunx playwright test
```

### View Test Results
```bash
# Open the HTML report
bunx playwright show-report

# Run tests in UI mode (interactive)
bunx playwright test --ui

# Run tests in headed mode (see browser)
bunx playwright test --headed

# Run specific test file
bunx playwright test e2e/battle-start.spec.js
```

## CI/CD Integration

These tests are automatically run by GitHub Actions workflows:
- `.github/workflows/e2e-test-1.yml` - First sub-agent workflow
- `.github/workflows/e2e-test-2.yml` - Second sub-agent workflow

Each workflow tests 3 game variants in parallel:
- `non-llm` - Base game without LLM features
- `llm-cpu` - CPU-based LLM support
- `llm-cuda` - NVIDIA GPU LLM support

The workflows automatically:
1. Set up the environment with appropriate dependencies
2. Build the frontend
3. Start the backend server for each variant
4. Start the frontend dev server
5. Run Playwright tests
6. Upload test artifacts (reports, videos, screenshots) on failure

## Configuration

The Playwright configuration is in `playwright.config.js` at the frontend root. It includes:
- Test directory: `./e2e`
- Base URL: `http://localhost:59001`
- Browser: Chromium (Desktop Chrome)
- Retries: 2 on CI, 0 locally
- Screenshots: On failure only
- Videos: Retained on failure
- HTML reporter for test results

The config also includes a webServer setting that automatically starts the frontend dev server when running tests locally.

## Adding New Tests

To add new E2E tests:

1. Create a new `.spec.js` file in this directory
2. Import Playwright test utilities:
   ```javascript
   import { test, expect } from '@playwright/test';
   ```
3. Write your tests using the Playwright API
4. Run tests locally to verify they work
5. Tests will automatically be picked up by CI workflows

## Debugging Failed Tests

When tests fail in CI:
1. Check the GitHub Actions workflow run
2. Download the test artifacts (reports, videos, screenshots)
3. Review the HTML report for detailed failure information
4. Watch the video recording to see what happened
5. Look at screenshots taken at the point of failure

For local debugging:
```bash
# Run with debug mode
PWDEBUG=1 bunx playwright test

# Run in headed mode with slow motion
bunx playwright test --headed --slow-mo=1000
```

## Best Practices

- Tests should be independent and not rely on each other
- Use `waitForLoadState('networkidle')` to ensure page is fully loaded
- Use `waitForTimeout()` sparingly - prefer waiting for specific elements
- Make tests resilient by checking for multiple possible selectors
- Add meaningful assertions that verify actual functionality
- Keep tests focused on user workflows, not implementation details
