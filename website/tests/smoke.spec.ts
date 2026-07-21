import { test, expect } from '@playwright/test';

test.describe('AetherGrid Sovereign Public Site', () => {
  test('homepage loads and displays hero', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/AetherGrid Sovereign/);
    
    // Check hero heading
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('The Sovereign Cryptographic Mesh');
  });

  test('navigation links resolve properly (no dead links)', async ({ page }) => {
    await page.goto('/');
    
    // All anchors should have an href that is not just "#"
    const links = page.locator('a');
    const count = await links.count();
    
    for (let i = 0; i < count; i++) {
      const href = await links.nth(i).getAttribute('href');
      expect(href).not.toBe('#');
      expect(href).toBeTruthy();
    }
  });

  test('tabs are operable', async ({ page }) => {
    await page.goto('/');
    
    // Check that we have tabs
    const tabs = page.locator('[role="tab"]');
    await expect(tabs).toHaveCount(3);
    
    // Click the second tab
    await tabs.nth(1).click();
    
    // Verify it becomes selected
    await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true');
    await expect(tabs.nth(0)).toHaveAttribute('aria-selected', 'false');
    
    // Check panel updates
    const panel = page.locator('[role="tabpanel"]');
    await expect(panel).toBeVisible();
    await expect(panel.locator('h4')).toContainText('Dynamic threat modeling during extreme weather');
  });

  test('mobile menu opens and closes', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Hamburger button in nav
    const menuBtn = page.locator('nav button').first();
    await menuBtn.click();
    
    // Check if mobile menu links appear
    const mobileMenu = page.locator('nav').locator('div').filter({ hasText: 'Capabilities' }).last();
    const mobileLink = mobileMenu.getByText('Operator Dashboard');
    await expect(mobileLink).toBeVisible();
    
    // Close menu
    await menuBtn.click();
    await expect(mobileLink).not.toBeVisible();
  });
});
