import os
import json

MEMORY_FILE = "logs/sent_jobs.json"


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
    """Check if a job URL has already been sent."""
    return url in _load_memory()


def mark_as_sent(urls: list):
    """Save a list of job URLs to memory so they won't be sent again."""
    seen = _load_memory()
    for url in urls:
        if url not in seen:
            seen.append(url)
    _save_memory(seen)
