"""
core/runtime_errors.py — Schéma canonique JSONL des erreurs runtime Forge.

Ce module définit le format officiel des événements d'erreur runtime.
Il fournit les constantes, les fonctions de construction et de sérialisation.

Ce module ne collecte ni n'écrit encore aucun fichier.
L'écriture dans storage/logs/errors.dev.jsonl est le rôle de DX-RUNTIME-ERRORS-JSONL-001.
"""
from __future__ import annotations

import json
import secrets
import sys
import traceback as _traceback
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0"

# ── Niveaux ───────────────────────────────────────────────────────────────────

LEVEL_ERROR    = "ERROR"
LEVEL_WARNING  = "WARNING"
LEVEL_INFO     = "INFO"
LEVEL_CRITICAL = "CRITICAL"

LEVELS: frozenset[str] = frozenset({
    LEVEL_ERROR, LEVEL_WARNING, LEVEL_INFO, LEVEL_CRITICAL,
})

# ── Catégories ────────────────────────────────────────────────────────────────

CATEGORY_RUNTIME       = "runtime"
CATEGORY_CONTROLLER    = "controller"
CATEGORY_ROUTING       = "routing"
CATEGORY_TEMPLATE      = "template"
CATEGORY_DATABASE      = "database"
CATEGORY_CONFIGURATION = "configuration"
CATEGORY_HTTP          = "http"
CATEGORY_UNKNOWN       = "unknown"

CATEGORIES: frozenset[str] = frozenset({
    CATEGORY_RUNTIME,
    CATEGORY_CONTROLLER,
    CATEGORY_ROUTING,
    CATEGORY_TEMPLATE,
    CATEGORY_DATABASE,
    CATEGORY_CONFIGURATION,
    CATEGORY_HTTP,
    CATEGORY_UNKNOWN,
})

# ── Champs obligatoires ───────────────────────────────────────────────────────

REQUIRED_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "id",
    "timestamp",
    "environment",
    "level",
    "category",
    "exception_type",
    "message",
    "safe_for_display",
})

# ── Clés sensibles à ne jamais enregistrer en clair ──────────────────────────

_SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password", "passwd", "pwd", "secret", "token",
    "api_key", "apikey", "authorization", "cookie",
    "session", "csrf", "private_key", "access_token",
    "refresh_token", "key", "auth", "bearer",
})


# ── Identifiant unique ────────────────────────────────────────────────────────

def _generate_id() -> str:
    """Génère un identifiant unique : err_YYYYMMDD_HHMMSS_xxxx."""
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = secrets.token_hex(2)
    return f"err_{ts}_{suffix}"


# ── Extraction de la pile d'appels ────────────────────────────────────────────

def _extract_traceback(exc_info=None) -> list[dict[str, Any]]:
    """Extrait une pile simplifiée depuis exc_info ou le contexte courant."""
    if exc_info is None:
        exc_info = sys.exc_info()
    _, _, tb = exc_info
    if tb is None:
        return []
    return [
        {"file": f.filename, "line": f.lineno, "function": f.name}
        for f in _traceback.extract_tb(tb)
    ]


