import { expect, test } from "@playwright/test";
import { HomePage } from "../../pages/HomePage";

test.describe("Frontend - Homepage UI", () => {
  let homePage: HomePage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    await homePage.navigate();
  });

  test("should display the homepage with correct title", async () => {
    const title = await homePage.getTitle();
    expect(title).toContain("Semantic Kernel");

    const headerText = await homePage.getHeaderText();
    expect(headerText).toBeTruthy();
  });

  test("should have prompt input and submit button", async () => {
    await expect(homePage.promptInput).toBeVisible();
    await expect(homePage.submitButton).toBeVisible();

    const isEnabled = await homePage.isSubmitEnabled();
    expect(isEnabled).toBeTruthy();
  });

  test("should allow entering text in prompt input", async () => {
    const testPrompt = "Tell me about artificial intelligence";
    await homePage.promptInput.fill(testPrompt);

    const inputValue = await homePage.promptInput.inputValue();
    expect(inputValue).toBe(testPrompt);
  });

  test("should clear prompt input", async () => {
    await homePage.promptInput.fill("Test text");
    await homePage.clearPrompt();

    const inputValue = await homePage.promptInput.inputValue();
    expect(inputValue).toBe("");
  });

  test("should submit a prompt and wait for response", async ({ page }) => {
    // Mock API response for testing
    await page.route("**/api/semantic/completion", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          response: "This is a test response from Semantic Kernel",
          success: true,
        }),
      });
    });

    await homePage.submitPrompt("What is machine learning?");

    // Should show loading indicator briefly
    const isLoading = await homePage.isLoading();
    // Loading might be too fast to catch, so we just check if it exists

    // Wait for response
    await homePage.waitForResponse();

    const responseText = await homePage.getResponseText();
    expect(responseText).toContain("test response");
  });

  test("should handle API errors gracefully", async ({ page }) => {
    // Mock API error response
    await page.route("**/api/semantic/completion", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          error: "Internal server error",
          success: false,
        }),
      });
    });

    await homePage.submitPrompt("This will fail");

    // Wait for error message
    await homePage.errorMessage.waitFor({ state: "visible", timeout: 5000 });

    const hasError = await homePage.hasError();
    expect(hasError).toBeTruthy();

    const errorText = await homePage.getErrorText();
    expect(errorText).toBeTruthy();
  });

  test("should display proper page structure", async ({ page }) => {
    // Check for Semantic UI components
    const container = page.locator(".ui.container");
    await expect(container).toBeVisible();

    const header = page.locator(".ui.header");
    await expect(header).toBeVisible();
  });

  test("should be responsive on mobile viewports", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await homePage.navigate();

    // Check if elements are still visible and accessible
    await expect(homePage.headerTitle).toBeVisible();
    await expect(homePage.promptInput).toBeVisible();
    await expect(homePage.submitButton).toBeVisible();
  });
});
