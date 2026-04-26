"""Chargement et résolution du registre des starter apps."""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


class StarterNotFound(ValueError):
    pass


class StarterUnavailable(ValueError):
    pass


def all_starters() -> list[dict]:
    starters = []
    for d in sorted(DATA_DIR.iterdir()):
        if not d.is_dir():
            continue
        meta_path = d / "starter.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["_dir"] = d
        starters.append(meta)
    starters.sort(key=lambda s: s.get("number", 99))
    return starters


def resolve(identifier: str) -> dict:
    """Résout 1, 'contacts', 'contact-simple' → metadata dict."""
    for s in all_starters():
        if str(s.get("number")) == identifier:
            return s
        if s.get("id") == identifier:
            return s
        if identifier.lower() in [a.lower() for a in s.get("aliases", [])]:
            return s
    raise StarterNotFound(
        f"Starter inconnu : {identifier!r}. Voir : forge starter:list"
    )
