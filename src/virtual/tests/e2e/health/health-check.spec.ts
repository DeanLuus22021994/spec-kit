import { expect, test } from "@playwright/test";

test.describe("Health Check Tests", () => {
  test("frontend health endpoint returns 200", async ({ request }) => {
    const response = await request.get("/health");
    expect(response.ok()).toBeTruthy();
  });

  test("backend API health endpoint returns 200", async ({ request }) => {
    const response = await request.get("http://localhost:5000/health");
    expect(response.ok()).toBeTruthy();
  });

  test("gateway health endpoint returns 200", async ({ request }) => {
    const response = await request.get("http://localhost:8080/health");
    expect(response.ok()).toBeTruthy();
  });
});
