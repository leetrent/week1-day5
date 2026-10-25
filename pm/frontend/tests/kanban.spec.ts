import { expect, test, type Page } from "@playwright/test";
import { initialData } from "../src/lib/kanban";

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

const installBoardApiMock = async (page: Page) => {
  let boardState = clone(initialData);
  let version = 1;

  await page.route("**/api/board/user", async (route, request) => {
    if (request.method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          username: "user",
          board: boardState,
          version,
          updated_at: "2026-10-24 00:00:00",
        }),
      });
      return;
    }

    if (request.method() === "PUT") {
      const body = request.postDataJSON() as { board: typeof initialData };
      boardState = clone(body.board);
      version += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          username: "user",
          board: boardState,
          version,
          updated_at: "2026-10-24 00:00:00",
        }),
      });
      return;
    }

    await route.fallback();
  });
};

const signIn = async (page: Page, options?: { installApiMock?: boolean }) => {
  if (options?.installApiMock ?? true) {
    await installBoardApiMock(page);
  }
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("loads the kanban board", async ({ page }) => {
  await signIn(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("rejects invalid login and supports logout", async ({ page }) => {
  await installBoardApiMock(page);
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: /sign in/i }).click();

  await expect(page.getByText("Invalid credentials. Use user / password.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).not.toBeVisible();

  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();

  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("keeps board changes after refresh via API persistence", async ({ page }) => {
  await installBoardApiMock(page);
  await signIn(page, { installApiMock: false });

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const titleInput = firstColumn.getByLabel("Column title");
  await titleInput.fill("Persisted Title");

  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();

  await expect(page.locator('[data-testid^="column-"]').first().getByLabel("Column title")).toHaveValue(
    "Persisted Title"
  );
});
