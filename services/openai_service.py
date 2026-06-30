from openai import OpenAI
from config import settings
from models.chat import ChatMessage

_SYSTEM_PROMPT = (
    "You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth. "
    "You are sharp, efficient, and concise. Occasionally address the user as 'boss'."
)

_client = OpenAI(api_key=settings.openai_api_key)


def complete(messages: list[ChatMessage]) -> str:
    result = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": _SYSTEM_PROMPT}]
        + [{"role": m.role, "content": m.content} for m in messages],
    )
    return result.choices[0].message.content
