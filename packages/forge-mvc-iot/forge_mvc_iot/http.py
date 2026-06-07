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
Aucune modification automatique de ``mvc/routes.py``.

Sécurité (IOT-HTTP-API-AUTH-001) : protection **optionnelle** par token
Bearer. Si ``FORGE_IOT_API_TOKEN`` est défini, les trois routes exigent
un en-tête ``Authorization: Bearer <token>`` ; sinon l'API reste ouverte
(mode local/pédagogique). L'auth vit dans ce module IoT, **jamais** dans
Forge Core.

Hors périmètre :

- pas de JWT/OAuth/session, pas de RBAC, pas de refresh token ;
- pas d'ingestion HTTP (``POST``/downlink) ;
- pas de pagination par offset ;
- pas de filtres temporels ``since``/``until`` ;
- pas de dashboard HTML ni d'intégration Forge Design.
"""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime
from typing import Any

from core.http.response import Response

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
]

logger = logging.getLogger(__name__)

# ── Constantes de route ─────────────────────────────────────────────────────

ROUTE_LIST_EVENTS = "/api/iot/events"
ROUTE_EVENTS_BY_DEVICE = "/api/iot/events/{site}/{device_id}"
ROUTE_DEVICE_COUNT = "/api/iot/devices/{site}/{device_id}/count"

# Codes d'erreur HTTP exposés dans le JSON — taxonomie stable.
ERROR_INVALID_LIMIT = "invalid_limit"
ERROR_INTERNAL = "internal_server_error"
ERROR_UNAUTHORIZED = "unauthorized"

# Schéma d'autorisation attendu (exactement « Bearer <token> »).
_BEARER_PREFIX = "Bearer "


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
    return Response.json(
        {"error": ERROR_INVALID_LIMIT, "message": exc.message},
        status=400,
    )


def _internal_error_response() -> Response:
    # Réponse sobre — aucune fuite SQL/stacktrace côté client.
    return Response.json(
        {"error": ERROR_INTERNAL},
        status=500,
    )


def _unauthorized_response() -> Response:
    # Réponse sobre : on n'indique jamais si c'est le header, le schéma ou
    # le token qui est en cause, et on ne renvoie évidemment pas le token.
    return Response.json(
        {"error": ERROR_UNAUTHORIZED},
        status=401,
    )


# ── Authentification optionnelle par Bearer token ──────────────────────────


def _extract_bearer_token(request: Any) -> str | None:
    """Extrait le token d'un en-tête ``Authorization: Bearer <token>``.

    Retourne ``None`` si l'en-tête est absent ou si le schéma n'est pas
    exactement ``Bearer `` (comparaison de schéma non secrète).
    """
    header = request.header("Authorization", None)
    if not header or not header.startswith(_BEARER_PREFIX):
        return None
    return header[len(_BEARER_PREFIX):]


def _is_authorized(request: Any, api_token: str | None) -> bool:
    """Autorise la requête.

    - ``api_token is None`` → API ouverte (mode local/pédagogique) ;
    - sinon, exige un Bearer token égal au token configuré, comparé avec
      ``secrets.compare_digest`` (temps constant).
    """
    if api_token is None:
        return True
    provided = _extract_bearer_token(request)
    if provided is None:
        return False
    return secrets.compare_digest(provided, api_token)


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
    ) -> None:
        self._repo = repository
        self._api_token = api_token

    def list_events(self, request: Any) -> Response:
        if not _is_authorized(request, self._api_token):
            return _unauthorized_response()
        try:
            limit = _parse_limit(request)
        except _BadLimit as exc:
            return _bad_limit_response(exc)
        try:
            events = self._repo.list_recent(limit=limit)
        except Exception:
            logger.exception("Forge IoT — erreur DB sur list_recent")
            return _internal_error_response()
        return Response.json(
            {"events": [_serialize_event(ev) for ev in events]},
        )

    def find_by_device(self, request: Any) -> Response:
        if not _is_authorized(request, self._api_token):
            return _unauthorized_response()
        site = request.route("site")
        device_id = request.route("device_id")
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
        if not _is_authorized(request, self._api_token):
            return _unauthorized_response()
        site = request.route("site")
        device_id = request.route("device_id")
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


# ── Point d'entrée public ───────────────────────────────────────────────────


def register_iot_routes(
    router: Any,
    *,
    repository: IotEventRepository | None = None,
    config: IotConfig | None = None,
) -> None:
    """Enregistre les routes Forge IoT sur un ``Router`` Forge.

    L'application appelle cette fonction **explicitement** depuis son
    ``mvc/routes.py`` — Forge Core n'enregistre rien automatiquement.

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
    controller = IotHttpController(repository, api_token=config.api_token)

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
