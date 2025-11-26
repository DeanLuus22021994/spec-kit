import { Page, Locator } from "@playwright/test";

export class DashboardPage {
  readonly page: Page;
  readonly logoutButton: Locator;
  readonly welcomeMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.logoutButton = page.getByRole("button", { name: "Logout" });
    this.welcomeMessage = page.locator(".welcome-message");
  }

  async isLoggedIn(): Promise<boolean> {
    try {
      await this.logoutButton.waitFor({ state: "visible", timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  async logout(): Promise<void> {
    await this.logoutButton.click();
  }
}
