"""NicholasSMP live Discord status — GitHub Actions / Python standard library only."""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

API_URL = 'https://topeaglerservers.com/api/status/nicholasgp.eagler.host'
SERVER_ADDRESS = 'nicholasgp.eagler.host'
WEBHOOK = os.environ['DISCORD_WEBHOOK_URL'].strip().rstrip('/')
MESSAGE_ID = os.environ.get('DISCORD_MESSAGE_ID', '').strip()


def fetch_json(url):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (NicholasSMP-Status/3.0)',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def normalized_key(key):
    return re.sub(r'[^a-z0-9]', '', str(key).lower())


def get_key(obj, *candidates):
    if not isinstance(obj, dict):
        return None
    lookup = {normalized_key(k): v for k, v in obj.items()}
    for name in candidates:
        v = lookup.get(normalized_key(name))
        if v is not None:
            return v
    return None


def deep_get(obj, *candidates):
    """Find a matching key anywhere within nested public status data."""
    queue = [obj]
    visited = 0
    while queue and visited < 100:
        current = queue.pop(0)
        visited += 1
        if isinstance(current, dict):
            value = get_key(current, *candidates)
            if value is not None:
                return value
            queue.extend(x for x in current.values() if isinstance(x, (dict, list)))
        elif isinstance(current, list):
            queue.extend(x for x in current if isinstance(x, (dict, list)))
    return None


def to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, dict):
        return to_bool(get_key(value, 'online', 'isOnline', 'status', 'state', 'reachable'))
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ('online', 'up', 'true', 'yes', 'reachable', 'running', '1'):
            return True
        if s in ('offline', 'down', 'false', 'no', 'unreachable', 'stopped', '0'):
            return False
    return None


def as_text(v, fallback='Unknown'):
    if v is None:
        return fallback
    if isinstance(v, dict):
        value = get_key(v, 'clean', 'text', 'plain', 'raw', 'value', 'name', 'description', 'version')
        return as_text(value, fallback)
    if isinstance(v, list):
        return ' | '.join(as_text(x, '') for x in v)[:950] or fallback
    # strip Minecraft legacy formatting; prevent Discord mentions
    text = re.sub(r'(?i)\u00a7[0-9a-fk-or]', '', str(v))
    return text.replace('@', '@\u200b').strip()[:950] or fallback


def get_stats(document):
    # API response known to contain success, timestamp and server.
    server = get_key(document, 'server')
    if isinstance(server, dict):
        root = server
    else:
        root = get_key(document, 'data') or document

    # Never interpret top-level `success` as proof that the Minecraft server is online.
    status = deep_get(root, 'online', 'isOnline', 'is_online', 'serverOnline',
                      'status', 'state', 'reachable', 'isReachable')
    online = to_bool(status)
