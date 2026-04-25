"""Formatage centralisé des tags CLI Forge.

Toutes les lignes de statut produites par les commandes de génération
passent par ce module pour garantir un alignement et un vocabulaire cohérents.
"""

from __future__ import annotations

_WIDTH = 12


def tag(label: str, message: str) -> str:
    return f"[{label}]".ljust(_WIDTH) + message


def written(path: str) -> str:
    return tag("ÉCRIT", path)


def created(path: str) -> str:
    return tag("CRÉÉ", path)


def preserved(path: str, detail: str = "") -> str:
    msg = path + (f"  {detail}" if detail else "")
    return tag("PRÉSERVÉ", msg)


def error(message: str) -> str:
    return tag("ERREUR", message)


def ok(message: str) -> str:
    return tag("OK", message)


def info(message: str) -> str:
    return tag("INFO", message)


def warn(message: str) -> str:
    return tag("WARN", message)


def dry_run(message: str) -> str:
    return tag("DRY-RUN", message)
