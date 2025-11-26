import { expect, test } from "@playwright/test";
import { ApiHelper } from "../../pages/ApiHelper";

test.describe("API - Health Check", () => {
  let api: ApiHelper;

  test.beforeEach(async ({ request }) => {
    api = new ApiHelper(request);
  });

  test("should return healthy status from health endpoint", async () => {
    const health = await api.healthCheck();

    expect(health.status).toBe(200);
    expect(health.healthy).toBeTruthy();
  });

  test("should have correct content-type headers", async () => {
    const response = await api.get("/health");

    expect(response.headers["content-type"]).toContain("application/json");
  });
});

test.describe("API - Semantic Kernel Completion", () => {
  let api: ApiHelper;

  test.beforeEach(async ({ request }) => {
    api = new ApiHelper(request);
  });

  test("should complete a simple prompt", async () => {
    const response = await api.completion("What is 2+2?");

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty("response");
    expect(response.data.response).toBeTruthy();
  });

  test("should handle empty prompt", async () => {
    const response = await api.completion("");

    // Should return 400 Bad Request or handle gracefully
    expect([400, 422]).toContain(response.status);
  });

  test("should handle very long prompts", async () => {
    const longPrompt = "A".repeat(5000);
    const response = await api.completion(longPrompt);

    // Should either process or return appropriate error
    expect(response.status).toBeGreaterThanOrEqual(200);
  });

  test("should return proper error for invalid requests", async () => {
    const response = await api.post("/api/semantic/completion", {
      invalidField: "test",
    });

    expect([400, 422, 500]).toContain(response.status);
  });
});

test.describe("API - Semantic Kernel Chat", () => {
  let api: ApiHelper;

  test.beforeEach(async ({ request }) => {
    api = new ApiHelper(request);
  });

  test("should start a new chat conversation", async () => {
    const response = await api.chat("Hello, how are you?");

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty("response");
    expect(response.data).toHaveProperty("conversationId");
  });

  test("should continue existing conversation", async () => {
    // Start conversation
    const firstResponse = await api.chat("My name is Alice");
    expect(firstResponse.status).toBe(200);

    const conversationId = firstResponse.data.conversationId;

    // Continue conversation
    const secondResponse = await api.chat("What is my name?", conversationId);
    expect(secondResponse.status).toBe(200);
    expect(secondResponse.data.response).toContain("Alice");
  });

  test("should handle multiple messages in sequence", async () => {
    let conversationId: string;

    // Message 1
    const response1 = await api.chat("I like pizza");
    expect(response1.status).toBe(200);
    conversationId = response1.data.conversationId;

    // Message 2
    const response2 = await api.chat("I also like pasta", conversationId);
    expect(response2.status).toBe(200);

    // Message 3 - should remember both previous messages
    const response3 = await api.chat("What foods do I like?", conversationId);
    expect(response3.status).toBe(200);
    expect(response3.data.response).toMatch(/pizza|pasta/i);
  });
});

test.describe("API - Embeddings", () => {
  let api: ApiHelper;

  test.beforeEach(async ({ request }) => {
    api = new ApiHelper(request);
  });

  test("should generate embeddings for text", async () => {
    const response = await api.getEmbeddings("This is a test sentence");

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty("embedding");
    expect(Array.isArray(response.data.embedding)).toBeTruthy();
    expect(response.data.embedding.length).toBeGreaterThan(0);
  });

  test("should handle empty text for embeddings", async () => {
    const response = await api.getEmbeddings("");

    // Should return error or empty embedding
    expect([200, 400, 422]).toContain(response.status);
  });

  test("should generate consistent embeddings for same text", async () => {
    const text = "Consistent test text";

    const response1 = await api.getEmbeddings(text);
    const response2 = await api.getEmbeddings(text);

    expect(response1.status).toBe(200);
    expect(response2.status).toBe(200);

    // Embeddings should be identical for same input
    expect(response1.data.embedding).toEqual(response2.data.embedding);
  });
});

test.describe("API - Vector Search", () => {
  let api: ApiHelper;

  test.beforeEach(async ({ request }) => {
    api = new ApiHelper(request);
  });

  test("should perform vector search", async () => {
    const response = await api.vectorSearch("artificial intelligence", 5);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty("results");
    expect(Array.isArray(response.data.results)).toBeTruthy();
  });

  test("should respect topK parameter", async () => {
    const topK = 3;
    const response = await api.vectorSearch("machine learning", topK);

    expect(response.status).toBe(200);
    expect(response.data.results.length).toBeLessThanOrEqual(topK);
  });

  test("should handle search with no results", async () => {
    const response = await api.vectorSearch("xyzabc123nonexistent");

    expect(response.status).toBe(200);
    expect(response.data.results).toHaveLength(0);
  });
});

test.describe("API - Error Handling", () => {
  let api: ApiHelper;

  test.beforeEach(async ({ request }) => {
    api = new ApiHelper(request);
  });

  test("should return 404 for non-existent endpoints", async () => {
    const response = await api.get("/api/nonexistent");

    expect(response.status).toBe(404);
  });

  test("should handle malformed JSON", async ({ request }) => {
    const response = await request.post(
      `${api.baseURL}/api/semantic/completion`,
      {
        data: "not valid json",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    expect([400, 422]).toContain(response.status());
  });

  test("should handle missing required fields", async () => {
    const response = await api.post("/api/semantic/completion", {});

    expect([400, 422]).toContain(response.status);
  });

  test("should return proper error messages", async () => {
    const response = await api.post("/api/semantic/completion", {
      invalidField: "test",
    });

    expect(response.data).toHaveProperty("error");
    expect(typeof response.data.error).toBe("string");
  });
});

test.describe("API - Performance", () => {
  let api: ApiHelper;

  test.beforeEach(async ({ request }) => {
    api = new ApiHelper(request);
  });

  test("should respond to health check within acceptable time", async () => {
    const startTime = Date.now();
    await api.healthCheck();
    const endTime = Date.now();

    const responseTime = endTime - startTime;
    expect(responseTime).toBeLessThan(1000); // Less than 1 second
  });

  test("should handle concurrent requests", async () => {
    const promises = Array(10)
      .fill(null)
      .map(() => api.completion("Test prompt"));

    const responses = await Promise.all(promises);

    responses.forEach((response) => {
      expect(response.status).toBe(200);
    });
  });
});
