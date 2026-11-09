import os
import json
import re
import urllib.request
from datetime import datetime, timezone

API = "https://topeaglerservers.com/api/status/nicholasgp.eagler.host"
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"].strip().rstrip("/")
MESSAGE_ID = os.getenv("DISCORD_MESSAGE_ID", "").strip()
SERVER = "nicholasgp.eagler.host"


def get_value(data, *keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def text(value, default="Unknown"):
    if value is None:
        return default
    if isinstance(value, dict):
        return text(get_value(value, "clean", "text", "plain", "version", "name"), default)
    if isinstance(value, list):
        return " | ".join(text(item, "") for item in value)[:900] or default
    result = re.sub(r"(?i)§[0-9a-fk-or]", "", str(value))
    return result.replace("@", "@\u200b")[:900] or default


def request_json(url, method="GET", payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "User-Agent": "NicholasSMP-Status/4.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        content = response.read()
        return json.loads(content) if content else {}


def make_embed():
    now = datetime.now(timezone.utc).isoformat()

    status = "🟡 STATUS UNAVAILABLE"
    color = 0xFEE75C
    players = "Unknown"
    version = "Unknown"
    ping = "Unknown"
    motd = "Unknown"

    try:
        data = request_json(API)
        print("API keys:", list(data.keys()))

        server = data.get("server", {})
        if not isinstance(server, dict):
            server = {}

        print("Server keys:", list(server.keys()))

        online = get_value(server, "online", "isOnline", "is_online")
        if online is None:
            online = get_value(server, "status", "state")

        if isinstance(online, str):
            online = online.lower() in ("online", "true", "up", "running")

        if online is True:
            status = "🟢 ONLINE"
            color = 0x57F287
        elif online is False:
            status = "🔴 OFFLINE"
            color = 0xED4245

        player_data = get_value(server, "players", "playerData")
        if isinstance(player_data, dict):
            count = get_value(player_data, "online", "current", "count")
            maximum = get_value(player_data, "max", "maximum", "limit")
        else:
            count = get_value(server, "playersOnline", "onlinePlayers", "playerCount")
            maximum = get_value(server, "maxPlayers", "playersMax")

        if count is not None:
            players = f"{text(count)} / {text(maximum, '?')}"

        version = text(get_value(server, "version", "minecraftVersion", "serverVersion"))

        ping_value = get_value(server, "ping", "latency", "responseTime")
        if ping_value is not None:
            ping = text(ping_value)
            if isinstance(ping_value, (int, float)):
                ping += " ms"

        motd = text(get_value(server, "motd", "description", "serverMotd"))

        print("Parsed status:", status)
        print("Parsed players:", players)

    except Exception as error:
        print("API ERROR:", type(error).__name__, str(error))

    return {
        "title": "✦ NICHOLASSMPOFFICIAL ✦",
        "description": f"**{status}**\nSurvival • Season 2",
        "color": color,
        "fields": [
            {"name": "👥 Players", "value": players, "inline": True},
            {"name": "🎮 Version", "value": version, "inline": True},
            {"name": "📡 Ping", "value": ping, "inline": True},
            {"name": "🌐 Server IP", "value": f"`{SERVER}`", "inline": False},
            {"name": "📜 Server MOTD", "value": motd, "inline": False}
        ],
        "footer": {
            "text": "NicholasSMP • Automatically updated!"
        },
        "timestamp": now
    }


def main():
    print("Starting NicholasSMP status updater...", flush=True)

    payload = {
        "embeds": [make_embed()],
        "allowed_mentions": {"parse": []}
    }

    if MESSAGE_ID:
        print("Updating message:", MESSAGE_ID, flush=True)
        request_json(
            f"{WEBHOOK}/messages/{MESSAGE_ID}",
            method="PATCH",
            payload=payload
        )
        print("SUCCESS: Existing Discord message updated!", flush=True)
    else:
        print("Creating new Discord message...", flush=True)
        payload["username"] = "NicholasSMP Status"

        result = request_json(
            WEBHOOK + "?wait=true",
            method="POST",
            payload=payload
        )

        print("SUCCESS: Discord message created!", flush=True)
        print("FIRST RUN MESSAGE ID:", result.get("id"), flush=True)
        print("Save this ID as DISCORD_MESSAGE_ID in GitHub Secrets.", flush=True)


if __name__ == "__main__":
    main()
