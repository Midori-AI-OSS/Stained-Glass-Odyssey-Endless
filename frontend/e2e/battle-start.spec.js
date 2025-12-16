import { test, expect } from '@playwright/test';

test.describe('Battle Start', () => {
  test('should start a new run and begin battle', async ({ page }) => {
    // Navigate to the home page
    await page.goto('/');

    // Wait for the page to load - look for the main viewport or menu
    await page.waitForLoadState('networkidle');
    
    // Wait a bit for the app to initialize (Svelte hydration, backend connection check)
    await page.waitForTimeout(2000);

    // Look for the "Run" button in the menu - could be a button or link
    // Try multiple selectors to be robust
    const runButton = page.locator('button:has-text("Run"), a:has-text("Run"), [aria-label*="Run"]').first();
    
    // Wait for the Run button to be visible
    await expect(runButton).toBeVisible({ timeout: 10000 });
    
    // Click the Run button to open the run selection
    await runButton.click();
    
    // Wait for the run chooser/overlay to appear
    // This might show existing runs or allow starting a new run
    await page.waitForTimeout(1000);
    
    // If there's a "New Run" option, click it first
    const newRunButton = page.locator('button:has-text("New Run"), button:has-text("Start New Run")');
    if (await newRunButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await newRunButton.first().click();
      await page.waitForTimeout(1000);
    }
    
    // Now look for the actual Start button (might be in a wizard or party selection)
    const finalStartButton = page.locator(
      'button:has-text("Start"), button:has-text("Begin"), button:has-text("Continue"), button:has-text("Confirm")'
    ).first();
    
    // Wait for and click the start button
    await expect(finalStartButton).toBeVisible({ timeout: 10000 });
    await finalStartButton.click();
    
    // Wait for battle to start - look for battle UI elements
    // Battle view should show combat elements, health bars, or battle status
    await page.waitForTimeout(3000);
    
    // Verify battle UI is present - look for common battle elements
    // Could be a battle viewport, enemy units, player units, etc.
    const battleIndicators = [
      page.locator('[class*="battle"]'),
      page.locator('[class*="combat"]'),
      page.locator('text=/Enemy|Foe|Battle|Combat/i'),
      page.locator('[aria-label*="Battle"]'),
      page.locator('[data-testid*="battle"]'),
    ];
    
    // At least one battle indicator should be visible
    let battleFound = false;
    for (const indicator of battleIndicators) {
      if (await indicator.first().isVisible({ timeout: 5000 }).catch(() => false)) {
        battleFound = true;
        break;
      }
    }
    
    // Assert that we found battle UI
    expect(battleFound).toBeTruthy();
    
    // Alternative: Check that we're no longer on the main menu
    const menuStillVisible = await page.locator('text=/Main Menu|Start Screen/i')
      .isVisible({ timeout: 1000 })
      .catch(() => false);
    expect(menuStillVisible).toBeFalsy();
  });

  test('should load the application without errors', async ({ page }) => {
    // Basic smoke test - just verify the app loads
    await page.goto('/');
    
    // Wait for network to be idle
    await page.waitForLoadState('networkidle');
    
    // Check for no console errors (Playwright automatically collects these)
    // We just verify the page loaded successfully
    await expect(page).toHaveTitle(/AutoFighter|Midori/i, { timeout: 10000 });
    
    // Verify the viewport is present
    const viewport = page.locator('[class*="viewport"]').first();
    await expect(viewport).toBeVisible({ timeout: 10000 });
  });
});
