"""
core/errors/runtime_error_logger.py — Collecteur d'erreurs runtime vers JSONL + Markdown.

En mode APP_ENV=dev, chaque erreur non gérée interceptée par le dispatcher
produit une ligne JSONL dans storage/logs/errors.dev.jsonl, puis régénère
storage/logs/errors.dev.md depuis le JSONL.

Ce module est silencieux : si l'écriture échoue, il logge un warning
et laisse l'application continuer normalement.

En mode prod, ce module ne fait rien.
"""
from __future__ import annotations

import logging
import os
import pathlib
import traceback as _traceback
from urllib.parse import urlencode

from core.errors.runtime_errors import (
    CATEGORY_CONFIGURATION,
    CATEGORY_DATABASE,
    CATEGORY_RUNTIME,
    CATEGORY_TEMPLATE,
    build_error_event_from_exc,
    safe_request_info,
    serialize_event,
)

logger = logging.getLogger(__name__)

_JSONL_FILENAME = "errors.dev.jsonl"
_JSONL_DIR_OVERRIDE: pathlib.Path | None = None


# ── Configuration du chemin (surchargeable pour les tests) ────────────────────

def set_jsonl_dir(path: pathlib.Path | None) -> None:
    """Surcharge le répertoire de logs JSONL. Passer None pour restaurer le défaut."""
    global _JSONL_DIR_OVERRIDE
    _JSONL_DIR_OVERRIDE = path


def _resolve_jsonl_dir() -> pathlib.Path:
    if _JSONL_DIR_OVERRIDE is not None:
        return _JSONL_DIR_OVERRIDE
    return pathlib.Path(__file__).parent.parent / "storage" / "logs"


# ── Détection de la catégorie ─────────────────────────────────────────────────

def _detect_category(exc: BaseException) -> str:
    """Détermine la catégorie d'une exception selon son type et son module."""
    module = type(exc).__module__ or ""
    name   = type(exc).__name__

    if "jinja2" in module or "Template" in name:
        return CATEGORY_TEMPLATE
    if "mariadb" in module:
        return CATEGORY_DATABASE
    msg = str(exc).lower()
    if "renderer" in msg or "routeur" in msg or "router" in msg:
        return CATEGORY_CONFIGURATION
    return CATEGORY_RUNTIME


# ── Extraction de la requête ──────────────────────────────────────────────────

def _extract_safe_request(request) -> dict | None:
    """Extrait les informations sûres d'un objet Request Forge."""
    if request is None:
        return None
    try:
        post_keys = sorted(request.body.keys()) if getattr(request, "body", None) else []
        params    = getattr(request, "params", {}) or {}
        query     = urlencode(params, doseq=True) if params else ""
        return safe_request_info(
            method    = getattr(request, "method", ""),
            path      = getattr(request, "path",   ""),
            query     = query,
            post_keys = post_keys,
        )
    except Exception:
        return None


# ── Création du dossier de logs ───────────────────────────────────────────────

def _ensure_log_dir(log_dir: pathlib.Path) -> bool:
    """Crée le dossier de logs si nécessaire. Retourne False si impossible."""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as err:
        logger.warning("Impossible de créer %s : %s", log_dir, err)
        return False


# ── Point d'entrée public ─────────────────────────────────────────────────────

def log_runtime_error(exc: BaseException, request: "object | None" = None) -> None:
    """
    Enregistre une erreur runtime dans storage/logs/errors.dev.jsonl.

    Doit être appelé depuis un bloc except pour que sys.exc_info() soit valide
    (nécessaire pour capturer le traceback).

    Silencieux si l'écriture échoue — ne propage aucune exception.
    N'écrit rien si APP_ENV != "dev".
    """
    # Source de vérité alignée sur le reste du core : core.forge.get("app_env")
    # (configuré via forge.configure). Repli sur os.environ si la config Forge
    # n'est pas initialisée.
    try:
        import core.forge as forge
        environment = forge.get("app_env")
    except Exception:
        environment = os.environ.get("APP_ENV", "dev")
    if environment != "dev":
        return

    try:
        category = _detect_category(exc)
        safe_req = _extract_safe_request(request)
        event    = build_error_event_from_exc(
            exc,
            environment = environment,
            category    = category,
            request     = safe_req,
        )
        line = serialize_event(event)

        log_dir = _resolve_jsonl_dir()
        if not _ensure_log_dir(log_dir):
            return

        jsonl_path = log_dir / _JSONL_FILENAME
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        # Régénère le rendu Markdown depuis le JSONL mis à jour
        try:
            from core.errors.runtime_error_markdown import write_errors_markdown as _write_md
            _write_md(jsonl_path, log_dir / "errors.dev.md")
        except Exception as md_err:
            logger.warning("Impossible de mettre à jour errors.dev.md : %s", md_err)

    except Exception as write_err:
        logger.warning("Impossible d'écrire dans %s : %s", _JSONL_FILENAME, write_err)


# ── Contexte d'erreur pour la page 500 (dev uniquement) ───────────────────────

def build_dev_error_context(exc: BaseException) -> dict | None:
    """Contexte d'erreur destiné à la page `errors/500.html`, en `APP_ENV=dev`.

    Retourne ``{"error": {"type", "message", "traceback"}}`` quand
    l'environnement est explicitement ``dev``, pour que la page 500 affiche la
    cause au développeur. Retourne ``None`` dans tous les autres cas : en prod,
    ou si l'environnement ne peut pas être déterminé. Aucune trace n'est donc
    jamais exposée par défaut (charte : sécuriser par défaut).

    Doit être appelée depuis un bloc ``except`` actif pour que la trace
    (``traceback.format_exc()``) corresponde à l'exception courante.
    """
    try:
        import core.forge as forge
        environment = forge.get("app_env")
    except Exception:
        # Boot incomplet : on ne se rabat PAS sur "dev" par défaut ici (contenu
        # exposé en HTTP), seul un APP_ENV=dev explicite autorise l'affichage.
        environment = os.environ.get("APP_ENV")

    if environment != "dev":
        return None

    return {
        "error": {
            "type":      type(exc).__name__,
            "message":   str(exc),
            "traceback": _traceback.format_exc(),
        }
    }
