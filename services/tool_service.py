import httpx

# ── WMO weather codes → short human-readable condition ────────────────────────
_WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

# ── Groq-compatible (OpenAI-style) tool schemas ────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a named location (city, town, landmark).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Place name, e.g. 'Hyderabad' or 'Paris, France'",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for a query. Returns a short answer plus top results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_location",
            "description": (
                "Ask the user's device for its current GPS location. Use this when "
                "the user refers to 'my location', 'where am I', or wants an answer "
                "relative to where they are without naming a place — including "
                "weather requests with no city given (e.g. 'what's the weather "
                "like?'). Call this instead of asking the user to type their "
                "location in chat; the app handles that prompt itself."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_maps",
            "description": "Open a location in Google Maps on the user's device.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Place name or address to search for",
                    },
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
            },
        },
    },
]

# Tools whose "execution" is a device action handed back to Flutter rather
# than something the backend can fulfil itself.
DEVICE_ACTION_TOOLS = {"get_current_location", "open_maps"}


async def get_weather(location: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1},
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return {"error": f"Could not find a location named '{location}'."}
        place = results[0]
        lat, lon = place["latitude"], place["longitude"]

        weather = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            },
        )
        weather.raise_for_status()
        current = weather.json().get("current", {})

    code = current.get("weather_code")
    return {
        "location": ", ".join(
            p for p in [place.get("name"), place.get("country")] if p
        ),
        "temperature_c": current.get("temperature_2m"),
        "condition": _WEATHER_CODES.get(code, "Unknown"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
    }


async def web_search(query: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
        )
        res.raise_for_status()
        data = res.json()

    results = []
    for topic in data.get("RelatedTopics", []):
        if "Topics" in topic:
            for sub in topic["Topics"]:
                if sub.get("Text") and sub.get("FirstURL"):
                    results.append({"title": sub["Text"], "url": sub["FirstURL"]})
                if len(results) >= 3:
                    break
        elif topic.get("Text") and topic.get("FirstURL"):
            results.append({"title": topic["Text"], "url": topic["FirstURL"]})
        if len(results) >= 3:
            break

    return {
        "answer": data.get("AbstractText") or data.get("Answer") or "",
        "source_url": data.get("AbstractURL", ""),
        "results": results[:3],
    }


def build_action(tool_name: str, arguments: dict) -> dict:
    """Turn a device-action tool call into the `action` payload sent to Flutter."""
    if tool_name == "get_current_location":
        return {"type": "get_location", "payload": {}}
    if tool_name == "open_maps":
        return {"type": "open_maps", "payload": arguments}
    raise ValueError(f"Unknown device action tool: {tool_name}")


async def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a server-side tool and return its JSON-able result."""
    if name == "get_weather":
        return await get_weather(arguments.get("location", ""))
    if name == "web_search":
        return await web_search(arguments.get("query", ""))
    raise ValueError(f"Unknown server-side tool: {name}")