def _extract_location(frames: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Retourne le dernier frame de la pile comme emplacement principal."""
    if not frames:
        return None
    last = frames[-1]
    return {"file": last["file"], "line": last["line"], "function": last["function"]}


# ── Filtrage des informations de requête ──────────────────────────────────────

def safe_request_info(
    method: str | None,
    path: str | None,
    query: str | None = None,
    post_keys: list[str] | None = None,
    header_names: list[str] | None = None,
) -> dict[str, Any]:
    """
    Construit un objet request sécurisé pour les événements d'erreur.

    Seuls les noms des champs POST sont conservés, jamais les valeurs.
    Les headers sont filtrés pour exclure les valeurs sensibles.
    """
    safe: dict[str, Any] = {
        "method": method or "",
        "path":   path   or "",
        "query":  query  or "",
    }
    if post_keys is not None:
        safe["post_keys"] = [str(k) for k in post_keys]
    if header_names is not None:
        safe["headers"] = [str(h) for h in header_names]
    return safe


# ── Construction d'un événement d'erreur ─────────────────────────────────────

def build_error_event(
    exception_type: str,
    message: str,
    *,
    environment: str = "dev",
    level: str = LEVEL_ERROR,
    category: str = CATEGORY_RUNTIME,
    request: dict[str, Any] | None = None,
    traceback_frames: list[dict[str, Any]] | None = None,
    hint: str = "",
    safe_for_display: bool = False,
) -> dict[str, Any]:
    """
    Construit un événement d'erreur conforme au schéma canonique v1.0.

    Args:
        exception_type  : nom du type d'exception (ex : "RuntimeError").
        message         : message court de l'erreur.
        environment     : environnement courant ("dev" ou "prod").
        level           : niveau — ERROR, WARNING, INFO, CRITICAL.
        category        : catégorie fonctionnelle (voir CATEGORIES).
        request         : objet request filtré via safe_request_info().
        traceback_frames: pile simplifiée (liste de dicts file/line/function).
        hint            : piste de correction pour le développeur.
        safe_for_display: True si le message peut être montré au visiteur.

    Returns:
        dict conforme au schéma, sérialisable en JSONL.
    """
    event: dict[str, Any] = {
        "schema_version":  SCHEMA_VERSION,
        "id":              _generate_id(),
        "timestamp":       datetime.now(tz=timezone.utc).isoformat(),
        "environment":     environment,
        "level":           level,
        "category":        category,
        "exception_type":  exception_type,
        "message":         message,
        "safe_for_display": safe_for_display,
    }

    if request is not None:
        event["request"] = request

    frames = traceback_frames or []
    if frames:
        event["traceback"] = frames
        loc = _extract_location(frames)
        if loc:
            event["location"] = loc

    if hint:
        event["hint"] = hint

    return event


def build_error_event_from_exc(
    exc: BaseException,
    *,
    environment: str = "dev",
    level: str = LEVEL_ERROR,
    category: str = CATEGORY_RUNTIME,
    request: dict[str, Any] | None = None,
    hint: str = "",
    safe_for_display: bool = False,
) -> dict[str, Any]:
    """
    Construit un événement d'erreur depuis une exception active.

    Doit être appelé depuis un bloc except pour que sys.exc_info() soit valide.
    """
    return build_error_event(
        exception_type  = type(exc).__name__,
        message         = str(exc),
        environment     = environment,
        level           = level,
        category        = category,
        request         = request,
        traceback_frames= _extract_traceback(),
        hint            = hint,
        safe_for_display= safe_for_display,
    )


# ── Validation ────────────────────────────────────────────────────────────────

def validate_event(event: dict[str, Any]) -> None:
    """
    Vérifie la présence des champs obligatoires.

    Raises:
        ValueError: si un ou plusieurs champs obligatoires sont absents.
    """
    missing = REQUIRED_FIELDS - set(event.keys())
    if missing:
        raise ValueError(f"Champs obligatoires manquants : {sorted(missing)}")


# ── Accès aux clés sensibles (pour tests et filtrage externe) ────────────────

def _sensitive_keys_exposed() -> frozenset[str]:
    """Retourne l'ensemble des clés considérées sensibles par ce module."""
    return _SENSITIVE_KEYS


# ── Sérialisation JSONL ───────────────────────────────────────────────────────

def serialize_event(event: dict[str, Any]) -> str:
    """
    Sérialise un événement en une ligne JSONL (sans retour à la ligne final).

    Chaque appel produit exactement une ligne JSON valide, sans saut de ligne.
    Encodage UTF-8, pas d'espaces superflus.
    """
    return json.dumps(event, ensure_ascii=False, separators=(",", ":"))
