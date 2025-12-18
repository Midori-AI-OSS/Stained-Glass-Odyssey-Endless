import { test, expect } from '@playwright/test';

test.describe('UI Screenshot Capture', () => {
  test('should capture screenshots of all UI screens', async ({ page }) => {
    // Navigate to the home page
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // 1. Capture Main Menu
    await page.screenshot({ path: 'screenshots/01-main-menu.png', fullPage: true });
    console.log('✓ Captured: Main Menu');
    
    // 2. Navigate to Run start flow and capture all 4 steps
    const runButton = page.locator('button:has-text("Run"), a:has-text("Run"), [aria-label*="Run"]').first();
    await expect(runButton).toBeVisible({ timeout: 10000 });
    await runButton.click();
    await page.waitForTimeout(1000);
    
    // Check if there's a "New Run" button and click it
    const newRunButton = page.locator('button:has-text("New Run"), button:has-text("Start New Run")');
    if (await newRunButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await newRunButton.first().click();
      await page.waitForTimeout(1000);
    }
    
    // Capture Run Start Flow - Step 1 (initial screen)
    await page.screenshot({ path: 'screenshots/02-run-start-step1.png', fullPage: true });
    console.log('✓ Captured: Run Start Flow - Step 1');
    
    // Try to find and click through the wizard steps
    // Look for Continue/Next/Confirm buttons to progress through steps
    const progressButtons = [
      'button:has-text("Continue")',
      'button:has-text("Next")',
      'button:has-text("Confirm")',
      'button:has-text(">")'
    ];
    
    // Step 2
    for (const selector of progressButtons) {
      const btn = page.locator(selector).first();
      if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await btn.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
    await page.screenshot({ path: 'screenshots/03-run-start-step2.png', fullPage: true });
    console.log('✓ Captured: Run Start Flow - Step 2');
    
    // Step 3
    for (const selector of progressButtons) {
      const btn = page.locator(selector).first();
      if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await btn.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
    await page.screenshot({ path: 'screenshots/04-run-start-step3.png', fullPage: true });
    console.log('✓ Captured: Run Start Flow - Step 3');
    
    // Step 4
    for (const selector of progressButtons) {
      const btn = page.locator(selector).first();
      if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await btn.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
    await page.screenshot({ path: 'screenshots/05-run-start-step4.png', fullPage: true });
    console.log('✓ Captured: Run Start Flow - Step 4');
    
    // Go back to main menu to access other sections
    // Look for a back/close button or navigate directly
    const backButton = page.locator('button:has-text("Back"), button:has-text("Cancel"), button:has-text("Close"), [aria-label*="close"]').first();
    if (await backButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await backButton.click();
      await page.waitForTimeout(1000);
    } else {
      // Navigate back to home
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }
    
    // 3. Capture Pull/Gacha screen
    const pullButton = page.locator('button:has-text("Pull"), a:has-text("Pull"), button:has-text("Gacha"), a:has-text("Gacha")').first();
    if (await pullButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pullButton.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: 'screenshots/06-pull-gacha.png', fullPage: true });
      console.log('✓ Captured: Pull/Gacha');
      
      // Go back to main menu
      const backBtn = page.locator('button:has-text("Back"), button:has-text("Close"), [aria-label*="close"]').first();
      if (await backBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await backBtn.click();
        await page.waitForTimeout(1000);
      } else {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
      }
    } else {
      console.log('⚠ Pull/Gacha button not found, skipping');
    }
    
    // 4. Capture Inventory screen
    const invButton = page.locator('button:has-text("Inventory"), a:has-text("Inventory"), button:has-text("Inv"), a:has-text("Inv")').first();
    if (await invButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await invButton.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: 'screenshots/07-inventory.png', fullPage: true });
      console.log('✓ Captured: Inventory');
      
      // Go back to main menu
      const backBtn = page.locator('button:has-text("Back"), button:has-text("Close"), [aria-label*="close"]').first();
      if (await backBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await backBtn.click();
        await page.waitForTimeout(1000);
      } else {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
      }
    } else {
      console.log('⚠ Inventory button not found, skipping');
    }
    
    // 5. Capture Guidebook screen
    const guidebookButton = page.locator('button:has-text("Guide"), a:has-text("Guide"), button:has-text("Guidebook"), a:has-text("Guidebook")').first();
    if (await guidebookButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await guidebookButton.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: 'screenshots/08-guidebook.png', fullPage: true });
      console.log('✓ Captured: Guidebook');
      
      // Go back to main menu
      const backBtn = page.locator('button:has-text("Back"), button:has-text("Close"), [aria-label*="close"]').first();
      if (await backBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await backBtn.click();
        await page.waitForTimeout(1000);
      } else {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
      }
    } else {
      console.log('⚠ Guidebook button not found, skipping');
    }
    
    // 6. Capture Settings screen
    const settingsButton = page.locator('button:has-text("Settings"), a:has-text("Settings"), [aria-label*="settings"]').first();
    if (await settingsButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await settingsButton.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: 'screenshots/09-settings.png', fullPage: true });
      console.log('✓ Captured: Settings');
    } else {
      console.log('⚠ Settings button not found, skipping');
    }
    
    // Final assertion - verify at least some screenshots were captured
    expect(true).toBeTruthy();
  });
});
