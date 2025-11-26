/**
 * Test Fixtures
 * Provides reusable test data and setup/teardown functions
 */

export const testUsers = {
  validUser: {
    email: "test@example.com",
    password: "password123",
    name: "Test User",
    id: 1,
  },
  adminUser: {
    email: "admin@example.com",
    password: "admin123",
    name: "Admin User",
    id: 2,
    role: "admin",
  },
  invalidUser: {
    email: "invalid@example.com",
    password: "wrongpassword",
  },
};

export const mockTokens = {
  validToken:
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  expiredToken:
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImV4cCI6MTUxNjIzOTAyMn0.abc123",
};

export const testPrompts = {
  simple: "What is 2+2?",
  complex: "Explain the concept of quantum computing in simple terms",
  longPrompt: "A".repeat(1000) + " What is artificial intelligence?",
  emptyPrompt: "",
  specialChars: 'What is <script>alert("test")</script>?',
  multiline: `This is a
    multiline
    prompt for testing`,
};

export const mockApiResponses = {
  successfulCompletion: {
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      response: "This is a successful completion response",
      success: true,
      timestamp: new Date().toISOString(),
    }),
  },

  errorResponse: {
    status: 500,
    contentType: "application/json",
    body: JSON.stringify({
      error: "Internal server error",
      success: false,
    }),
  },

  timeoutResponse: {
    status: 408,
    contentType: "application/json",
    body: JSON.stringify({
      error: "Request timeout",
      success: false,
    }),
  },

  unauthorizedResponse: {
    status: 401,
    contentType: "application/json",
    body: JSON.stringify({
      error: "Unauthorized",
      success: false,
    }),
  },

  validationErrorResponse: {
    status: 422,
    contentType: "application/json",
    body: JSON.stringify({
      error: "Validation failed",
      errors: {
        prompt: "Prompt is required",
      },
      success: false,
    }),
  },
};

export const mockEmbeddings = {
  sampleEmbedding: Array(1536)
    .fill(0)
    .map(() => Math.random()),

  shortTextEmbedding: {
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      embedding: Array(1536)
        .fill(0)
        .map(() => Math.random()),
      dimensions: 1536,
      model: "text-embedding-3-small",
    }),
  },
};

export const mockConversations = {
  singleTurnConversation: {
    conversationId: "conv-123",
    messages: [
      { role: "user", content: "Hello" },
      { role: "assistant", content: "Hi there!" },
    ],
  },

  multiTurnConversation: {
    conversationId: "conv-456",
    messages: [
      { role: "user", content: "My name is Alice" },
      { role: "assistant", content: "Nice to meet you, Alice!" },
      { role: "user", content: "What is my name?" },
      { role: "assistant", content: "Your name is Alice." },
    ],
  },
};

export const testEnvironments = {
  development: {
    baseURL: "http://localhost:3000",
    apiURL: "http://localhost:5000",
  },

  staging: {
    baseURL: "https://staging.example.com",
    apiURL: "https://api-staging.example.com",
  },

  production: {
    baseURL: "https://example.com",
    apiURL: "https://api.example.com",
  },
};

/**
 * Generate a random conversation ID
 */
export function generateConversationId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Generate a random user ID
 */
export function generateUserId(): number {
  return Math.floor(Math.random() * 10000) + 1;
}

/**
 * Create a mock JWT token
 */
export function createMockToken(
  userId: number,
  expiresIn: number = 3600
): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = btoa(
    JSON.stringify({
      sub: userId.toString(),
      name: "Test User",
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + expiresIn,
    })
  );
  const signature = "mock-signature";

  return `${header}.${payload}.${signature}`;
}

/**
 * Wait for a specified duration
 */
export async function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry a function until it succeeds or max retries reached
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (i < maxRetries - 1) {
        await wait(delay);
      }
    }
  }

  throw lastError!;
}
