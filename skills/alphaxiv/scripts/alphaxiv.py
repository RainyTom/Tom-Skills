#!/usr/bin/env python3
"""Minimal alphaXiv MCP client over Streamable HTTP.

Use when native MCP tools are unavailable (scripts, CI, headless agents).
Requires an API key: env ALPHAXIV_API_KEY, --api-key, or ~/.config/alphaxiv/key.

Usage:
  alphaxiv.py list-tools
  alphaxiv.py call <tool_name> '<json arguments>'
  alphaxiv.py call discover_papers '{"keywords": ["RAG"], "question": "...", "difficulty": 3}'
"""

import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.alphaxiv.org/mcp/v1"
PROTOCOL_VERSION = "2025-06-18"


def get_key():
    key = os.environ.get("ALPHAXIV_API_KEY")
    if key:
        return key
    for arg in sys.argv:
        if arg.startswith("--api-key="):
            return arg.split("=", 1)[1]
    try:
        with open(os.path.expanduser("~/.config/alphaxiv/key")) as f:
            return f.read().strip()
    except OSError:
        return None


def post(session_id, key, payload):
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/126.0.0.0 Safari/537.36",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(ENDPOINT, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            new_session = resp.headers.get("Mcp-Session-Id") or session_id
            raw = resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:800]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"connection error: {e}", file=sys.stderr)
        sys.exit(1)
    # Streamable HTTP may return SSE events
    if raw.startswith("event:"):
        data = "\n".join(
            line[6:] for line in raw.splitlines() if line.startswith("data:")
        )
        raw = data
    return new_session, json.loads(raw) if raw else None


def rpc(session_id, key, method, params=None, _id=1):
    payload = {"jsonrpc": "2.0", "id": _id, "method": method}
    if params is not None:
        payload["params"] = params
    return post(session_id, key, payload)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--api-key=")]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    key = get_key()
    if not key:
        print(
            "No API key found. Set ALPHAXIV_API_KEY, pass --api-key=<key>, "
            "or write it to ~/.config/alphaxiv/key.",
            file=sys.stderr,
        )
        sys.exit(1)

    session_id, init_resp = rpc(None, key, "initialize", {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": "alphaxiv-skill-client", "version": "1.0.0"},
    })
    if not init_resp or "result" not in init_resp:
        print(f"initialize failed: {init_resp}", file=sys.stderr)
        sys.exit(1)
    # Bearer-key mode is stateless: no Mcp-Session-Id header is returned,
    # and subsequent requests work without one.

    # Fire-and-forget initialized notification
    try:
        post(session_id, key, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    except Exception:
        pass

    if args[0] == "list-tools":
        _, resp = rpc(session_id, key, "tools/list", _id=2)
        tools = (resp or {}).get("result", {}).get("tools", [])
        for t in tools:
            print(f"- {t['name']}: {t.get('description', '')[:120]}")
        sys.exit(0)

    if args[0] == "call":
        if len(args) < 3:
            print("usage: alphaxiv.py call <tool> '<json args>'", file=sys.stderr)
            sys.exit(2)
        tool, args_raw = args[1], args[2]
        call_args = json.loads(args_raw) if args_raw.strip() else {}
        _, resp = rpc(session_id, key, "tools/call",
                      {"name": tool, "arguments": call_args}, _id=2)
        if resp is None or "result" not in resp:
            print(json.dumps(resp or {"error": "no response"}, ensure_ascii=False))
            sys.exit(1)
        result = resp["result"]
        content = result.get("content", [])
        text = "\n".join(
            c.get("text", "") for c in content if c.get("type") == "text"
        )
        print(text if text else json.dumps(result, ensure_ascii=False))
        sys.exit(0)

    print(f"unknown command: {args[0]}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
