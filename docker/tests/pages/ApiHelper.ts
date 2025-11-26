import { APIRequestContext } from "@playwright/test";

export class ApiHelper {
  readonly request: APIRequestContext;
  readonly baseURL: string;

  constructor(request: APIRequestContext) {
    this.request = request;
    this.baseURL = process.env.BASE_URL || "http://localhost:3000";
  }

  async healthCheck() {
    const response = await this.request.get(`${this.baseURL}/health`);
    return {
      status: response.status(),
      healthy: response.ok(),
    };
  }

  async get(endpoint: string) {
    const response = await this.request.get(`${this.baseURL}${endpoint}`);
    return {
      status: response.status(),
      headers: response.headers(),
      data: await response.json().catch(() => ({})),
    };
  }

  async post(endpoint: string, data: any) {
    const response = await this.request.post(`${this.baseURL}${endpoint}`, {
      data,
    });
    return {
      status: response.status(),
      data: await response.json().catch(() => ({})),
    };
  }

  async completion(prompt: string) {
    return this.post("/api/semantic/completion", { prompt });
  }

  async chat(message: string, conversationId?: string) {
    return this.post("/api/semantic/chat", { message, conversationId });
  }

  async getEmbeddings(text: string) {
    return this.post("/api/semantic/embeddings", { text });
  }

  async vectorSearch(query: string, topK: number = 3) {
    return this.post("/api/semantic/search", { query, topK });
  }
}
