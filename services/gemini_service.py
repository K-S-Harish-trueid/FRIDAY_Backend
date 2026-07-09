import google.generativeai as genai
from config import settings
from models.chat import ChatMessage

_SYSTEM_PROMPT = (
    "You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth. "
    "You are sharp, efficient, and concise. Occasionally address the user as 'boss'."
)

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=_SYSTEM_PROMPT)


async def complete(messages: list[ChatMessage]) -> str:
    history = [
        {"role": "user" if m.role == "user" else "model", "parts": [m.content]}
        for m in messages
    ]
    response = await _model.generate_content_async(history)
    return response.text
