# pyright: strict
import logging
import os
from typing import Any
from core.forge import get as _cfg
from core.http.response import Response
from core.templating.errors import (
    TemplateNotFoundError,
    format_missing_template_dev,
    format_missing_template_prod,
)
from core.templating.manager import template_manager

_TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"

_logger = logging.getLogger(__name__)


def _missing_template_response(
    template: str,
    views_dir: str | None,
    exc: TemplateNotFoundError | None = None,
) -> Response:
    """Construit la réponse pédagogique (dev) ou minimale (prod) — DX-RENDER-ERROR-001.

    Lit `app_env` du registre `core.forge`. Si la clé n'est pas disponible
    (situation de boot incomplet), retombe sur le mode `dev` par défaut,
    ce qui est cohérent avec le défaut du registre.

    Quand `exc` est fourni ET qu'on s'exécute dans un bloc `except` actif,
    on délègue aussi à `log_runtime_error` pour préserver la trace JSONL
    catégorisée `template` utilisée par les outils de diagnostic — sans
    quoi le développeur perdrait la visibilité historique sur ce type
    d'erreur.
    """
    try:
        env = str(_cfg("app_env")).lower()
    except KeyError:
        env = "dev"

    _logger.warning("template introuvable : %s (vues : %s)", template, views_dir)

    if exc is not None:
        try:
            from core.errors.runtime_error_logger import log_runtime_error
            log_runtime_error(exc)
        except Exception:  # pragma: no cover — défensif
            # Le logger JSONL est best-effort : on ne casse pas la réponse
            # utilisateur si l'écriture échoue.
            pass

    if env == "dev":
        body = format_missing_template_dev(template, views_dir)
    else:
        body = format_missing_template_prod()

    return Response(500, body, content_type=_TEXT_CONTENT_TYPE)


def html(template: str, status: int = 200, context: "dict[str, Any] | None" = None, *, raw: bool = False) -> Response:
    # Le 2e argument positionnel est le STATUS, pas le contexte. Sans cette
    # garde, `render(template, {...})` (réflexe d'autres frameworks) mettait un
    # dict dans `status` et provoquait une erreur différée et obscure.
    if not isinstance(status, int) or isinstance(status, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(
            "Le 2e argument positionnel de html()/render() est le STATUS HTTP "
            f"(entier), pas le contexte ; reçu {type(status).__name__} {status!r}. "
            "Passez le contexte par mot-clé : render(template, context={...}) "
            "ou html(template, context={...})."
        )
    if raw:
        views_dir = _cfg("views_dir")
        filepath = os.path.join(views_dir, template)
        # Anti-traversal (SEC-HTML-RAW-TRAVERSAL-001) : le chemin résolu doit
        # rester sous views_dir. Un `template` contenant « ../ » (ou un chemin
        # absolu) sortirait sinon du dossier des vues et pourrait lire un fichier
        # arbitraire. On refuse comme un gabarit introuvable, sans rien révéler.
        base = os.path.realpath(views_dir)
        target = os.path.realpath(filepath)
        if target != base and not target.startswith(base + os.sep):
            return _missing_template_response(
                template, views_dir,
                exc=TemplateNotFoundError(template, views_dir),
            )
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return Response(status, f.read())
        except FileNotFoundError as exc:
            return _missing_template_response(
                template, views_dir,
                exc=TemplateNotFoundError(template, views_dir).with_traceback(exc.__traceback__),
            )

    try:
        body = template_manager.render(template, context or {})
    except TemplateNotFoundError as exc:
        return _missing_template_response(exc.template, exc.views_dir, exc=exc)
    return Response(status, body)


def json_response(data: Any, status: int = 200) -> Response:
    # CORE-JSON-RESPONSE-UNIFY-001 : Response.json est la seule implémentation
    # de la sérialisation JSON (garde TypeError → ValueError, content-type).
    return Response.json(data, status)


def api_success(data: Any = None, status: int = 200, meta: "dict[str, Any] | None" = None) -> Response:
    payload: "dict[str, Any]" = {"success": True, "data": data}
    if meta is not None:
        payload["meta"] = meta
    return json_response(payload, status)


def api_error(message: str, status: int = 400, code: str = "error", details: Any = None) -> Response:
    error: "dict[str, Any]" = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return json_response({"success": False, "error": error}, status)
