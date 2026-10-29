"use client";

import { FormEvent, useState, useSyncExternalStore } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const AUTH_STORAGE_KEY = "pm.authenticated";
const AUTH_USERNAME_KEY = "pm.username";
const VALID_USERNAME = "user";
const VALID_PASSWORD = "password";

const sessionListeners = new Set<() => void>();

const subscribeSession = (listener: () => void) => {
  sessionListeners.add(listener);
  return () => {
    sessionListeners.delete(listener);
  };
};

const getSessionUsername = () =>
  window.sessionStorage.getItem(AUTH_STORAGE_KEY) === "true"
    ? window.sessionStorage.getItem(AUTH_USERNAME_KEY) || VALID_USERNAME
    : null;

const getServerSessionUsername = () => null;

const setSessionUsername = (username: string | null) => {
  if (username) {
    window.sessionStorage.setItem(AUTH_STORAGE_KEY, "true");
    window.sessionStorage.setItem(AUTH_USERNAME_KEY, username);
  } else {
    window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
    window.sessionStorage.removeItem(AUTH_USERNAME_KEY);
  }
  sessionListeners.forEach((listener) => listener());
};

export const AuthGate = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const activeUsername = useSyncExternalStore(
    subscribeSession,
    getSessionUsername,
    getServerSessionUsername
  );

  const handleLogin = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (username === VALID_USERNAME && password === VALID_PASSWORD) {
      setSessionUsername(username);
      setError(null);
      setPassword("");
      return;
    }

    setError("Invalid credentials. Use user / password.");
  };

  const handleLogout = () => {
    setSessionUsername(null);
    setUsername("");
    setPassword("");
    setError(null);
  };

  if (!activeUsername) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center px-6">
        <section className="w-full rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            Project Management MVP
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Sign in
          </h1>
          <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
            Use the MVP credentials to access the Kanban board.
          </p>
          <form onSubmit={handleLogin} className="mt-6 space-y-4">
            <div>
              <label
                htmlFor="username"
                className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
              >
                Username
              </label>
              <input
                id="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
                required
              />
            </div>
            {error ? (
              <p className="text-sm font-semibold text-[var(--secondary-purple)]">{error}</p>
            ) : null}
            <button
              type="submit"
              className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
            >
              Sign in
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <div>
      <div className="sticky top-0 z-20 border-b border-[var(--stroke)] bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between px-6 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Signed in as {activeUsername}
          </p>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
          >
            Log out
          </button>
        </div>
      </div>
      <KanbanBoard username={activeUsername} />
    </div>
  );
};
