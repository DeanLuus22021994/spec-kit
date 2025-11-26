/**
 * Environment Configuration
 * Manages different environment settings for tests
 */

export interface EnvironmentConfig {
  name: string;
  baseURL: string;
  apiURL: string;
  wsURL?: string;
  timeout: number;
  retries: number;
  parallel: boolean;
  headless: boolean;
  slowMo?: number;
  features?: {
    auth?: boolean;
    embeddings?: boolean;
    vectorSearch?: boolean;
    chat?: boolean;
  };
}

/**
 * Development environment configuration
 */
export const developmentConfig: EnvironmentConfig = {
  name: "development",
  baseURL: process.env.BASE_URL || "http://localhost:3000",
  apiURL: process.env.API_URL || "http://localhost:5000",
  wsURL: process.env.WS_URL || "ws://localhost:5000",
  timeout: 30000,
  retries: 0,
  parallel: true,
  headless: false,
  slowMo: 100,
  features: {
    auth: true,
    embeddings: true,
    vectorSearch: true,
    chat: true,
  },
};

/**
 * CI environment configuration
 */
export const ciConfig: EnvironmentConfig = {
  name: "ci",
  baseURL: process.env.BASE_URL || "http://localhost:3000",
  apiURL: process.env.API_URL || "http://localhost:5000",
  wsURL: process.env.WS_URL || "ws://localhost:5000",
  timeout: 60000,
  retries: 2,
  parallel: false,
  headless: true,
  features: {
    auth: true,
    embeddings: true,
    vectorSearch: true,
    chat: true,
  },
};

/**
 * Staging environment configuration
 */
export const stagingConfig: EnvironmentConfig = {
  name: "staging",
  baseURL: process.env.BASE_URL || "https://staging.example.com",
  apiURL: process.env.API_URL || "https://api-staging.example.com",
  wsURL: process.env.WS_URL || "wss://api-staging.example.com",
  timeout: 45000,
  retries: 2,
  parallel: true,
  headless: true,
  features: {
    auth: true,
    embeddings: true,
    vectorSearch: true,
    chat: true,
  },
};

/**
 * Production environment configuration
 */
export const productionConfig: EnvironmentConfig = {
  name: "production",
  baseURL: process.env.BASE_URL || "https://example.com",
  apiURL: process.env.API_URL || "https://api.example.com",
  wsURL: process.env.WS_URL || "wss://api.example.com",
  timeout: 45000,
  retries: 3,
  parallel: true,
  headless: true,
  features: {
    auth: true,
    embeddings: true,
    vectorSearch: true,
    chat: true,
  },
};

/**
 * Get environment configuration based on NODE_ENV
 */
export function getEnvironmentConfig(): EnvironmentConfig {
  const env = process.env.NODE_ENV || "development";

  switch (env) {
    case "ci":
      return ciConfig;
    case "staging":
      return stagingConfig;
    case "production":
      return productionConfig;
    case "development":
    default:
      return developmentConfig;
  }
}

/**
 * Check if a feature is enabled in current environment
 */
export function isFeatureEnabled(
  feature: keyof EnvironmentConfig["features"]
): boolean {
  const config = getEnvironmentConfig();
  return config.features?.[feature] ?? false;
}

/**
 * Get current environment name
 */
export function getEnvironmentName(): string {
  return getEnvironmentConfig().name;
}

/**
 * Check if running in CI environment
 */
export function isCI(): boolean {
  return !!process.env.CI || process.env.NODE_ENV === "ci";
}

/**
 * Check if running in headless mode
 */
export function isHeadless(): boolean {
  const config = getEnvironmentConfig();
  return config.headless;
}

/**
 * Get API base URL for current environment
 */
export function getApiBaseURL(): string {
  return getEnvironmentConfig().apiURL;
}

/**
 * Get frontend base URL for current environment
 */
export function getFrontendBaseURL(): string {
  return getEnvironmentConfig().baseURL;
}

/**
 * Get WebSocket URL for current environment
 */
export function getWebSocketURL(): string | undefined {
  return getEnvironmentConfig().wsURL;
}

/**
 * Get timeout for current environment
 */
export function getTimeout(): number {
  return getEnvironmentConfig().timeout;
}

/**
 * Get retry count for current environment
 */
export function getRetries(): number {
  return getEnvironmentConfig().retries;
}
