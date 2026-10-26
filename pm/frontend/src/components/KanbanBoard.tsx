"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { fetchBoard, saveBoard, sendAiBoardMessage, type AiConversationMessage } from "@/lib/api";
import { createId, initialData, moveCard, type BoardData } from "@/lib/kanban";

type KanbanBoardProps = {
  username?: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export const KanbanBoard = ({ username }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const boardRef = useRef(board);
  const chatBodyRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    boardRef.current = board;
  }, [board]);

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [chatMessages, isAiLoading]);

  useEffect(() => {
    if (!username) {
      return;
    }

    const loadBoard = async () => {
      setIsSyncing(true);
      setSyncError(null);
      try {
        const payload = await fetchBoard(username);
        setBoard(payload.board);
      } catch {
        setSyncError("Unable to load saved board. Showing local board state.");
      } finally {
        setIsSyncing(false);
      }
    };

    void loadBoard();
  }, [username]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board.cards, [board.cards]);

  const persistBoard = async (nextBoard: BoardData) => {
    if (!username) {
      return;
    }
    setIsSyncing(true);
    setSyncError(null);
    try {
      const payload = await saveBoard(username, nextBoard);
      setBoard(payload.board);
    } catch {
      setSyncError("Unable to save board changes. Please retry your action.");
    } finally {
      setIsSyncing(false);
    }
  };

  const applyBoardUpdate = (updater: (current: BoardData) => BoardData) => {
    const current = boardRef.current;
    const next = updater(current);
    setBoard(next);
    boardRef.current = next;
    void persistBoard(next);
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    applyBoardUpdate((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    applyBoardUpdate((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    applyBoardUpdate((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    applyBoardUpdate((prev) => {
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
  };

  const handleSendMessage = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const message = chatInput.trim();
    if (!message) {
      return;
    }
    if (!username) {
      setChatError("AI chat requires a signed-in user.");
      return;
    }

    const history: AiConversationMessage[] = chatMessages.map((entry) => ({
      role: entry.role,
      content: entry.content,
    }));

    setChatMessages((current) => [...current, { role: "user", content: message }]);
    setChatInput("");
    setChatError(null);
    setIsAiLoading(true);

    try {
      const payload = await sendAiBoardMessage(username, message, history);
      setChatMessages((current) => [...current, { role: "assistant", content: payload.reply }]);
      if (payload.board_updated) {
        setBoard(payload.board);
        boardRef.current = payload.board;
      }
    } catch {
      setChatError("Unable to get an AI response right now. Please retry.");
    } finally {
      setIsAiLoading(false);
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
              <button
                type="button"
                onClick={() => setIsChatOpen((current) => !current)}
                className="mt-4 w-full rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
              >
                {isChatOpen ? "Hide AI chat" : "Open AI chat"}
              </button>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {username ? (
              <div className="rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                {isSyncing ? "Syncing..." : "Synced"}
              </div>
            ) : null}
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
          {syncError ? (
            <p className="text-sm font-semibold text-[var(--secondary-purple)]">{syncError}</p>
          ) : null}
        </header>

        <div className={`grid gap-6 ${isChatOpen ? "xl:grid-cols-[minmax(0,1fr)_360px]" : ""}`}>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <section className="grid gap-6 lg:grid-cols-5">
              {board.columns.map((column) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  cards={column.cardIds.map((cardId) => board.cards[cardId])}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                />
              ))}
            </section>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          {isChatOpen ? (
            <aside className="flex min-h-[520px] flex-col rounded-3xl border border-[var(--stroke)] bg-white p-4 shadow-[var(--shadow)]">
              <div className="border-b border-[var(--stroke)] px-2 pb-3">
                <h2 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
                  AI Assistant
                </h2>
                <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
                  Ask to create, edit, or move cards across the board.
                </p>
              </div>

              <div
                ref={chatBodyRef}
                className="mt-4 flex-1 space-y-3 overflow-y-auto px-1"
                data-testid="ai-chat-messages"
              >
                {chatMessages.length === 0 ? (
                  <p className="rounded-2xl border border-dashed border-[var(--stroke)] px-4 py-3 text-sm text-[var(--gray-text)]">
                    Start a conversation to update your board with AI.
                  </p>
                ) : null}
                {chatMessages.map((entry, index) => (
                  <div
                    key={`${entry.role}-${index}`}
                    className={`flex ${entry.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                        entry.role === "user"
                          ? "bg-[var(--primary-blue)] text-white"
                          : "border border-[var(--stroke)] bg-[var(--surface)] text-[var(--navy-dark)]"
                      }`}
                    >
                      {entry.content}
                    </div>
                  </div>
                ))}
                {isAiLoading ? (
                  <p className="text-sm font-semibold text-[var(--gray-text)]">AI is thinking...</p>
                ) : null}
              </div>

              <form onSubmit={handleSendMessage} className="mt-4 space-y-3 border-t border-[var(--stroke)] pt-4">
                <textarea
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  aria-label="Message AI assistant"
                  placeholder="Ask AI to update your board..."
                  rows={3}
                  className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                />
                {chatError ? (
                  <p className="text-sm font-semibold text-[var(--secondary-purple)]">{chatError}</p>
                ) : null}
                <button
                  type="submit"
                  disabled={isAiLoading || !chatInput.trim()}
                  className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Send
                </button>
              </form>
            </aside>
          ) : null}
        </div>
      </main>
    </div>
  );
};
