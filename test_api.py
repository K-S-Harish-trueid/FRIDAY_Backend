"""
Run with: python test_api.py
Requires the server to be running: uvicorn main:app --reload
"""

import sys
import httpx

BASE_URL = "https://friday-backend-t7xa.onrender.com"
#BASE_URL = "http://localhost:8000"

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0
conversation_id = None


def header(title: str):
    print(f"\n{CYAN}{BOLD}{'─' * 50}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'─' * 50}{RESET}")


def ok(label: str, detail: str = ""):
    global passed
    passed += 1
    suffix = f"  {YELLOW}{detail}{RESET}" if detail else ""
    print(f"  {GREEN}✓ PASS{RESET}  {label}{suffix}")


def fail(label: str, detail: str = ""):
    global failed
    failed += 1
    suffix = f"  {RED}{detail}{RESET}" if detail else ""
    print(f"  {RED}✗ FAIL{RESET}  {label}{suffix}")


def show(res: httpx.Response):
    try:
        import json
        body = json.dumps(res.json(), indent=4)
    except Exception:
        body = res.text
    print(f"  {YELLOW}Status:{RESET} {res.status_code}")
    print(f"  {YELLOW}Body:{RESET}")
    for line in body.splitlines():
        print(f"    {line}")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_health(client: httpx.Client):
    header("1. Health Check  GET /health")
    res = client.get("/health")
    show(res)
    if res.status_code == 200 and res.json().get("status") == "ok":
        ok("Server is up", f"version {res.json().get('version')}")
    else:
        fail("Health check failed")


def test_local_command(client: httpx.Client):
    header("2. Local Command (no DB/Groq)  POST /api/chat")
    payload = {"messages": [{"role": "user", "content": "what time is it"}]}
    res = client.post("/api/chat", json=payload)
    show(res)
    data = res.json()
    if res.status_code == 200 and data.get("response"):
        no_conv = data.get("conversation_id") is None
        ok("Local command handled", data["response"][:60])
        if no_conv:
            ok("No conversation created for local command")
        else:
            fail("Unexpected conversation_id for local command")
    else:
        fail("Local command failed")


def test_chat_new_conversation(client: httpx.Client):
    global conversation_id
    header("3. Chat — auto-create conversation  POST /api/chat")
    payload = {"messages": [{"role": "user", "content": "Who built you?"}]}
    res = client.post("/api/chat", json=payload, timeout=30)
    show(res)
    data = res.json()
    if res.status_code == 200 and data.get("conversation_id"):
        conversation_id = data["conversation_id"]
        ok("Got AI reply", data["response"][:60])
        ok("Conversation auto-created", conversation_id)
    else:
        fail("Chat / conversation creation failed", str(res.status_code))


def test_chat_continue(client: httpx.Client):
    header("4. Continue existing conversation  POST /api/chat")
    if not conversation_id:
        fail("Skipped — no conversation_id from previous test")
        return
    payload = {
        "messages": [
            {"role": "user",     "content": "Who built you?"},
            {"role": "assistant","content": "I am F.R.I.D.A.Y."},
            {"role": "user",     "content": "Tell me a fun fact."},
        ],
        "conversation_id": conversation_id,
    }
    res = client.post("/api/chat", json=payload, timeout=30)
    show(res)
    data = res.json()
    if res.status_code == 200 and data.get("conversation_id") == conversation_id:
        ok("Continued same conversation", data["response"][:60])
    else:
        fail("Continuation failed", str(res.status_code))


def test_list_conversations(client: httpx.Client):
    header("5. List conversations  GET /conversations/")
    res = client.get("/conversations/")
    show(res)
    data = res.json()
    if res.status_code == 200 and isinstance(data, list) and len(data) > 0:
        ok(f"Found {len(data)} conversation(s)", f"latest title: \"{data[0]['title']}\"")
    else:
        fail("List failed or empty", str(res.status_code))


def test_get_messages(client: httpx.Client):
    header("6. Get messages  GET /conversations/{id}/messages")
    if not conversation_id:
        fail("Skipped — no conversation_id")
        return
    res = client.get(f"/conversations/{conversation_id}/messages")
    show(res)
    data = res.json()
    if res.status_code == 200 and isinstance(data, list):
        ok(f"Retrieved {len(data)} message(s)")
        for m in data:
            ok(f"  [{m['role']}]", m["content"][:60])
    else:
        fail("Get messages failed", str(res.status_code))


def test_delete_conversation(client: httpx.Client):
    header("7. Delete conversation  DELETE /conversations/{id}")
    if not conversation_id:
        fail("Skipped — no conversation_id")
        return
    res = client.delete(f"/conversations/{conversation_id}")
    show(res)
    if res.status_code == 200 and res.json().get("deleted"):
        ok("Conversation deleted")
    else:
        fail("Delete failed", str(res.status_code))

    # Verify it's gone
    res2 = client.get(f"/conversations/{conversation_id}/messages")
    if res2.status_code == 404:
        ok("Confirmed 404 after deletion")
    else:
        fail("Expected 404 after deletion, got", str(res2.status_code))


def test_invalid_conversation(client: httpx.Client):
    header("8. Invalid conversation_id  POST /api/chat")
    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "conversation_id": "00000000-0000-0000-0000-000000000000",
    }
    res = client.post("/api/chat", json=payload, timeout=30)
    show(res)
    if res.status_code == 404:
        ok("Correctly returned 404 for unknown conversation")
    else:
        fail("Expected 404", f"got {res.status_code}")


# ── Runner ────────────────────────────────────────────────────────────────────

def main():
    # Enable ANSI on Windows
    if sys.platform == "win32":
        import os
        os.system("")

    print(f"\n{BOLD}{CYAN}F.R.I.D.A.Y  API  TEST  SUITE{RESET}")
    print(f"Target: {BASE_URL}\n")

    try:
        with httpx.Client(base_url=BASE_URL) as client:
            test_health(client)
            test_local_command(client)
            test_chat_new_conversation(client)
            test_chat_continue(client)
            test_list_conversations(client)
            test_get_messages(client)
            test_delete_conversation(client)
            test_invalid_conversation(client)
    except httpx.ConnectError:
        print(f"\n{RED}{BOLD}Cannot connect to {BASE_URL}{RESET}")
        print("Start the server first:  uvicorn main:app --reload\n")
        sys.exit(1)

    # Summary
    total = passed + failed
    colour = GREEN if failed == 0 else RED
    print(f"\n{CYAN}{BOLD}{'─' * 50}{RESET}")
    print(f"{BOLD}  Results: {colour}{passed}/{total} passed{RESET}", end="")
    print(f"  {RED}({failed} failed){RESET}" if failed else "")
    print(f"{CYAN}{BOLD}{'─' * 50}{RESET}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
