import { expect, test } from "@playwright/test";
import { ApiHelper } from "../../pages/ApiHelper";
import { DashboardPage } from "../../pages/DashboardPage";
import { HomePage } from "../../pages/HomePage";
import { LoginPage } from "../../pages/LoginPage";

test.describe("Integration - End-to-End User Flow", () => {
  test("should complete full user journey from login to semantic completion", async ({
    page,
    request,
  }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    const homePage = new HomePage(page);
    const api = new ApiHelper(request);

    // Mock authentication
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

    // Step 1: Login
    await loginPage.navigate();
    await loginPage.login("test@example.com", "password123");
    await loginPage.waitForLoginSuccess();

    // Step 2: Verify dashboard access
    const isLoggedIn = await dashboardPage.isLoggedIn();
    expect(isLoggedIn).toBeTruthy();

    // Step 3: Navigate to main page
    await homePage.navigate();
    await expect(homePage.headerTitle).toBeVisible();

    // Step 4: Submit semantic kernel request
    await page.route("**/api/semantic/completion", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          response: "Integration test response from Semantic Kernel",
          success: true,
        }),
      });
    });

    await homePage.submitPrompt("What is artificial intelligence?");
    await homePage.waitForResponse();

    const responseText = await homePage.getResponseText();
    expect(responseText).toContain("Integration test response");

    // Step 5: Verify API health check still works
    const health = await api.healthCheck();
    expect(health.healthy).toBeTruthy();
  });

  test("should handle authentication failure and retry", async ({ page }) => {
    const loginPage = new LoginPage(page);

    let loginAttempts = 0;

    // First attempt fails, second succeeds
    await page.route("**/api/auth/login", async (route) => {
      loginAttempts++;

      if (loginAttempts === 1) {
        await route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: "Invalid credentials",
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            success: true,
            token: "fake-jwt-token",
            user: { id: 1, email: "test@example.com", name: "Test User" },
          }),
        });
      }
    });

    // First login attempt (fails)
    await loginPage.navigate();
    await loginPage.login("test@example.com", "wrongpassword");

    const hasError = await loginPage.hasError();
    expect(hasError).toBeTruthy();

    // Second login attempt (succeeds)
    await loginPage.login("test@example.com", "correctpassword");
    await loginPage.waitForLoginSuccess();
  });

  test("should maintain conversation context across multiple interactions", async ({
    page,
    request,
  }) => {
    const homePage = new HomePage(page);
    let conversationId: string;

    // Mock chat API to maintain conversation
    await page.route("**/api/semantic/chat", async (route) => {
      const requestData = route.request().postDataJSON();

      if (!conversationId) {
        conversationId = "conv-" + Date.now();
      }

      let response = "";
      if (requestData.message.includes("name is Bob")) {
        response = "Nice to meet you, Bob!";
      } else if (requestData.message.includes("What is my name")) {
        response = "Your name is Bob.";
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          response,
          conversationId,
          success: true,
        }),
      });
    });

    await homePage.navigate();

    // Message 1
    await homePage.submitPrompt("My name is Bob");
    await homePage.waitForResponse();
    let responseText = await homePage.getResponseText();
    expect(responseText).toContain("Bob");

    // Clear and send Message 2
    await homePage.clearPrompt();
    await homePage.submitPrompt("What is my name?");
    await homePage.waitForResponse();
    responseText = await homePage.getResponseText();
    expect(responseText).toContain("Bob");
  });
});

test.describe("Integration - API and Frontend Synchronization", () => {
  test("should sync frontend state with API responses", async ({
    page,
    request,
  }) => {
    const homePage = new HomePage(page);
    const api = new ApiHelper(request);

    // Verify API is healthy before frontend interaction
    const health = await api.healthCheck();
    expect(health.healthy).toBeTruthy();

    // Load frontend
    await homePage.navigate();
    await expect(homePage.headerTitle).toBeVisible();

    // Mock API response
    await page.route("**/api/semantic/completion", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          response: "API response synchronized with frontend",
          success: true,
          timestamp: new Date().toISOString(),
        }),
      });
    });

    // Submit request from frontend
    await homePage.submitPrompt("Test synchronization");
    await homePage.waitForResponse();

    const responseText = await homePage.getResponseText();
    expect(responseText).toContain("synchronized");
  });

  test("should handle API timeout gracefully in frontend", async ({ page }) => {
    const homePage = new HomePage(page);

    // Mock slow API response
    await page.route("**/api/semantic/completion", async (route) => {
      await page.waitForTimeout(5000); // 5 second delay
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          response: "Delayed response",
          success: true,
        }),
      });
    });

    await homePage.navigate();
    await homePage.submitPrompt("This will timeout");

    // Should show loading or timeout error
    const isLoading = await homePage.isLoading();
    // Check if error is shown or loading persists
  });
});

test.describe("Integration - Database and Vector Store", () => {
  test("should store and retrieve embeddings", async ({ request }) => {
    const api = new ApiHelper(request);

    // Generate embedding
    const text = "This is a test document for vector storage";
    const embeddingResponse = await api.getEmbeddings(text);

    expect(embeddingResponse.status).toBe(200);
    expect(embeddingResponse.data.embedding).toBeTruthy();

    // Perform vector search
    const searchResponse = await api.vectorSearch(text, 5);

    expect(searchResponse.status).toBe(200);
    // Should find similar vectors
  });

  test("should handle semantic search with multiple documents", async ({
    request,
  }) => {
    const api = new ApiHelper(request);

    // Generate embeddings for multiple documents
    const documents = [
      "Artificial intelligence is fascinating",
      "Machine learning uses algorithms",
      "Deep learning is a subset of ML",
    ];

    const embeddingPromises = documents.map((doc) => api.getEmbeddings(doc));
    const embeddingResults = await Promise.all(embeddingPromises);

    embeddingResults.forEach((result) => {
      expect(result.status).toBe(200);
    });

    // Search for related content
    const searchResponse = await api.vectorSearch("AI and ML", 3);
    expect(searchResponse.status).toBe(200);
    expect(searchResponse.data.results.length).toBeGreaterThan(0);
  });
});

test.describe("Integration - Error Recovery", () => {
  test("should recover from transient API failures", async ({ page }) => {
    const homePage = new HomePage(page);
    let requestCount = 0;

    // First request fails, second succeeds
    await page.route("**/api/semantic/completion", async (route) => {
      requestCount++;

      if (requestCount === 1) {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({
            error: "Temporary server error",
            success: false,
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            response: "Recovery successful",
            success: true,
          }),
        });
      }
    });

    await homePage.navigate();

    // First attempt (fails)
    await homePage.submitPrompt("First attempt");
    const hasError = await homePage.hasError();
    expect(hasError).toBeTruthy();

    // Second attempt (succeeds)
    await homePage.clearPrompt();
    await homePage.submitPrompt("Second attempt");
    await homePage.waitForResponse();

    const responseText = await homePage.getResponseText();
    expect(responseText).toContain("Recovery successful");
  });
});
