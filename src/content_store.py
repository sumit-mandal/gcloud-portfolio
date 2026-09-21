"""Load and persist portfolio content as JSON."""

from __future__ import annotations

import json
import re
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
CONTENT_PATH = DATA_DIR / "content.json"

_lock = threading.Lock()

SECTION_THEMES = {
    "skills": "skills-section",
    "experience": "experience-section",
    "education": "education-section",
    "achievements": "achievements-section",
    "custom": "custom-section",
}


def _default_content() -> dict[str, Any]:
    return {
        "site": {
            "title": "Portfolio",
            "footer": "© Portfolio",
        },
        "home": {
            "name_line_1": "Your",
            "name_line_2": "Name",
            "role_sticker": "Role",
            "tagline": "Tagline",
            "email": "you@example.com",
            "cta_text": "Contact Me",
            "profile_image": "/static/images/profile.jpg",
            "badge_1": "Badge",
            "badge_2": "Badge",
            "marquee": "Skill ✦ Skill ✦",
        },
        "sections": [],
    }


def load_content() -> dict[str, Any]:
    with _lock:
        if not CONTENT_PATH.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = _default_content()
            CONTENT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return deepcopy(data)
        return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def save_content(data: dict[str, Any]) -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        CONTENT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "section"


def unique_section_id(content: dict[str, Any], base: str) -> str:
    existing = {s.get("id") for s in content.get("sections", [])}
    candidate = slugify(base)
    if candidate not in existing and candidate != "home":
        return candidate
    idx = 2
    while f"{candidate}-{idx}" in existing:
        idx += 1
    return f"{candidate}-{idx}"


def get_section(content: dict[str, Any], section_id: str) -> dict[str, Any] | None:
    for section in content.get("sections", []):
        if section.get("id") == section_id:
            return section
    return None


def enabled_sections(content: dict[str, Any]) -> list[dict[str, Any]]:
    return [s for s in content.get("sections", []) if s.get("enabled", True)]
