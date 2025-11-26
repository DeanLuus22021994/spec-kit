import { Page, Locator } from "@playwright/test";

export class HomePage {
  readonly page: Page;
  readonly promptInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly headerTitle: Locator;
  readonly responseContainer: Locator;
  readonly loadingIndicator: Locator;

  constructor(page: Page) {
    this.page = page;
    this.promptInput = page.locator('textarea[name="prompt"]');
    this.submitButton = page.getByRole("button", { name: "Submit" });
    this.errorMessage = page.locator(".error-message");
    this.headerTitle = page.locator("h1");
    this.responseContainer = page.locator(".response-container");
    this.loadingIndicator = page.locator(".loading");
  }

  async navigate() {
    await this.page.goto("/");
  }

  async getTitle(): Promise<string> {
    return await this.page.title();
  }

  async getHeaderText(): Promise<string> {
    return await this.headerTitle.innerText();
  }

  async isSubmitEnabled(): Promise<boolean> {
    return await this.submitButton.isEnabled();
  }

  async clearPrompt() {
    await this.promptInput.clear();
  }

  async submitPrompt(text: string) {
    await this.promptInput.fill(text);
    await this.submitButton.click();
  }

  async isLoading(): Promise<boolean> {
    return await this.loadingIndicator.isVisible();
  }

  async waitForResponse() {
    await this.responseContainer.waitFor({ state: "visible" });
  }

  async getResponseText(): Promise<string> {
    return await this.responseContainer.innerText();
  }

  async hasError(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  async getErrorText(): Promise<string> {
    return await this.errorMessage.innerText();
  }
}
