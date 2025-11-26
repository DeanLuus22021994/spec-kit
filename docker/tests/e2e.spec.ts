// e2e tests for the Semantic Kernel application

import { expect, Page, test } from "@playwright/test";

test.describe("Semantic Kernel End-to-End Tests", () => {
  test("should load the homepage", async ({ page }: { page: Page }) => {
    await page.goto("http://localhost:3000");
    await expect(page).toHaveTitle(/Semantic Kernel/);
  });

  test("should authenticate user", async ({ page }: { page: Page }) => {
    await page.goto("http://localhost:3000/login");
    await page.fill('input[name="username"]', "testuser");
    await page.fill('input[name="password"]', "password123");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("http://localhost:3000/dashboard");
  });

  test("should fetch data from the API", async ({ page }: { page: Page }) => {
    await page.goto("http://localhost:3000/dashboard");
    const response = await page.request.get("http://localhost:5000/api/data");
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty("items");
  });

  test("should handle 404 errors gracefully", async ({
    page,
  }: {
    page: Page;
  }) => {
    await page.goto("http://localhost:3000/non-existent-page");
    await expect(page.locator("h1")).toHaveText("404 Not Found");
  });
});
