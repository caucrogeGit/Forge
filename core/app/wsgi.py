# pyright: strict
"""core/app/wsgi.py — Callables WSGI pour Forge.

Tickets :
- WSGI-ENTRYPOINT-001 : `create_wsgi_app(application)` — adaptateur minimal
  qui prend une `Application` déjà construite et retourne un callable WSGI ;
- WSGI-APP-FACTORY-CONFIG-001 : `create_configured_wsgi_app()` — applique la
  configuration de `config.py` (via `core.app.app_factory`) et retourne le
  callable WSGI. Il ne charge PAS ce que `app.py` câble : middlewares et
  magasin de sessions y sont des objets construits, que `config.py` ne porte
  pas. La docstring affirmait le contraire, et c'est ce qui empêchait de
  soupçonner le problème ;
- WSGI-UNARMED-APP-GUARD-001 : d'où le refus. `create_configured_wsgi_app()`
  ne construit plus quand `app.py` câble ce qu'elle ne verra pas (ADR-092) ;
- WSGI-PROD-WARNINGS-001 : `create_configured_wsgi_app()` émet aussi
  les warnings production (`MemorySessionStore` en `APP_ENV=prod`) — une
  seule fois à la construction de l'application, jamais par requête ;
- CORE-WSGI-HEALTH-PARITY-001 : `GET /health` répond `200 {"status": "ok"}`
  ici comme sur le serveur de développement. La sonde figure au contrat de
  stabilité, mais n'était servie que par ce dernier et répondait 404 derrière
  Gunicorn ; la réponse vient désormais de `core.http.health`, source unique ;
- CORE-WSGI-BODY-LIMIT-001 : le corps de requête est contrôlé contre
  `request_size_limit(...)` AVANT d'être lu (aucune allocation pour un
  `Content-Length` au-delà de la limite), il n'est lu que pour les méthodes
  à corps, et son dépassement répond 413 (plus jamais 400).

Usage typique — dans le `wsgi.py` de l'application, servir l'application DÉJÀ
ARMÉE, celle que construit `app.py` :

    from app import application
    from core.app.wsgi import create_wsgi_app

    application = create_wsgi_app(application)

Puis exposer `application` à un serveur WSGI externe (ex.
`gunicorn wsgi:application`).

`create_configured_wsgi_app()` reste la voie d'un projet dont tout le câblage
tient dans `config.py`.

Périmètre :
- ne remplace pas `python app.py` (serveur de développement) ;
- ne sert pas les fichiers statiques (responsabilité du reverse proxy), mais
  sert bien `/media/`, qui passe par une couche applicative que le proxy ne
  saurait pas reproduire (`CORE-WSGI-MEDIA-PARITY-001`) ;
- ajoute le socle de headers de sécurité partagé avec `app.py` via
  `core.security.headers.apply_security_headers` (`WSGI-SECURITY-HEADERS-001`)
  — HSTS conditionné à `wsgi.url_scheme == "https"` ; derrière un reverse
  proxy TLS-terminé, c'est le proxy qui pose HSTS ;
- ne couvre pas la production complète — cf `DOCS-PRODUCTION-LIMITS-001`.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from http import HTTPStatus
from http.client import HTTPMessage
from io import BytesIO
from typing import Any, Iterable

from core.http.health import health_response, is_health_request
from core.http.media import is_media_request, media_response
from core.http.request import (
    BODY_METHODS,
    Request,
    RequestEntityTooLarge,
    request_size_limit,
)
from core.http.response import Response
from core.security import csp as _csp
from core.security.headers import apply_security_headers, assert_headers_are_safe


_REASONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    500: "Internal Server Error",
    # Les trois codes que Forge émet SANS littéral `Response(<code>, ...)`, et
    # qui manquaient : 206 et 416 viennent de `Response.file` (HTTP Range), 503
    # de `_service_unavailable` et de `_api_error`.
    #
    # Ils sont figés ici, et pas laissés à `http.HTTPStatus`, parce que la
    # phrase de raison de la stdlib change avec la version de Python : 416 vaut
    # « Requested Range Not Satisfiable » jusqu'en 3.12 et « Range Not
    # Satisfiable » à partir de 3.13, qui réaligne ces noms sur la RFC 9110.
    #
    # Deux serveurs de production sur des Python différents auraient alors émis
    # deux lignes de statut différentes pour la même réponse. La CI l'a dit en
    # premier, la matrice couvrant 3.12 à 3.14 : ce que Forge émet ne doit
    # dépendre que de Forge. Les formulations retenues sont celles de la RFC
    # 9110, déjà employées par la documentation de `Response.file`.
    206: "Partial Content",
    416: "Range Not Satisfiable",
    503: "Service Unavailable",
}


def _headers_from_environ(environ: dict[str, Any]) -> HTTPMessage:
    """Construit les headers de la requête WSGI, du type qu'attend `Request`.

    Ticket : CORE-WSGI-HEADERS-PARITY-001.

    Le chemin WSGI portait ici une classe maison qui IMITAIT le contrat de
    `http.client.HTTPMessage`, le type que le serveur de développement fournit.
    Une imitation ne vaut que ce que son auteur a prévu, et il manquait dix
    comportements, dont trois qui cassaient du code applicatif ordinaire :

    - `headers.get("X-Absent")` rendait `""` là où `HTTPMessage` rend `None`.
      L'écart traversait l'API publique : `request.header("X-Absent", "repli")`
      rendait `""` en production et `"repli"` en développement, alors que les
      `@overload` de `Request.header` promettent le défaut ;
    - `"X-Header" in headers` levait `TypeError` en production et fonctionnait
      en développement, faute de `__contains__` ;
    - `headers["X-Header"]`, `len(...)` et l'itération levaient `TypeError`.

    Ces défauts ne se voient qu'en production, sur du code qui marche en
    développement. `CORE-WSGI-HEADERS-CONTRACT-001` avait déjà ajouté `keys()`
    et `items()` après un `AttributeError` : c'était la première rustine, le
    ticket 66 du terrain en demandait une deuxième.

    La cause est retirée plutôt que le symptôme (règle A) : les deux serveurs
    emploient désormais le MÊME type, et non deux qui se ressemblent.

    Les valeurs sont posées une à une, sans jamais parser de texte : aucun
    en-tête ne peut en injecter un autre par un saut de ligne.

    Limite, imposée par WSGI et non par Forge : `environ` ne conserve pas la
    casse d'origine des noms (`HTTP_HX_REQUEST` ne dit pas si le client a écrit
    `HX-Request` ou `Hx-Request`). Les noms sont donc restitués en `Title-Case`.
    Toute LECTURE reste insensible à la casse, des deux côtés ; seul l'affichage
    d'un nom par `keys()` peut différer de ce que le client a envoyé.
    """
    headers = HTTPMessage()
    if "CONTENT_TYPE" in environ:
        headers["Content-Type"] = environ["CONTENT_TYPE"]
    if "CONTENT_LENGTH" in environ:
        headers["Content-Length"] = str(environ["CONTENT_LENGTH"])
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            headers[key[5:].replace("_", "-").title()] = value
    return headers


class _WsgiHandlerStub:
    """Stub `handler` minimal pour instancier `core.http.Request`.

    Reproduit les seuls attributs lus par `Request.__init__` :
    `path`, `command`, `headers`, `client_address`, `rfile`.
    """

    def __init__(self, environ: dict[str, Any]) -> None:
        path = environ.get("PATH_INFO", "/") or "/"
        qs = environ.get("QUERY_STRING", "") or ""
        self.path = f"{path}?{qs}" if qs else path
        self.command = environ.get("REQUEST_METHOD", "GET")
        self.headers = _headers_from_environ(environ)
        # nosec B104 — valeur de repli pour l'adresse du CLIENT, lue dans
        # l'environnement WSGI. Aucune socket n'est ouverte ici.
        remote = environ.get("REMOTE_ADDR", "0.0.0.0") or "0.0.0.0"  # nosec B104
        self.client_address = (remote, 0)
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            length = 0
        stream = environ.get("wsgi.input")
        # CORE-WSGI-BODY-LIMIT-001 : le corps n'est lu que pour les méthodes à
        # corps (aligné sur `Request`, qui ignore le corps des autres), et le
        # Content-Length annoncé est contrôlé AVANT toute lecture — un corps
        # trop grand est refusé sans jamais être chargé en mémoire.
        raw = b""
        if length > 0 and stream is not None and self.command in BODY_METHODS:
            content_type = self.headers.get("content-type", "")
            if length > request_size_limit(content_type):
                raise RequestEntityTooLarge(length)
            raw = stream.read(length)
        self.rfile = BytesIO(raw)


def _format_status(code: int) -> str:
    """Statut WSGI `"<code> <raison>"`, jamais un code nu.

    La table ci dessus ne portait ni 206, ni 416, ni 503 : ces codes sortaient
    donc sans phrase de raison, ce que le validateur de la PEP 3333 signale
    (`The status string ('206') should be a three-digit integer followed by a
    single space and a status explanation`). 503 est rendu par le cœur lui même,
    et 206/416 le sont par tout média servi avec un en-tête `Range`, ce que
    `CORE-WSGI-MEDIA-PARITY-001` vient de rendre possible.

    Ces trois codes y figurent désormais, avec une phrase FIXÉE. S'en remettre à
    `http.HTTPStatus` pour eux paraissait plus élégant, et c'était un piège : sa
    phrase change avec la version de Python, si bien que la même réponse sortait
    en « Requested Range Not Satisfiable » sous 3.12 et « Range Not Satisfiable »
    sous 3.13. Ce que Forge émet ne doit dépendre que de Forge.

    `HTTPStatus` reste le repli des codes que Forge n'émet pas lui même, qu'une
    application est libre de rendre : mieux vaut une phrase de la stdlib qu'un
    code nu.
    """
    reason = _REASONS.get(code)
    if reason is None:
        try:
            reason = HTTPStatus(code).phrase
        except ValueError:
            reason = ""
    return f"{code} {reason}".rstrip()


def _response_to_wsgi(
    response: Response,
    start_response: Callable[..., Any],
    *,
    is_https: bool = False,
) -> Iterable[bytes]:
    """Adapte une `Response` Forge en réponse WSGI avec headers de sécurité.

    Les headers de sécurité par défaut (X-Frame-Options, CSP, etc.) sont
    posés en `setdefault` via `core.security.headers.apply_security_headers`
    — une route applicative qui définit explicitement un de ces headers garde
    la main. HSTS est conditionné à `is_https=True` (cf
    `WSGI-SECURITY-HEADERS-001`).
    """
    # Corps : soit un itérable de streaming (Response.file → Range/206,
    # CORE-HTTP-FILE-RANGE-001), soit le `body` bytes habituel. Dans le cas
    # streaming, `Content-Length` vient de `response.content_length` (taille de
    # la tranche servie), pas de `len(body)`.
    stream = getattr(response, "stream", None)
    if stream is not None:
        body_iter: Iterable[bytes] = stream
        content_length = getattr(response, "content_length", None) or 0
    else:
        body = response.body
        body_iter = [body]
        content_length = len(body)

    # On part des headers applicatifs, on superpose les défauts de sécurité,
    # puis on construit la liste WSGI finale. Content-Type / Content-Length
    # restent en tête, calculés ici (jamais issus du dict applicatif).
    headers_dict: dict[str, str] = {str(k): str(v) for k, v in response.headers.items()}
    apply_security_headers(
        headers_dict,
        include_hsts=is_https,
        # Le nonce de la requête en cours, posé par le callable WSGI. `None`
        # quand `APP_CSP_NONCE_ENABLED` est absent, et la CSP reste alors
        # `script-src 'self'`, sans `unsafe-inline`.
        #
        # L'application peut toujours définir sa propre
        # `Content-Security-Policy` dans `response.headers` : le `setdefault`
        # la respecte.
        csp=_csp.build_csp_header(_csp.get_request_nonce()),
    )

    # CORE-HEADER-CRLF-001 : contrôle AVANT `start_response`, tant qu'aucune
    # ligne n'est partie. Un saut de ligne dans une valeur découperait la
    # réponse pour le client.
    assert_headers_are_safe(headers_dict)

    headers: list[tuple[str, str]] = [
        ("Content-Type", response.content_type),
        ("Content-Length", str(content_length)),
    ]
    # Content-Type / Content-Length sont calculés ici : on écarte toute clé
    # homonyme du dict applicatif (comparaison insensible à la casse) pour ne
    # pas émettre deux fois le même en-tête.
    _reserved = {"content-type", "content-length"}
    for key, value in headers_dict.items():
        if key.lower() in _reserved:
            continue
        headers.append((key, value))
    # Cookies additionnels : une ligne Set-Cookie par cookie accumulé via
    # response.add_cookie (CORE-RESPONSE-MULTI-COOKIE-001).
    for cookie in getattr(response, "set_cookies", []):
        headers.append(("Set-Cookie", str(cookie)))
    start_response(_format_status(response.status), headers)
    return body_iter


def create_wsgi_app(
    application: Any,
    *,
    emit_prod_warnings: bool = True,
    logger: logging.Logger | None = None,
) -> Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]:
    """Retourne un callable WSGI qui dispatche via l'`Application` Forge fournie.

    `application` doit exposer `dispatch(request) -> Response`.

    Émet aussi, une seule fois à la construction et jamais par requête, les
    avertissements de production de `core.app.prod_warnings` (magasin de
    sessions en mémoire sous `APP_ENV=prod`).

    Ils vivaient dans `create_configured_wsgi_app` seul. Le point d'entrée
    recommandé étant devenu celui qui sert l'application déjà armée
    (ADR-092), les y laisser aurait fait disparaître l'avertissement du chemin
    que tout le monde suit, sans que personne le remarque. Ils appartiennent au
    passage en WSGI, pas à une fabrique particulière.

    Passer `emit_prod_warnings=False` pour les tests qui ne veulent pas polluer
    le logger.
    """
    if emit_prod_warnings:
        import core.forge as forge
        from core.app.prod_warnings import emit_memory_store_warning_if_needed

        emit_memory_store_warning_if_needed(
            str(forge.get("app_env") or ""),
            forge.get("session_store"),
            logger=logger,
        )

    def app(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        # CORE-WSGI-CSP-NONCE-001 : le nonce est posé pour toute la durée de la
        # requête, exactement comme le fait le serveur de développement. Sans
        # lui, `APP_CSP_NONCE_ENABLED` n'agissait qu'en développement alors que
        # la documentation le prescrit en production, et le script inline d'un
        # gabarit était silencieusement bloqué une fois déployé.
        #
        # L'enveloppe couvre le rendu ET la construction de l'en-tête : le
        # gabarit et la CSP doivent voir la même valeur, faute de quoi le
        # mécanisme ne sert à rien.
        with _csp.request_nonce(
            _csp.generate_nonce() if _csp.nonce_enabled() else None
        ):
            return _repondre(environ, start_response)

    def _repondre(
        environ: dict[str, Any], start_response: Callable[..., Any]
    ) -> Iterable[bytes]:
        is_https = environ.get("wsgi.url_scheme") == "https"
        try:
            handler = _WsgiHandlerStub(environ)
            request = Request(handler)
        except RequestEntityTooLarge:
            # CORE-WSGI-BODY-LIMIT-001 : un corps au-delà de la limite est un
            # 413 explicite (comme le serveur de dev), pas un 400 générique.
            too_large = Response(
                status=413,
                body=b"Payload Too Large",
                content_type="text/plain; charset=utf-8",
            )
            return _response_to_wsgi(too_large, start_response, is_https=is_https)
        except Exception:
            # Même le 400 d'entrée ne doit pas être moins protégé que la
            # réponse nominale : on passe par _response_to_wsgi pour profiter
            # du socle de headers de sécurité.
            bad_request = Response(
                status=400,
                body=b"Bad Request",
                content_type="text/plain; charset=utf-8",
            )
            return _response_to_wsgi(bad_request, start_response, is_https=is_https)
        # CORE-WSGI-HEALTH-PARITY-001 : la sonde du contrat de stabilité, servie
        # avant le routage comme sur le serveur de dev. Elle n'était traitée que
        # par ce dernier, et répondait 404 derrière Gunicorn.
        if is_health_request(request.path):
            return _response_to_wsgi(
                health_response(), start_response, is_https=is_https)
        # CORE-WSGI-MEDIA-PARITY-001 : `/media/` est un préfixe servi avant le
        # routage, comme sur le serveur de développement. Cette interception
        # n'existait que là bas, et une application déployée rendait 404 sur
        # TOUS ses médias, en servant ses pages normalement.
        if is_media_request(request.path):
            return _response_to_wsgi(
                media_response(request.path, request),
                start_response, is_https=is_https)
        response = application.dispatch(request)
        return _response_to_wsgi(response, start_response, is_https=is_https)

    return app


def create_configured_wsgi_app(
    *,
    emit_prod_warnings: bool = True,
    logger: logging.Logger | None = None,
) -> Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]:
    """Construit l'`Application` depuis `config.py` et retourne le callable WSGI.

    Applique la configuration via `core.app.app_factory.build_application`, puis
    enveloppe l'application dans un adaptateur WSGI standard.

    **Ne charge pas ce que `app.py` câble.** `build_application()` lit
    `config.py` et le module de routes ; middlewares et magasin de sessions sont
    des objets construits, que `config.py` ne porte pas. Un projet qui les câble
    dans `app.py`, comme le squelette le prescrit, obtiendrait ici une
    application privée de toutes ses gardes sauf la première.

    D'où le refus posé par l'ADR-092 : quand `app.py` déclare un câblage
    invisible d'ici, cette fonction lève `UnarmedApplicationError` au lieu de
    construire. Servir l'application déjà armée passe par `create_wsgi_app`.

    Garantit que les paramètres `forge.configure(...)` (dont
    `trusted_proxies`) sont appliqués avant que la première requête WSGI
    ne soit dispatched.

    Si `emit_prod_warnings=True` (défaut), émet une seule fois — à la
    construction, pas à chaque requête — les avertissements production
    de `core.app.prod_warnings` (ex. `MemorySessionStore` en `APP_ENV=prod`).
    Passer `emit_prod_warnings=False` pour les tests qui ne veulent pas
    polluer le logger.
    """
    from core.app.app_factory import build_application, project_root
    from core.app.wiring_guard import assert_wiring_is_visible

    # ADR-092 : refuser AVANT de construire. Un `app.py` qui câble des
    # middlewares ou un magasin de sessions les rend invisibles à cette
    # fabrique, qui lit `config.py` et les routes, jamais lui. L'application
    # démarrait alors sans ses gardes, en répondant 200.
    #
    # La vérification est statique (`ast`), jamais un import : importer `app.py`
    # serait exécuter ce que ce chemin cherche justement à éviter.
    racine = project_root()
    if racine is not None:
        assert_wiring_is_visible(racine / "app.py")

    application = build_application()
    # Les avertissements sont emis par `create_wsgi_app`, une seule fois : les
    # emettre ici aussi les doublerait sur ce chemin.
    return create_wsgi_app(
        application, emit_prod_warnings=emit_prod_warnings, logger=logger)
