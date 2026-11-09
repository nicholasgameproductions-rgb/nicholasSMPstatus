
import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ==========================================
# NICHOLASSMP - DISCORD STATUS BOT
# ==========================================

SERVER = "nicholasgp.eagler.host"

API = (
    "https://topeaglerservers.com/api/status/"
    + SERVER
)

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"].strip().rstrip("/")

MESSAGE_ID = os.getenv(
    "DISCORD_MESSAGE_ID", ""
).strip()


# ==========================================
# API FUNCTIONS
# ==========================================

def get_value(data, *keys):
    if not isinstance(data, dict):
        return None

    for key in keys:
        if key in data and data[key] is not None:
            return data[key]

    return None


def clean_text(value, default="Unknown"):
    if value is None:
        return default

    if isinstance(value, dict):
        return clean_text(
            get_value(
                value, "clean", "text",
                "plain", "name", "version"
            ),
            default
        )

    if isinstance(value, list):
        result = " | ".join(
            clean_text(item, "")
            for item in value
        )
        return result[:900] or default

    result = re.sub(
        r"(?i)§[0-9a-fk-or]", "",
        str(value)
    )

    return result.replace(
        "@", "@\u200b"
    )[:900] or default


def request_json(url, method="GET", payload=None):
    body = (
        json.dumps(payload).encode("utf-8")
        if payload is not None
        else None
    )

    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "User-Agent": "NicholasSMP-Status/5.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )

    with urllib.request.urlopen(
        req, timeout=25
    ) as response:
        content = response.read()
        return (
            json.loads(content)
            if content
            else {}
        )


# ==========================================
# PING DETECTION
# ==========================================

def find_ping(obj):
    """
    Searches nested API data for common
    ping and latency field names.
    """

    if isinstance(obj, dict):

        for key, value in obj.items():
            normalized = (
                key.lower()
                .replace("_", "")
                .replace("-", "")
            )

            if normalized in (
                "ping",
                "pingms",
                "latency",
                "latencyms",
                "responsetime",
                "responsetimems"
            ):
                if isinstance(value, (int, float)):
                    return f"{value:g} ms"

                if isinstance(value, str):
                    value = value.strip()
                    if value:
                        return value

        for value in obj.values():
            result = find_ping(value)

            if result is not None:
                return result

    elif isinstance(obj, list):

        for item in obj:
            result = find_ping(item)

            if result is not None:
                return result

    return None


# ==========================================
# CREATE DISCORD EMBED
# ==========================================

def make_embed():

    now = datetime.now(
        timezone.utc
    ).isoformat()

    status = "🟡 STATUS UNAVAILABLE"
    color = 0xFEE75C

    players = "Unknown"
    version = "Unknown"
    ping = "Unknown"
    motd = "Unknown"

    try:
        data = request_json(API)

        print(
            "API keys:",
            list(data.keys())
        )

        server = data.get("server", {})

        if not isinstance(server, dict):
            server = {}

        print(
            "Server keys:",
            list(server.keys())
        )

        # ONLINE STATUS

        online = get_value(
            server,
            "online",
            "isOnline",
            "is_online",
            "status",
            "state"
        )

        if isinstance(online, str):
            online = online.lower() in (
                "online",
                "true",
                "up",
                "running"
            )

        if online is True:
            status = "🟢 ONLINE"
            color = 0x57F287

        elif online is False:
            status = "🔴 OFFLINE"
            color = 0xED4245

        # PLAYER COUNT

        player_data = get_value(
            server,
            "players",
            "playerData"
        )

        if isinstance(player_data, dict):

            count = get_value(
                player_data,
                "online",
                "current",
                "count"
            )

            maximum = get_value(
                player_data,
                "max",
                "maximum",
                "limit"
            )

        else:

            count = get_value(
                server,
                "playersOnline",
                "onlinePlayers",
                "playerCount"
            )

            maximum = get_value(
                server,
                "maxPlayers",
                "playersMax"
            )

        if count is not None:
            players = (
                f"{clean_text(count)} / "
                f"{clean_text(maximum, '?')}"
            )

        # MINECRAFT VERSION

        version = clean_text(
            get_value(
                server,
                "version",
                "minecraftVersion",
                "serverVersion"
            )
        )

        # PING - IMPROVED DETECTION

        ping = (
            find_ping(server)
            or find_ping(data)
            or "Not provided"
        )

        print(
            "Detected ping:",
            ping
        )

        # MOTD

        motd = clean_text(
            get_value(
                server,
                "motd",
                "description",
                "serverMotd"
            )
        )

        print(
            "Parsed status:",
            status
        )

        print(
            "Parsed players:",
            players
        )

    except Exception as error:

        print(
            "API ERROR:",
            type(error).__name__,
            str(error)
        )

    # DISCORD EMBED

    return {
        "title": "✦ NICHOLASSMP OFFICIAL ✦",

        "description": (
            f"**{status}**\n"
            "⚔️ Survival • Season 2"
        ),

        "color": color,

        "fields": [
            {
                "name": "👥 Players Online",
                "value": players,
                "inline": True
            },
            {
                "name": "🎮 Minecraft Version",
                "value": version,
                "inline": True
            },
            {
                "name": "📡 Server Ping",
                "value": ping,
                "inline": True
            },
            {
                "name": "🌐 Server Address",
                "value": f"`{SERVER}`",
                "inline": False
            },
            {
                "name": "📜 Server MOTD",
                "value": motd,
                "inline": False
            }
        ],

        "footer": {
            "text": (
                "NicholasSMP • Live Server Monitor "
                "• Auto Updated"
            )
        },

        "timestamp": now
    }


# ==========================================
# DISCORD MESSAGE UPDATER
# ==========================================

def main():

    print(
        "Starting NicholasSMP status updater...",
        flush=True
    )

    payload = {
        "embeds": [make_embed()],
        "allowed_mentions": {
            "parse": []
        }
    }

    if MESSAGE_ID:

        print(
            "Updating existing message:",
            MESSAGE_ID,
            flush=True
        )

        request_json(
            f"{WEBHOOK}/messages/{MESSAGE_ID}",
            method="PATCH",
            payload=payload
        )

        print(
            "SUCCESS: Existing Discord "
            "message updated!",
            flush=True
        )

    else:

        print(
            "Creating new Discord message...",
            flush=True
        )

        payload["username"] = (
            "NicholasSMP Status"
        )

        result = request_json(
            WEBHOOK + "?wait=true",
            method="POST",
            payload=payload
        )

        print(
            "SUCCESS: Discord message created!",
            flush=True
        )

        print(
            "FIRST RUN MESSAGE ID:",
            result.get("id"),
            flush=True
        )

        print(
            "Save this ID as DISCORD_MESSAGE_ID "
            "in GitHub Secrets.",
            flush=True
        )


# ==========================================
# START THE BOT
# ==========================================

if __name__ == "__main__":
    main()
