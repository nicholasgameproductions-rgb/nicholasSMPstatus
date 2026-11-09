import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://topeaglerservers.com/api/status/nicholasgp.eagler.host"
HOOK = os.environ["DISCORD_WEBHOOK_URL"].strip().rstrip("/")
MESSAGE_ID = os.environ.get("DISCORD_MESSAGE_ID", "").strip()


def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": "NicholasSMP-Discord-Status/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    if not isinstance(data, dict):
        raise ValueError("Unexpected API response (not a JSON object)")
    print("API keys:", ", ".join(data.keys()))
    return data


def pick(data, *keys):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def flatten(value):
    if isinstance(value, dict):
        return flatten(pick(value, "clean", "text", "raw", "description", "motd"))
    if isinstance(value, list):
        return " | ".join(map(str, value))
    return str(value) if value is not None else "Unknown"


def build_embed():
    checked = datetime.now(timezone.utc).isoformat()
    try:
        data = fetch()
        # API providers use slightly different response wrappers.
        core = data.get("data", data)
        if not isinstance(core, dict):
            core = data
        explicit_online = pick(core, "online", "is_online", "isOnline")
        status = pick(core, "status", "state")
        if isinstance(explicit_online, bool):
            online = explicit_online
        elif isinstance(status, str):
            online = status.lower() in ("online", "up")
        else:
            online = None
        players = pick(core, "players", "playerCount", "player_count")
        if isinstance(players, dict):
            current = pick(players, "online", "current", "count")
            maximum = pick(players, "max", "maximum", "limit")
        else:
            current = players
            maximum = pick(core, "maxPlayers", "max_players", "max")
        version = flatten(pick(core, "version", "serverVersion", "minecraft_version"))
        ping = pick(core, "latency", "ping", "responseTime", "response_time")
        motd = flatten(pick(core, "motd", "description", "message"))
        # If the API lacks an explicit online field, don't silently label it Online.
        if online is None:
            label, color = "🟡 STATUS UNKNOWN", 0xF1C40F
        else:
            label, color = ("🟢 ONLINE", 0x57F287) if online else ("🔴 OFFLINE", 0xED4245)
        player_text = f"{current if current is not None else '?'} / {maximum if maximum is not None else '?'}" if online is not False else "Offline"
        ping_text = f"{ping} ms" if isinstance(ping, (int, float)) else flatten(ping)
        fields = [
            {"name": "👥 Players", "value": str(player_text)[:1024], "inline": True},
            {"name": "🎮 Version", "value": version[:1024], "inline": True},
            {"name": "📡 Ping", "value": ping_text[:1024], "inline": True},
            {"name": "🌐 Server Address", "value": "`nicholasgp.eagler.host`", "inline": False},
            {"name": "📜 MOTD", "value": (motd or "Unknown")[:1024], "inline": False},
        ]
        description = f"**{label}**\nSurvival • NicholasSMPOfficial"
    except Exception as exc:
        print(f"Could not retrieve server status: {type(exc).__name__}: {exc}")
        color = 0xFEE75C
        description = "🟡 **STATUS UNAVAILABLE**\nMonitoring API could not be reached. This does *not* necessarily mean the server is offline."
        fields = [{"name": "🌐 Server Address", "value": "`nicholasgp.eagler.host`", "inline": False}]
    return {"title": "✦ NICHOLASSMP OFFICIAL ✦", "description": description,
            "color": color, "fields": fields,
            "footer": {"text": "NicholasSMP • Auto-updates approximately every 5 minutes"}, "timestamp": checked}


def send(method, url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "NicholasSMPStatus/1.0"}, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = resp.read().decode()
    return json.loads(result) if result else {}


if __name__ == "__main__":
    payload = {"embeds": [build_embed()], "allowed_mentions": {"parse": []}}
    if MESSAGE_ID:
        url = f"{HOOK}/messages/{MESSAGE_ID}"
        result = send("PATCH", url, payload)
        print("Updated existing status message:", result.get("id", MESSAGE_ID))
    else:
        result = send("POST", f"{HOOK}?wait=true", {**payload, "username": "NicholasSMP Status"})
        print("FIRST RUN: message created successfully. MESSAGE ID:", result.get("id"))
        print("Set repository secret DISCORD_MESSAGE_ID to this ID BEFORE running again to avoid duplicate messages.")
