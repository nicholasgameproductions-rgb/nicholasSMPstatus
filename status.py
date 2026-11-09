import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

SERVER = "nicholasgp.eagler.host"
API = f"https://topeaglerservers.com/api/status/{SERVER}"
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"].strip().rstrip("/")
MESSAGE_ID = os.getenv("DISCORD_MESSAGE_ID", "").strip()


def request_json(url, method="GET", payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "User-Agent": "NicholasSMP-Status/6.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read()
        return json.loads(raw) if raw else {}


def clean(value):
    if isinstance(value, list):
        value = "\n".join(str(item) for item in value)
    if value is None:
        return "Unknown"
    value = re.sub(r"(?i)§[0-9a-fk-orx]", "", str(value))
    value = value.replace("@", "@\u200b").strip()
    return value[:1000] or "Unknown"


def make_embed():
    color = 0xFEE75C
    status = "🟡 STATUS UNAVAILABLE"
    players = version = ping = motd = "Unknown"
    quality = ""
    try:
        data = request_json(API)
        if data.get("success") is False:
            raise ValueError("Status API returned success=false")
        server = data.get("server")
        if not isinstance(server, dict):
            raise ValueError("Missing server object in API response")

        online = server.get("online")
        if online is True:
            status, color = "🟢 ONLINE", 0x57F287
        elif online is False:
            status, color = "🔴 OFFLINE", 0xED4245

        player_data = server.get("players") or {}
        if isinstance(player_data, dict):
            count = player_data.get("online")
            maximum = player_data.get("max")
            if count is not None:
                players = f"{count} / {maximum if maximum is not None else '?'}"

        version = clean(server.get("version"))
        motd = clean(server.get("motd"))
        ping_data = server.get("ping")
        if isinstance(ping_data, dict):
            latency = ping_data.get("time")
            quality = clean(ping_data.get("quality")) if ping_data.get("quality") else ""
            if isinstance(latency, (int, float)) and not isinstance(latency, bool):
                ping = f"{latency:g} ms"
            elif latency is not None:
                ping = f"{clean(latency)} ms"
        elif isinstance(ping_data, (int, float)) and not isinstance(ping_data, bool):
            ping = f"{ping_data:g} ms"

        print(f"API: online={online}, players={players}, ping={ping}, quality={quality}", flush=True)
    except Exception as error:
        print(f"API ERROR: {type(error).__name__}: {error}", flush=True)

    if ping != "Unknown" and quality:
        ping += f" ({quality.title()})"

    return {
        "title": "✦ NICHOLASSMP OFFICIAL ✦",
        "description": f"**{status}**\n⚔️ Survival • Season 2",
        "color": color,
        "fields": [
            {"name": "👥 Players", "value": players, "inline": True},
            {"name": "🎮 Version", "value": version, "inline": True},
            {"name": "📡 Ping", "value": ping, "inline": True},
            {"name": "🌐 Server Address", "value": f"`{SERVER}`", "inline": False},
            {"name": "📜 MOTD", "value": motd, "inline": False},
        ],
        "footer": {"text": "NicholasSMP • GitHub Actions status monitor"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print("NicholasSMP status update starting", flush=True)
    payload = {"embeds": [make_embed()], "allowed_mentions": {"parse": []}}
    if MESSAGE_ID:
        try:
            request_json(f"{WEBHOOK}/messages/{MESSAGE_ID}", "PATCH", payload)
            print("SUCCESS: Updated existing Discord status message", flush=True)
            return
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            print("Existing message missing (404); creating a new one", flush=True)

    payload["username"] = "NicholasSMP Status"
    result = request_json(f"{WEBHOOK}?wait=true", "POST", payload)
    new_id = result.get("id")
    print("SUCCESS: Created Discord status message", flush=True)
    print("FIRST RUN MESSAGE ID:", new_id, flush=True)
    print("Set DISCORD_MESSAGE_ID to this ID in GitHub Actions secrets.", flush=True)


if __name__ == "__main__":
    main()
