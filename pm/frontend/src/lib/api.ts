import type { BoardData } from "@/lib/kanban";

type BoardApiPayload = {
  username: string;
  board: BoardData;
  version: number;
  updated_at: string;
};

export type AiConversationMessage = {
  role: "user" | "assistant";
  content: string;
};

type AiBoardApiPayload = {
  username: string;
  model: string;
  reply: string;
  board_updated: boolean;
  board: BoardData;
  version: number;
  updated_at: string;
};

const assertBoardPayload = (payload: unknown): BoardApiPayload => {
  if (
    !payload ||
    typeof payload !== "object" ||
    !("board" in payload) ||
    !("username" in payload) ||
    !("version" in payload) ||
    !("updated_at" in payload)
  ) {
    throw new Error("Invalid board API response.");
  }
  return payload as BoardApiPayload;
};

const assertAiBoardPayload = (payload: unknown): AiBoardApiPayload => {
  if (
    !payload ||
    typeof payload !== "object" ||
    !("username" in payload) ||
    !("model" in payload) ||
    !("reply" in payload) ||
    !("board_updated" in payload) ||
    !("board" in payload) ||
    !("version" in payload) ||
    !("updated_at" in payload)
  ) {
    throw new Error("Invalid AI board API response.");
  }
  return payload as AiBoardApiPayload;
};

export const fetchBoard = async (username: string): Promise<BoardApiPayload> => {
  const response = await fetch(`/api/board/${encodeURIComponent(username)}`);
  if (!response.ok) {
    throw new Error(`Board fetch failed with status ${response.status}`);
  }
  const payload: unknown = await response.json();
  return assertBoardPayload(payload);
};

export const sendAiBoardMessage = async (
  username: string,
  message: string,
  conversation: AiConversationMessage[]
): Promise<AiBoardApiPayload> => {
  const response = await fetch(`/api/ai/board/${encodeURIComponent(username)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation }),
  });
  if (!response.ok) {
    throw new Error(`AI board request failed with status ${response.status}`);
  }
  const payload: unknown = await response.json();
  return assertAiBoardPayload(payload);
};

export const saveBoard = async (
  username: string,
  board: BoardData
): Promise<BoardApiPayload> => {
  const response = await fetch(`/api/board/${encodeURIComponent(username)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ board }),
  });
  if (!response.ok) {
    throw new Error(`Board save failed with status ${response.status}`);
  }
  const payload: unknown = await response.json();
  return assertBoardPayload(payload);
};
