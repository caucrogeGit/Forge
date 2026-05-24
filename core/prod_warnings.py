"""core/prod_warnings.py — Avertissements de démarrage liés à la production.

Ticket : AUTH-RATE-LIMIT-PROD-WARNING-001.

Le runtime Forge tolère pour le développement plusieurs choix qui deviennent
fragiles en production : `MemorySessionStore` (perte des sessions au
redémarrage, mono-process) et rate-limit en mémoire (compteurs `dict`
non partagés entre workers — par design dans la série 1.0.0).

Ce module détecte ces situations en `APP_ENV=prod` et fournit un message
clair, sans rien modifier ni bloquer le démarrage. Les fonctions sont
pures et testables ; l'émission via `logging.warning(...)` reste à la
charge du point d'entrée (`app.py`).
"""
from __future__ import annotations

import logging
from typing import Any


PROD_ENV = "prod"

_WARNING_MESSAGE = (
    "AVERTISSEMENT-PROD — Forge tourne en APP_ENV=prod avec stockage mémoire.\n"
    "  * Sessions : MemorySessionStore est volatile et mono-processus.\n"
    "  * Rate-limit (login, uploads) : compteurs en mémoire non partagés.\n"
    "Tolérée pour développement/test, cette configuration est fragile en\n"
    "production. Configurer un session store partagé avant exposition\n"
    "publique (ex. forge.configure(session_store=FileSessionStore(...))).\n"
    "Référence : ADR-002 — docs/adr/002-session-strategy.md."
)


def is_memory_session_store(store: Any) -> bool:
    """Retourne True si le store passé est mémoire (ou pas configuré).

    Le défaut Forge (store non configuré → `None` côté `forge.configure`)
    se résout en `MemorySessionStore` via `core.sessions.manager.get_session_store`,
    donc `None` est traité comme mémoire ici.
    """
    if store is None:
        return True
    # Import local pour ne pas créer de cycle d'import.
    from core.sessions.memory_store import MemorySessionStore
    return isinstance(store, MemorySessionStore)


def should_warn_memory_store_in_prod(app_env: str, session_store: Any) -> bool:
    """Vrai si l'environnement est `prod` et le session store est mémoire."""
    if (app_env or "").strip().lower() != PROD_ENV:
        return False
    return is_memory_session_store(session_store)


def format_memory_store_warning() -> str:
    """Retourne le message d'avertissement humain (multi-ligne)."""
    return _WARNING_MESSAGE


def emit_memory_store_warning_if_needed(
    app_env: str,
    session_store: Any,
    *,
    logger: logging.Logger | None = None,
) -> bool:
    """Émet le warning via `logger.warning(...)` si la condition est vraie.

    Retourne `True` si un warning a été émis, `False` sinon. Idempotent côté
    appelant : à invoquer une seule fois au démarrage.
    """
    if not should_warn_memory_store_in_prod(app_env, session_store):
        return False
    target = logger if logger is not None else logging.getLogger(__name__)
    target.warning("%s", format_memory_store_warning())
    return True
