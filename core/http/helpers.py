# pyright: strict
import logging
import os
from typing import Any
from core.app.env import DEFAULT_APP_ENV, normalize_app_env
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
        env = normalize_app_env(_cfg("app_env"))
    except KeyError:
        env = DEFAULT_APP_ENV

    _logger.warning("template introuvable : %s (vues : %s)", template, views_dir)

    if exc is not None:
        try:
            from core.errors.runtime_error_logger import log_runtime_error
            log_runtime_error(exc)
        except Exception:  # pragma: no cover — défensif
            # Le logger JSONL est best-effort : on ne casse pas la réponse
            # utilisateur si l'écriture échoue.
            pass

    if env == DEFAULT_APP_ENV:
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


def json_error(code: str, status: int, *, message: "str | None" = None) -> Response:
    """Réponse d'erreur JSON, forme unique de Forge (ADR-088).

    ```json
    {"error": "not_found"}
    ```

    `code` est un identifiant stable, lisible par une machine, jamais une
    phrase. `message` reste **facultatif et réservé aux erreurs de
    validation**, seul cas où le client a besoin de savoir quoi corriger. Les
    autres erreurs n'en portent pas, et c'est délibéré : un refus qui explique
    à quelle étape il a eu lieu renseigne l'attaquant.

    Il n'y a pas d'enveloppe de succès en regard. Une réponse de succès rend la
    ressource, le code HTTP portant déjà l'information que `{"success": true}`
    redoublait. C'est la décision de l'ADR-088, prise après avoir constaté que
    l'enveloppe déclarée n'avait aucun adoptant, pas même dans Forge.

    Toute réponse d'erreur JSON du cœur et des opt-ins passe par ici. Un
    garde-fou l'exige, parce que la divergence précédente est née exactement
    de l'absence d'un endroit unique où la forme soit écrite.
    """
    corps: "dict[str, Any]" = {"error": code}
    if message is not None:
        corps["message"] = message
    return json_response(corps, status)


#: Corps de repli des pages d'erreur, par code. Volontairement sobre : à ce
#: stade le gabarit du projet est indisponible, ce n'est pas le moment de
#: solliciter davantage le moteur de rendu.
_REPLIS: "dict[int, str]" = {
    400: "Requete invalide.\n",
    403: "Acces refuse.\n",
    404: "Page introuvable.\n",
    405: "Methode non autorisee.\n",
    500: "Erreur interne du serveur.\n",
    503: "Service momentanement indisponible.\n",
}


def error_page(
    template: str,
    status: int,
    context: "dict[str, Any] | None" = None,
    *,
    fallback: "str | None" = None,
) -> Response:
    """Page d'erreur dont le **code HTTP est garanti**, quoi qu'il arrive au gabarit.

    Les gabarits `errors/*.html` **appartiennent à l'utilisateur** : le squelette
    les livre et Forge n'y réécrit jamais (principe 4). Un projet peut donc les
    casser, ou ne pas les avoir, et cela ne doit pas changer ce que le code de
    statut annonce.

    Deux situations produisaient un `500` à la place du code voulu
    (`CORE-WSGI-CSRF-POST-001`) :

    - **gabarit cassé.** `html` ne rattrape que `TemplateNotFoundError` ; une
      syntaxe Jinja invalide, un filtre inconnu ou une variable absente
      ressortaient ;
    - **gabarit absent.** `html` ne lève pas, il rend une réponse `500`
      explicative, ce qui écrase le code choisi.

    Or le code de statut d'un refus n'est pas cosmétique. Un `403` annonce une
    requête invalide, qu'il ne sert à rien de rejouer ; un `500` annonce une
    panne et invite à réessayer. Un `404` dit qu'une ressource n'existe pas ;
    un `500` dit que le serveur est en défaut. Côté exploitant, la différence
    sépare une vague de fausses pannes d'un fonctionnement normal.

    Le **corps** explicatif de `DX-RENDER-ERROR-001` est conservé quand il
    existe : signaler au développeur qu'un gabarit manque reste utile. Seul le
    code est corrigé. Il n'y a donc pas de divergence entre les environnements,
    et c'en est le point important : un chemin d'erreur qui se comporte
    autrement en développement qu'en production est un chemin qu'on ne teste
    jamais là où il compte.
    """
    try:
        rendue = html(template, status, context)
    except Exception:  # noqa: BLE001 — le gabarit du projet est en défaut
        _logger.exception("Rendu de %s impossible ; repli sur une reponse minimale", template)
        rendue = None

    if rendue is not None and rendue.status == status:
        return rendue

    if rendue is not None and fallback is None:
        # Gabarit absent : `html` a rendu une réponse explicative, mais en 500,
        # ce qui écrase le code voulu. On garde son corps et on rétablit le code.
        #
        # Un `fallback` explicite l'emporte en revanche sur cette explication :
        # l'appelant qui en fournit un a une chose à dire au visiteur que le
        # générique ne peut pas deviner, comme l'invitation à réessayer d'un
        # 503. Le développeur, lui, a déjà l'avertissement au journal.
        return Response(
            status,
            rendue.body,
            content_type=rendue.headers.get("Content-Type", _TEXT_CONTENT_TYPE),
        )

    corps = fallback if fallback is not None else _REPLIS.get(status, "Erreur.\n")
    return Response(status, corps.encode("utf-8"), content_type=_TEXT_CONTENT_TYPE)
