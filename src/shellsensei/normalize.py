from __future__ import annotations

import hashlib
import re

_URL_RE = re.compile(r"https?://[^\s\"']+", re.IGNORECASE)
_WIN_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s\"']+")
_UNIX_PATH_RE = re.compile(r"(?<![\w.-])/(?:[^\s\"']+)")
_NUM_RE = re.compile(r"\b\d+\b")
_QUOTED_RE = re.compile(r"([\"']).*?\1")
_WS_RE = re.compile(r"\s+")


def normalize_command(raw: str) -> str:
    text = raw.strip()
    if not text:
        return ""

    text = _URL_RE.sub("<URL>", text)
    text = _WIN_PATH_RE.sub("<PATH>", text)
    text = _UNIX_PATH_RE.sub("<PATH>", text)
    text = _QUOTED_RE.sub("<STR>", text)
    text = _NUM_RE.sub("<NUM>", text)
    text = _WS_RE.sub(" ", text)

    return text.lower().strip()


def command_hash(normalized: str) -> str:
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
