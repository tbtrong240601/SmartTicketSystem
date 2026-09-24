"""Process-local login backoff for the single-process local server."""
from collections import deque
from threading import Lock
from time import monotonic
from flask import current_app


def state():
    return current_app.extensions.setdefault("login_throttle", {"lock": Lock(), "attempts": {}})


def allow_login(key):
    data = state()
    with data["lock"]:
        cutoff = monotonic() - 900
        for old_key in list(data["attempts"]):
            queue = data["attempts"][old_key]
            while queue and queue[0] < cutoff:
                queue.popleft()
            if not queue:
                del data["attempts"][old_key]
        return len(data["attempts"].get(key, ())) < 10


def record_failure(key):
    data = state()
    with data["lock"]:
        if len(data["attempts"]) >= 10000 and key not in data["attempts"]:
            data["attempts"].pop(next(iter(data["attempts"])))
        data["attempts"].setdefault(key, deque(maxlen=10)).append(monotonic())


def clear_failures(key):
    data = state()
    with data["lock"]:
        data["attempts"].pop(key, None)
