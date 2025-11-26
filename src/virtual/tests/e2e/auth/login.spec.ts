import { expect, test } from "@playwright/test";
import { DashboardPage } from "../../pages/DashboardPage";
import { LoginPage } from "../../pages/LoginPage";

test.describe("Authentication Flow", () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
  });

  test("should display login page with all elements", async () => {
    await loginPage.navigate();

    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
    await expect(loginPage.forgotPasswordLink).toBeVisible();
    await expect(loginPage.signUpLink).toBeVisible();
  });

  test("should login with valid credentials", async ({ page }) => {
    // Mock successful login API
    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          token: "fake-jwt-token",
          user: {
            id: 1,
            email: "test@example.com",
            name: "Test User",
          },
        }),
      });
    });

    await loginPage.navigate();
    await loginPage.login("test@example.com", "password123");

    // Should redirect to dashboard
    await loginPage.waitForLoginSuccess();

    // Verify we're on dashboard
    const isLoggedIn = await dashboardPage.isLoggedIn();
    expect(isLoggedIn).toBeTruthy();
  });

  test("should show error message with invalid credentials", async ({
    page,
  }) => {
    // Mock failed login API
    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          success: false,
          error: "Invalid email or password",
        }),
      });
    });

    await loginPage.navigate();
    await loginPage.login("wrong@example.com", "wrongpassword");

    // Should show error message
    await loginPage.errorMessage.waitFor({ state: "visible", timeout: 5000 });

    const hasError = await loginPage.hasError();
    expect(hasError).toBeTruthy();

    const errorText = await loginPage.getErrorText();
    expect(errorText).toContain("Invalid");
  });

  test("should validate email format", async ({ page }) => {
    await loginPage.navigate();

    // Try to submit with invalid email
    await loginPage.emailInput.fill("invalid-email");
    await loginPage.passwordInput.fill("password123");

    // HTML5 validation should prevent submission or show error
    const emailValidity = await loginPage.emailInput.evaluate(
      (el: any) => el.validity.valid
    );
    expect(emailValidity).toBeFalsy();
  });

  test("should require password field", async ({ page }) => {
    await loginPage.navigate();

    await loginPage.emailInput.fill("test@example.com");
    // Leave password empty

    const passwordValidity = await loginPage.passwordInput.evaluate(
      (el: any) => el.validity.valid
    );
    expect(passwordValidity).toBeFalsy();
  });

  test("should navigate to forgot password page", async () => {
    await loginPage.navigate();
    await loginPage.clickForgotPassword();

    // Wait for navigation
    await loginPage.page.waitForURL(/\/forgot-password/, { timeout: 5000 });
  });

  test("should navigate to sign up page", async () => {
    await loginPage.navigate();
    await loginPage.clickSignUp();

    // Wait for navigation
    await loginPage.page.waitForURL(/\/signup/, { timeout: 5000 });
  });

  test("should logout from dashboard", async ({ page }) => {
    // Mock login
    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          token: "fake-jwt-token",
          user: { id: 1, email: "test@example.com", name: "Test User" },
        }),
      });
    });

    // Mock logout
    await page.route("**/api/auth/logout", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true }),
      });
    });

    // Login first
    await loginPage.navigate();
    await loginPage.login("test@example.com", "password123");
    await loginPage.waitForLoginSuccess();

    // Now logout
    await dashboardPage.logout();

    // Should redirect to login page
    await page.waitForURL(/\/login/, { timeout: 5000 });
  });

  test("should maintain session after page reload", async ({
    page,
    context,
  }) => {
    // Mock login and set session cookie
    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          token: "fake-jwt-token",
          user: { id: 1, email: "test@example.com", name: "Test User" },
        }),
      });
    });

    await loginPage.navigate();
    await loginPage.login("test@example.com", "password123");
    await loginPage.waitForLoginSuccess();

    // Add auth cookie
    await context.addCookies([
      {
        name: "auth_token",
        value: "fake-jwt-token",
        domain: "localhost",
        path: "/",
      },
    ]);

    // Reload page
    await page.reload();

    // Should still be logged in
    const isLoggedIn = await dashboardPage.isLoggedIn();
    expect(isLoggedIn).toBeTruthy();
  });
});
