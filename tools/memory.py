import os
import json
from urllib.parse import urlsplit, urlunsplit

MEMORY_FILE = "logs/sent_jobs.json"


def _normalize(url: str) -> str:
    """Strip query string and fragment so the same posting with different
    tracking params (?q=..., ?jid=...) is treated as one job."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_memory(data):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_duplicate(url: str) -> bool:
    """Check if a job URL (ignoring query params) has already been sent."""
    normalized = _normalize(url)
    return normalized in [_normalize(u) for u in _load_memory()]


def mark_as_sent(urls: list):
    """Save a list of job URLs to memory so they won't be sent again."""
    seen = _load_memory()
    seen_normalized = [_normalize(u) for u in seen]
    for url in urls:
        if _normalize(url) not in seen_normalized:
            seen.append(url)
            seen_normalized.append(_normalize(url))
    _save_memory(seen)
