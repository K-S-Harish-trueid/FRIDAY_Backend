import json
from groq import AsyncGroq
from config import settings
from models.chat import ChatMessage
from services import tool_service

_SYSTEM_PROMPT = (
    "You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth. "
    "You are sharp, efficient, and concise. Occasionally address the user as 'boss'. "
    "Use the available tools when the user asks for live information (weather, web "
    "search) or a device action (opening maps, checking their location) — otherwise "
    "just reply directly. If the user asks for weather or other location-dependent "
    "info without naming a place, call get_current_location instead of asking them "
    "in plain text or suggesting outside websites — the app itself will prompt the "
    "user to share their location or type it in, so just call the tool."
)

_MODEL = "llama-3.3-70b-versatile"
_client = AsyncGroq(api_key=settings.groq_api_key, timeout=30.0)


async def complete(messages: list[ChatMessage]) -> str:
    """Plain completion, no tools — used as the simple text-only path."""
    result = await _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "system", "content": _SYSTEM_PROMPT}]
        + [{"role": m.role, "content": m.content} for m in messages],
    )
    return result.choices[0].message.content


async def complete_with_tools(messages: list[ChatMessage]) -> tuple[str, dict | None]:
    """Runs the Groq tool-calling agent loop.

    Returns (reply_text, action). `action` is a dict for Flutter to execute
    (open_maps / get_location) or None for a plain text reply.
    """
    chat_messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}] + [
        {"role": m.role, "content": m.content} for m in messages
    ]

    try:
        result = await _client.chat.completions.create(
            model=_MODEL,
            messages=chat_messages,
            tools=tool_service.TOOLS,
            tool_choice="auto",
        )
        message = result.choices[0].message
    except Exception:
        # Anything from a malformed tool-call grammar (BadRequestError) to a
        # transient network/timeout blip on this specific call — degrade to
        # a plain completion rather than failing the whole turn. Falling
        # all the way through to the Gemini fallback isn't useful here
        # anyway since Gemini has no tool support.
        return await complete(messages), None

    if not message.tool_calls:
        return message.content, None

    chat_messages.append(
        {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        }
    )

    try:
        action = None
        for tc in message.tool_calls:
            args = json.loads(tc.function.arguments or "{}")

            if tc.function.name in tool_service.DEVICE_ACTION_TOOLS:
                if action is None:
                    action = tool_service.build_action(tc.function.name, args)
                tool_result = {"status": "dispatched_to_device"}
            else:
                tool_result = await tool_service.execute_tool(tc.function.name, args)

            chat_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": json.dumps(tool_result),
                }
            )

        final = await _client.chat.completions.create(
            model=_MODEL,
            messages=chat_messages,
        )
        return final.choices[0].message.content, action
    except Exception:
        # Tool execution (weather/search API down) or the follow-up
        # completion failed — degrade to a plain reply instead of losing
        # the whole turn.
        return await complete(messages), None
