import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";

describe("AuthGate", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it("shows login form before authentication", async () => {
    render(<AuthGate />);
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("rejects invalid credentials", async () => {
    render(<AuthGate />);
    await screen.findByRole("heading", { name: "Sign in" });

    await userEvent.type(screen.getByLabelText("Username"), "wrong");
    await userEvent.type(screen.getByLabelText("Password"), "creds");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText("Invalid credentials. Use user / password.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("shows board with valid credentials", async () => {
    render(<AuthGate />);
    await screen.findByRole("heading", { name: "Sign in" });

    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
  });

  it("returns to login after logout", async () => {
    render(<AuthGate />);
    await screen.findByRole("heading", { name: "Sign in" });

    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    await screen.findByRole("heading", { name: "Kanban Studio" });

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });
});
