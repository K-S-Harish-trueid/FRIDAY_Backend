from datetime import datetime
from typing import Optional
import random


class CommandResult:
    def __init__(self, response: str, command_type: str):
        self.response = response
        self.command_type = command_type


# ── Handler registry ──────────────────────────────────────────────────────────
# Each handler is a callable(lower: str) -> Optional[CommandResult].
# Return None to pass to the next handler; return a CommandResult to stop.
# Add new handlers to the list at the bottom of this file.

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _matches(text: str, patterns: list[str]) -> bool:
    return any(p in text for p in patterns)


def handle_time(lower: str) -> Optional[CommandResult]:
    if lower == "time" or _matches(lower, ["what time", "current time", "time now"]):
        now = datetime.now()
        return CommandResult(
            response=f"It's {now.strftime('%H:%M')}, boss.",
            command_type="time",
        )
    return None


def handle_date(lower: str) -> Optional[CommandResult]:
    if lower == "date" or _matches(
        lower, ["today's date", "what day", "what date", "current date"]
    ):
        now = datetime.now()
        weekday = _WEEKDAYS[now.weekday()]
        month = _MONTHS[now.month - 1]
        return CommandResult(
            response=f"Today is {weekday}, {now.day} {month} {now.year}.",
            command_type="date",
        )
    return None


def handle_greeting(lower: str) -> Optional[CommandResult]:
    if lower in ("hi", "hey", "hello") or _matches(
        lower, ["hey friday", "hello friday", "hi friday"]
    ):
        return CommandResult(
            response="Systems online. Ready when you are, boss.",
            command_type="greeting",
        )
    return None


def handle_identity(lower: str) -> Optional[CommandResult]:
    if _matches(lower, ["who are you", "introduce yourself", "what are you"]):
        return CommandResult(
            response=(
                "F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth. "
                "Backend systems operational. How can I assist?"
            ),
            command_type="identity",
        )
    return None


def handle_help(lower: str) -> Optional[CommandResult]:
    if lower in ("help", "commands") or _matches(
        lower, ["what can you do", "what do you do", "show commands"]
    ):
        help_text = (
            "Available server-side commands:\n\n"
            "• time — Current server time\n"
            "• date — Today's server date\n"
            "• hello / hi — Greeting\n"
            "• who are you — Introduction\n"
            "• help — Show this list\n\n"
            "Anything else routes to the AI backend (not yet connected)."
        )
        return CommandResult(response=help_text, command_type="help")
    return None


def handle_shutdown(lower: str) -> Optional[CommandResult]:
    if lower in ("shutdown", "goodbye", "bye") or _matches(
        lower, ["bye friday", "shut down", "power off", "goodbye friday"]
    ):
        return CommandResult(
            response="Powering down. Until next time, boss.",
            command_type="shutdown",
        )
    return None


# ── Registry — add new handlers here as a drop-in ────────────────────────────
# TODO: add handle_pokemon, handle_weather, etc. when services are ready
HANDLERS = [
    handle_time,
    handle_date,
    handle_greeting,
    handle_identity,
    handle_help,
    handle_shutdown,
]


def dispatch(user_message: str) -> Optional[CommandResult]:
    """Run the message through all registered handlers; return first match."""
    lower = user_message.lower().strip()
    for handler in HANDLERS:
        result = handler(lower)
        if result is not None:
            return result
    return None
