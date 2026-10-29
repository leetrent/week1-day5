import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

const installApiMock = (
  aiResponse?: {
    reply: string;
    board_updated: boolean;
    board: BoardData;
  },
  failures: { load?: number; save?: number; ai?: number } = {}
) => {
  let board = clone(initialData);
  let version = 1;
  const remainingFailures = { load: 0, save: 0, ai: 0, ...failures };

  const shouldFail = (kind: keyof typeof remainingFailures) => {
    if (remainingFailures[kind] > 0) {
      remainingFailures[kind] -= 1;
      return true;
    }
    return false;
  };

  return vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = init?.method ?? "GET";

    if (url.includes("/api/board/user") && method === "GET" && shouldFail("load")) {
      return new Response("Server error", { status: 500 });
    }
    if (url.includes("/api/board/user") && method === "PUT" && shouldFail("save")) {
      return new Response("Server error", { status: 500 });
    }
    if (url.includes("/api/ai/board/user") && method === "POST" && shouldFail("ai")) {
      return new Response("Server error", { status: 500 });
    }

    if (url.includes("/api/board/user") && method === "GET") {
      return new Response(
        JSON.stringify({
          username: "user",
          board,
          version,
          updated_at: "2026-10-26 00:00:00",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    if (url.includes("/api/board/user") && method === "PUT" && init?.body) {
      const payload = JSON.parse(String(init.body)) as { board: BoardData };
      board = clone(payload.board);
      version += 1;
      return new Response(
        JSON.stringify({
          username: "user",
          board,
          version,
          updated_at: "2026-10-26 00:00:00",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    if (url.includes("/api/ai/board/user") && method === "POST") {
      const payload = aiResponse ?? {
        reply: "No changes needed.",
        board_updated: false,
        board,
      };
      if (payload.board_updated) {
        board = clone(payload.board);
        version += 1;
      }
      return new Response(
        JSON.stringify({
          username: "user",
          model: "openai/gpt-oss-120b",
          reply: payload.reply,
          board_updated: payload.board_updated,
          board,
          version,
          updated_at: "2026-10-26 00:00:00",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response("Not found", { status: 404 });
  });
};

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders five columns", () => {
    render(<KanbanBoard />);
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("opens chat and shows AI response without board update", async () => {
    installApiMock({
      reply: "No board changes required.",
      board_updated: false,
      board: clone(initialData),
    });

    render(<KanbanBoard username="user" />);
    await screen.findByRole("heading", { name: "Kanban Studio" });

    await userEvent.click(screen.getByRole("button", { name: /hide ai chat/i }));
    expect(screen.queryByRole("heading", { name: "AI Assistant" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /open ai chat/i }));
    expect(screen.getByRole("heading", { name: "AI Assistant" })).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Message AI assistant"), "What is 2+2?");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("No board changes required.")).toBeInTheDocument();
    expect(screen.getByText("What is 2+2?")).toBeInTheDocument();
  });

  it("applies AI board updates returned from backend", async () => {
    const updated = clone(initialData);
    updated.columns[0].title = "AI Updated Backlog";
    installApiMock({
      reply: "Updated the first column.",
      board_updated: true,
      board: updated,
    });

    render(<KanbanBoard username="user" />);
    await screen.findByRole("heading", { name: "Kanban Studio" });

    await userEvent.type(
      screen.getByLabelText("Message AI assistant"),
      "Rename the first column to AI Updated Backlog"
    );
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Updated the first column.")).toBeInTheDocument();
    const firstColumnInput = within(getFirstColumn()).getByLabelText("Column title");
    expect(firstColumnInput).toHaveValue("AI Updated Backlog");
  });

  it("shows an error and keeps the local board when loading fails", async () => {
    installApiMock(undefined, { load: 1 });

    render(<KanbanBoard username="user" />);

    expect(
      await screen.findByText("Unable to load saved board. Showing local board state.")
    ).toBeInTheDocument();
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("shows an error when saving fails and clears it after a successful retry", async () => {
    installApiMock(undefined, { save: 1 });

    render(<KanbanBoard username="user" />);
    await screen.findByText("Synced");

    const input = within(getFirstColumn()).getByLabelText("Column title");
    await userEvent.type(input, "!");
    expect(
      await screen.findByText("Unable to save board changes. Please retry your action.")
    ).toBeInTheDocument();
    expect(input).toHaveValue("Backlog!");

    await userEvent.type(input, "!");
    await waitFor(() =>
      expect(
        screen.queryByText("Unable to save board changes. Please retry your action.")
      ).not.toBeInTheDocument()
    );
    expect(input).toHaveValue("Backlog!!");
  });

  it("shows a chat error when the AI request fails and leaves the board unchanged", async () => {
    installApiMock(undefined, { ai: 1 });

    render(<KanbanBoard username="user" />);
    await screen.findByText("Synced");

    await userEvent.type(screen.getByLabelText("Message AI assistant"), "Rename the first column");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(
      await screen.findByText("Unable to get an AI response right now. Please retry.")
    ).toBeInTheDocument();
    expect(screen.getByText("Rename the first column")).toBeInTheDocument();
    expect(within(getFirstColumn()).getByLabelText("Column title")).toHaveValue("Backlog");
  });
});
