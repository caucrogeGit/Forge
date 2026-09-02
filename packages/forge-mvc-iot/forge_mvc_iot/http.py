# pyright: strict
"""API HTTP JSON de lecture des événements IoT — IOT-HTTP-API-001.

Branche trois routes GET sur un ``Router`` Forge :

- ``GET /api/iot/events`` — N derniers événements
  (``IotEventRepository.list_recent``).
- ``GET /api/iot/events/{site}/{device_id}`` — événements d'un device
  (``IotEventRepository.find_by_device``).
- ``GET /api/iot/devices/{site}/{device_id}/count`` — compteur
  (``IotEventRepository.count_by_device``).

Aucun SQL n'est écrit dans les handlers : toute la lecture passe par le
repository. Le module reste **opt-in** : l'application appelle
explicitement ``register_iot_routes(router)`` pour les enregistrer.
Aucune modification automatique de ``mvc/routes/__init__.py``.

Sécurité (IOT-HTTP-API-AUTH-001) : protection **optionnelle** par token
Bearer. Si ``FORGE_IOT_API_TOKEN`` est défini, les trois routes exigent
un en-tête ``Authorization: Bearer <token>`` ; sinon l'API reste ouverte
(mode local/pédagogique). L'auth vit dans ce module IoT, **jamais** dans
Forge Core.

Sécuriser par défaut (SEC-IOT-TOKEN-PROD-001) : en ``APP_ENV=prod``,
``register_iot_routes`` **refuse** le mode ouvert (sans token) et lève une
erreur actionnable ; le mode ouvert ne vaut que hors production.

Hors périmètre :

- pas de JWT/OAuth/session, pas de RBAC, pas de refresh token ;
- pas d'ingestion HTTP (``POST``/downlink) ;
- pas de pagination par offset ;
- pas de filtres temporels ``since``/``until`` ;
- pas de dashboard HTML ni d'intégration Forge Design.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from core.app.env import is_prod as _is_prod
from core.forge import get as _forge_get
from core.http.bearer import extract_bearer_token, is_bearer_authorized
from core.http.helpers import json_error
from core.http.response import Response

from forge_mvc_iot.access import (
    ACTION_READ_AGGREGATES,
    ACTION_READ_EVENTS,
    is_read_allowed,
)
from forge_mvc_iot.aggregates import (
    IotAggregateError,
    aggregate_for_device,
    aggregate_for_site,
)
from forge_mvc_iot.tokens import GLOBAL_SCOPE, IotScope, IotTokenRepository
from forge_mvc_iot.config import IotConfig, load_iot_config
from forge_mvc_iot.storage.repository import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    IotEventRepository,
)

__all__ = [
    "IotHttpController",
    "register_iot_routes",
    "ROUTE_LIST_EVENTS",
    "ROUTE_EVENTS_BY_DEVICE",
    "ROUTE_DEVICE_COUNT",
    "ROUTE_SITE_AGGREGATE",
    "ROUTE_DEVICE_AGGREGATE",
]

logger = logging.getLogger(__name__)

# ── Constantes de route ─────────────────────────────────────────────────────

#: Fenêtre d'agrégat par défaut, en heures.
DEFAULT_WINDOW_HOURS = 24

ROUTE_LIST_EVENTS = "/api/iot/events"
ROUTE_EVENTS_BY_DEVICE = "/api/iot/events/{site}/{device_id}"
ROUTE_DEVICE_COUNT = "/api/iot/devices/{site}/{device_id}/count"
#: Agrégats sur une fenêtre (IOT-AGGREGATES-001).
ROUTE_SITE_AGGREGATE = "/api/iot/sites/{site}/aggregate/{kind}"
ROUTE_DEVICE_AGGREGATE = "/api/iot/devices/{site}/{device_id}/aggregate/{kind}"

# Codes d'erreur HTTP exposés dans le JSON — taxonomie stable.
ERROR_INVALID_LIMIT = "invalid_limit"
ERROR_INTERNAL = "internal_server_error"
ERROR_UNAUTHORIZED = "unauthorized"

# ── Erreurs internes (capturées dans le contrôleur, jamais propagées) ──────


class _BadLimit(Exception):
    """Levée par ``_parse_limit`` en cas de paramètre limit invalide.

    Détail privé du module : capturé immédiatement par le contrôleur
    pour produire une réponse 400 propre.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ── Helpers de sérialisation ────────────────────────────────────────────────


