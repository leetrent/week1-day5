import json
import os
import re
from dataclasses import dataclass
from typing import TypedDict
from urllib import error, request

from pydantic import ValidationError

from app.board import Board


OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-oss-120b"
DEFAULT_TIMEOUT_SECONDS = 30


class OpenRouterConfigError(ValueError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


class OpenRouterTimeoutError(TimeoutError):
    pass


class OpenRouterMessage(TypedDict):
    role: str
    content: str


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str
    chat_url: str
    timeout_seconds: int


@dataclass(frozen=True)
class BoardAssistantResult:
    model: str
    reply: str
    board: Board | None


def load_openrouter_config() -> OpenRouterConfig:
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        raise OpenRouterConfigError("OPENROUTER_API_KEY is not set.")

    model = (os.getenv("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL).strip()
    if not model:
        raise OpenRouterConfigError("OPENROUTER_MODEL cannot be empty.")

    timeout_raw = (os.getenv("OPENROUTER_TIMEOUT_SECONDS") or "").strip()
    timeout_seconds = DEFAULT_TIMEOUT_SECONDS
    if timeout_raw:
        try:
            timeout_seconds = int(timeout_raw)
        except ValueError as error_value:
            raise OpenRouterConfigError("OPENROUTER_TIMEOUT_SECONDS must be an integer.") from error_value
        if timeout_seconds <= 0:
            raise OpenRouterConfigError("OPENROUTER_TIMEOUT_SECONDS must be greater than zero.")

    return OpenRouterConfig(
        api_key=api_key,
        model=model,
        chat_url=OPENROUTER_CHAT_URL,
        timeout_seconds=timeout_seconds,
    )


def _extract_openrouter_error_message(raw_payload: bytes | None) -> str | None:
    if not raw_payload:
        return None

    try:
        payload = json.loads(raw_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    error_obj = payload.get("error")
    if isinstance(error_obj, dict):
        message = error_obj.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()

    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()

    return None


def _request_completion(messages: list[OpenRouterMessage]) -> tuple[str, str]:
    config = load_openrouter_config()
    payload = {
        "model": config.model,
        "messages": messages,
    }
    encoded_payload = json.dumps(payload).encode("utf-8")
    req = request.Request(
        config.chat_url,
        data=encoded_payload,
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            response_payload = response.read()
    except error.HTTPError as request_error:
        provider_message = _extract_openrouter_error_message(request_error.read())
        if request_error.code in (401, 403):
            message = "OpenRouter authentication failed. Check OPENROUTER_API_KEY."
            if provider_message:
                message = f"{message} Provider message: {provider_message}"
            raise OpenRouterConfigError(message) from request_error

        fallback_message = provider_message or "No additional details provided."
        raise OpenRouterRequestError(
            f"OpenRouter request failed with status {request_error.code}. {fallback_message}"
        ) from request_error
    except TimeoutError as timeout_error:
        raise OpenRouterTimeoutError("OpenRouter request timed out.") from timeout_error
    except error.URLError as network_error:
        raise OpenRouterRequestError(f"OpenRouter connection failed: {network_error.reason}") from network_error

    try:
        decoded_payload = json.loads(response_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as decode_error:
        raise OpenRouterRequestError("OpenRouter returned invalid JSON.") from decode_error

    choices = decoded_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterRequestError("OpenRouter response did not include choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise OpenRouterRequestError("OpenRouter response choice was malformed.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise OpenRouterRequestError("OpenRouter response did not include a message object.")

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return config.model, content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        if parts:
            return config.model, "\n".join(parts)

    raise OpenRouterRequestError("OpenRouter response did not include assistant content.")


def request_chat_completion(prompt: str) -> tuple[str, str]:
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise ValueError("Prompt cannot be empty.")

    return _request_completion([{"role": "user", "content": normalized_prompt}])


def _parse_json_object(content: str) -> dict[str, object]:
    candidates = [content.strip()]
    fenced_json_pattern = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
    for match in fenced_json_pattern.finditer(content):
        candidate = match.group(1).strip()
        if candidate:
            candidates.append(candidate)

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    raise OpenRouterRequestError("OpenRouter structured response was not a valid JSON object.")


def _validate_board_integrity(board: Board) -> None:
    cards_by_id = board.cards
    seen_card_ids: set[str] = set()

    for column in board.columns:
        for card_id in column.cardIds:
            if card_id not in cards_by_id:
                raise OpenRouterRequestError(
                    f"OpenRouter board update referenced missing card '{card_id}'."
                )
            if card_id in seen_card_ids:
                raise OpenRouterRequestError(
                    f"OpenRouter board update placed card '{card_id}' multiple times."
                )
            seen_card_ids.add(card_id)

    for card_key, card in cards_by_id.items():
        if card.id != card_key:
            raise OpenRouterRequestError(
                f"OpenRouter board update had mismatched card id for key '{card_key}'."
            )

    unplaced_cards = sorted(set(cards_by_id.keys()) - seen_card_ids)
    if unplaced_cards:
        raise OpenRouterRequestError(
            "OpenRouter board update left cards unplaced in columns: "
            + ", ".join(unplaced_cards[:5])
        )


def request_board_assistant_response(
    board: Board,
    user_message: str,
    conversation_history: list[OpenRouterMessage],
) -> BoardAssistantResult:
    normalized_user_message = user_message.strip()
    if not normalized_user_message:
        raise ValueError("User message cannot be empty.")

    messages: list[OpenRouterMessage] = [
        {
            "role": "system",
            "content": (
                "You are an assistant for a project-management Kanban board. "
                "Return JSON only with this exact shape: "
                '{"reply":"string","board":null|{"columns":[...],"cards":{...}}}. '
                "Set board to null when no board changes are needed. "
                "If board is provided, return the complete updated board."
            ),
        }
    ]

    for message in conversation_history:
        role = (message.get("role") or "").strip()
        content = (message.get("content") or "").strip()
        if role not in {"user", "assistant"}:
            raise ValueError("Conversation history roles must be 'user' or 'assistant'.")
        if not content:
            raise ValueError("Conversation history content cannot be empty.")
        messages.append({"role": role, "content": content})

    board_json = json.dumps(board.model_dump(mode="json"), separators=(",", ":"))
    messages.append(
        {
            "role": "user",
            "content": (
                "Current board JSON:\n"
                f"{board_json}\n\n"
                "User request:\n"
                f"{normalized_user_message}"
            ),
        }
    )

    model, raw_response = _request_completion(messages)
    payload = _parse_json_object(raw_response)

    reply_value = payload.get("reply")
    if not isinstance(reply_value, str) or not reply_value.strip():
        raise OpenRouterRequestError(
            "OpenRouter structured response must include a non-empty 'reply' string."
        )

    board_value = payload.get("board")
    parsed_board: Board | None = None
    if board_value is None:
        parsed_board = None
    elif isinstance(board_value, dict):
        try:
            parsed_board = Board.model_validate(board_value)
        except ValidationError as validation_error:
            raise OpenRouterRequestError(
                "OpenRouter board update did not match the board schema."
            ) from validation_error
        _validate_board_integrity(parsed_board)
    else:
        raise OpenRouterRequestError(
            "OpenRouter structured response field 'board' must be an object or null."
        )

    return BoardAssistantResult(model=model, reply=reply_value.strip(), board=parsed_board)