def _iso_utc(dt: datetime) -> str:
    """Sérialise un ``datetime`` en ISO 8601 UTC avec suffixe ``Z``.

    - ``datetime`` naïf → interprété comme UTC ;
    - ``datetime`` UTC-aware → reformaté avec ``Z`` (plutôt que ``+00:00``) ;
    - autre fuseau → converti en UTC puis formaté avec ``Z``.
    """
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    utc_dt = dt.astimezone(UTC).replace(tzinfo=None)
    return utc_dt.isoformat() + "Z"


def _serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Transforme un dict repository en dict JSON-friendly.

    Le seul vrai travail est sérialiser ``received_at`` (``datetime``)
    en chaîne ISO. ``metadata`` est déjà un dict (ou ``None``) côté
    repository, donc JSON-friendly. ``metadata_json`` (interne
    stockage) n'apparaît jamais ici.
    """
    received_at = event["received_at"]
    if isinstance(received_at, datetime):
        received_at = _iso_utc(received_at)
    # Pour les autres types (str venant d'un mock, ou None), on laisse
    # tel quel — le sérialiseur JSON s'en charge.
    return {
        "id": event["id"],
        "site": event["site"],
        "device_id": event["device_id"],
        "kind": event["kind"],
        "value": event["value"],
        "unit": event["unit"],
        "timestamp": event["timestamp"],
        "metadata": event["metadata"],
        "received_at": received_at,
    }


# ── Helpers de validation ───────────────────────────────────────────────────


def _parse_limit(request: Any) -> int:
    """Lit et valide ``?limit=`` depuis la requête.

    - absent → ``DEFAULT_LIMIT`` ;
    - non convertible en ``int`` → ``_BadLimit`` ;
    - hors plage ``1..MAX_LIMIT`` → ``_BadLimit``.
    """
    raw = request.query("limit", default=None)
    if raw is None or raw == "":
        return DEFAULT_LIMIT
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise _BadLimit(
            f"limit doit être un entier (vu : {raw!r})"
        ) from exc
    if value < 1:
        raise _BadLimit(f"limit doit être >= 1 (vu : {value})")
    if value > MAX_LIMIT:
        raise _BadLimit(f"limit doit être <= {MAX_LIMIT} (vu : {value})")
    return value


# ── Helpers de réponses d'erreur ────────────────────────────────────────────


def _bad_limit_response(exc: _BadLimit) -> Response:
    # Seul cas où un `message` accompagne le code : une erreur de validation,
    # où le client a besoin de savoir quoi corriger (ADR-088).
    return json_error(ERROR_INVALID_LIMIT, 400, message=exc.message)


def _internal_error_response() -> Response:
    # Réponse sobre — aucune fuite SQL/stacktrace côté client.
    return json_error(ERROR_INTERNAL, 500)


def _forbidden_response() -> Response:
    """Le jeton est valide mais n'ouvre pas ce qui est demandé.

    Distinct du 401 : renvoyer 401 ferait croire au porteur que son jeton est
    faux, et il le remplacerait au lieu d'en demander un dont la portée
    convient. Le 403 ne dit pas davantage ce qui existe.
    """
    return json_error("forbidden", 403)


def _unauthorized_response() -> Response:
    # Réponse sobre : on n'indique jamais si c'est le header, le schéma ou
    # le token qui est en cause, et on ne renvoie évidemment pas le token.
    return json_error(ERROR_UNAUTHORIZED, 401)


# ── Contrôleur ──────────────────────────────────────────────────────────────


class IotHttpController:
    """Handlers HTTP branchés sur un ``IotEventRepository``.

    Le contrôleur est volontairement fin : il valide le limit, délègue
    au repository, sérialise la réponse. Aucune lecture SQL directe.
    """

    def __init__(
        self,
        repository: IotEventRepository,
        *,
        api_token: str | None = None,
        token_repository: "IotTokenRepository | None" = None,
    ) -> None:
        self._repo = repository
        self._api_token = api_token
        self._tokens = token_repository

    def _scope(self, request: Any) -> "IotScope | None":
        """Portée du porteur, ou `None` s'il n'est pas autorisé.

        **Sans registre de jetons, le comportement est celui d'avant
        `IOT-DEVICE-AUTH-001`** : le jeton d'environnement suffit, et son
        absence laisse l'API ouverte, ce que `register_iot_routes` refuse déjà
        en production.

        Le registre s'active en le passant à `register_iot_routes`. Il n'est
        pas monté d'office : le monter exigerait un jeton là où l'API était
        ouverte, et casserait sans le dire les déploiements existants. Le
        principe 3 veut que ce changement soit demandé, pas deviné.

        Une fois le registre actif, l'ordre est le suivant. Le jeton
        d'environnement, s'il est défini, donne la portée **globale** : le
        retirer serait une rupture d'API publique. Sinon le jeton présenté est
        cherché dans la table, et donne la portée qu'il déclare.
        """
        if self._api_token is not None and is_bearer_authorized(request, self._api_token):
            return GLOBAL_SCOPE

        if self._tokens is None:
            # Chemin historique : ouvert si aucun jeton n'est configuré.
            if self._api_token is None:
                return GLOBAL_SCOPE
            return None

        presente = extract_bearer_token(request)
        if not presente:
            return None
        try:
            return self._tokens.resolve(presente)
        except Exception:
            logger.exception("Forge IoT — erreur DB sur la résolution du jeton")
            return None

    def list_events(self, request: Any) -> Response:
        portee = self._scope(request)
        if portee is None:
            return _unauthorized_response()
        if not is_read_allowed(request, portee, ACTION_READ_EVENTS):
            return _forbidden_response()
        try:
            limit = _parse_limit(request)
        except _BadLimit as exc:
            return _bad_limit_response(exc)
        try:
            if portee.is_global:
                # Chemin inchangé pour une portée globale. Un dépôt fourni par
                # l'application et écrit avant `IOT-DEVICE-AUTH-001` n'expose
                # pas `list_recent_scoped` : lui imposer la nouvelle méthode
                # serait une rupture d'API publique hors release majeure, que
                # la règle C de la charte refuse.
                events = self._repo.list_recent(limit=limit)
            else:
                # Le filtre est posé en SQL : rapatrier les mesures des autres
                # sites pour les écarter ensuite les ferait passer par un
                # processus qui n'y a pas droit.
                events = self._repo.list_recent_scoped(
                    site=portee.site, device_id=portee.device_id, limit=limit
                )
        except Exception:
            logger.exception("Forge IoT — erreur DB sur list_recent")
            return _internal_error_response()
        return Response.json(
            {"events": [_serialize_event(ev) for ev in events]},
        )

    def find_by_device(self, request: Any) -> Response:
        portee = self._scope(request)
        if portee is None:
            return _unauthorized_response()
        site = request.route("site")
        device_id = request.route("device_id")
        if not portee.allows(site, device_id):
            return _forbidden_response()
        if not is_read_allowed(request, portee, ACTION_READ_EVENTS):
            return _forbidden_response()
        try:
            limit = _parse_limit(request)
        except _BadLimit as exc:
            return _bad_limit_response(exc)
        try:
            events = self._repo.find_by_device(site, device_id, limit=limit)
        except Exception:
            logger.exception(
                "Forge IoT — erreur DB sur find_by_device(%r, %r)",
                site, device_id,
            )
            return _internal_error_response()
        return Response.json(
            {"events": [_serialize_event(ev) for ev in events]},
        )

    def count_by_device(self, request: Any) -> Response:
        portee = self._scope(request)
        if portee is None:
            return _unauthorized_response()
        site = request.route("site")
        device_id = request.route("device_id")
        if not portee.allows(site, device_id):
            return _forbidden_response()
        if not is_read_allowed(request, portee, ACTION_READ_EVENTS):
            return _forbidden_response()
        try:
            count = self._repo.count_by_device(site, device_id)
        except Exception:
            logger.exception(
                "Forge IoT — erreur DB sur count_by_device(%r, %r)",
                site, device_id,
            )
            return _internal_error_response()
        return Response.json(
            {"site": site, "device_id": device_id, "count": count},
        )


    def _aggregate(self, request: Any, *, by_device: bool) -> Response:
        """Agrégat sur une fenêtre, pour un site ou un équipement."""
        portee = self._scope(request)
        if portee is None:
            return _unauthorized_response()
        site = request.route("site")
        device_id = request.route("device_id") if by_device else None
        if not portee.allows(site, device_id):
            return _forbidden_response()
        if not is_read_allowed(request, portee, ACTION_READ_AGGREGATES):
            return _forbidden_response()

        kind = request.route("kind")
        brut = request.query("hours", None) if hasattr(request, "query") else None
        try:
            heures = int(str(brut)) if brut not in (None, "") else DEFAULT_WINDOW_HOURS
        except (TypeError, ValueError):
            return json_error("invalid_hours", 400)

        try:
            if by_device:
                agregat = aggregate_for_device(site, device_id or "", kind, hours=heures)
            else:
                agregat = aggregate_for_site(site, kind, hours=heures)
        except IotAggregateError as exc:
            return json_error(str(exc), 400)
        except Exception:
            logger.exception("Forge IoT — erreur DB sur l'agrégat")
            return _internal_error_response()

        charge: dict[str, Any] = {
            "site": site, "kind": kind, "hours": heures, **agregat.as_dict(),
        }
        if by_device:
            charge["device_id"] = device_id
        return Response.json(charge)

    def site_aggregate(self, request: Any) -> Response:
        return self._aggregate(request, by_device=False)

    def device_aggregate(self, request: Any) -> Response:
        return self._aggregate(request, by_device=True)


# ── Point d'entrée public ───────────────────────────────────────────────────


def register_iot_routes(
    router: Any,
    *,
    repository: IotEventRepository | None = None,
    config: IotConfig | None = None,
    token_repository: "IotTokenRepository | None" = None,
) -> None:
    """Enregistre les routes Forge IoT sur un ``Router`` Forge.

    L'application appelle cette fonction **explicitement** depuis son
    ``mvc/routes/__init__.py`` — Forge Core n'enregistre rien automatiquement.

    Parameters
    ----------
    router:
        Instance ``core.http.router.Router`` (ou compatible).
    repository:
        ``IotEventRepository`` à utiliser. Par défaut, instancié sans
        adapter (donc avec ``core.database.db``).
    config:
        ``IotConfig`` source du ``api_token``. Par défaut, chargé via
        ``load_iot_config()`` (lecture de l'environnement). Si
        ``config.api_token`` est défini, les routes exigent un Bearer
        token ; sinon l'API reste ouverte.

    Example
    -------
    ::

        from core.http.router import Router
        from forge_mvc_iot.http import register_iot_routes

        router = Router()
        register_iot_routes(router)
    """
    if repository is None:
        repository = IotEventRepository()
    if config is None:
        config = load_iot_config()

    # Sécuriser par défaut (principe 7) : l'API ouverte (sans token) est réservée
    # au développement. En production, l'exposer sans Bearer token serait une
    # fuite de données IoT — on refuse explicitement plutôt que d'exposer.
    if config.api_token is None and _is_prod(_forge_get("app_env")):
        raise RuntimeError(
            "API IoT ouverte interdite en production : définir FORGE_IOT_API_TOKEN "
            "pour exiger un Bearer token, ou n'enregistrer les routes IoT qu'en "
            "environnement de développement (le mode ouvert est local/pédagogique)."
        )

    # IOT-DEVICE-AUTH-001 : le registre de jetons s'active en le passant ici,
    # jamais d'office. Le monter par défaut exigerait un jeton là où l'API
    # était ouverte, et casserait sans le dire les déploiements existants.
    #
    #     register_iot_routes(router, token_repository=IotTokenRepository())
    #
    # Un projet qui ne le passe pas garde exactement le comportement d'avant.
    controller = IotHttpController(
        repository, api_token=config.api_token, token_repository=token_repository
    )

    router.add(
        "GET", ROUTE_LIST_EVENTS, controller.list_events,
        name="iot_events_list",
        public=True, csrf=False, api=True,
    )
    router.add(
        "GET", ROUTE_EVENTS_BY_DEVICE, controller.find_by_device,
        name="iot_events_by_device",
        public=True, csrf=False, api=True,
    )
    router.add(
        "GET", ROUTE_DEVICE_COUNT, controller.count_by_device,
        name="iot_devices_count",
        public=True, csrf=False, api=True,
    )
    router.add(
        "GET", ROUTE_SITE_AGGREGATE, controller.site_aggregate,
        name="iot_site_aggregate",
        public=True, csrf=False, api=True,
    )
    router.add(
        "GET", ROUTE_DEVICE_AGGREGATE, controller.device_aggregate,
        name="iot_device_aggregate",
        public=True, csrf=False, api=True,
    )
