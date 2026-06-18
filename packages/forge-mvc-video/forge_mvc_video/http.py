# pyright: strict
"""Lecture HTTP des vidéos — VIDEO-PLAYBACK-RANGE-001.

Branche une route de **lecture en streaming** sur un ``Router`` Forge :

- ``GET /videos/{uuid}`` — sert le fichier vidéo en streaming avec support
  HTTP **Range** (seek), via la primitive core ``Response.file``.

Le chemin servi vient **de la base** (``mp4_path`` si la vidéo est transcodée,
sinon ``original_path``), jamais de l'URL → aucun *path traversal* possible
(l'``uuid`` n'est qu'une clé de lookup).

Sécurité (optionnelle, mirror IoT) : si ``FORGE_VIDEO_API_TOKEN`` est défini,
la route exige ``Authorization: Bearer <token>`` ; sinon elle est ouverte
(mode local/pédagogique). L'auth vit dans ce module, **jamais** dans Forge Core.

Le module reste **opt-in** : l'application appelle ``register_video_routes``
explicitement (couche ``optins/video/``). Aucune écriture dans ``mvc/routes.py``.
"""
from __future__ import annotations

import logging
import secrets
from pathlib import Path
from typing import Any

from core.http.response import Response

from forge_mvc_video.config import VideoConfig, load_video_config
from forge_mvc_video.storage.repository import VideoRepository

__all__ = ["VideoHttpController", "register_video_routes", "ROUTE_PLAYBACK"]

logger = logging.getLogger(__name__)

ROUTE_PLAYBACK = "/videos/{uuid}"

_BEARER_PREFIX = "Bearer "


def _extract_bearer_token(request: Any) -> str | None:
    header = request.header("Authorization", None)
    if not header or not header.startswith(_BEARER_PREFIX):
        return None
    return header[len(_BEARER_PREFIX):]


def _is_authorized(request: Any, api_token: str | None) -> bool:
    """Ouvert si ``api_token is None`` ; sinon Bearer == token (temps constant)."""
    if api_token is None:
        return True
    provided = _extract_bearer_token(request)
    if provided is None:
        return False
    return secrets.compare_digest(provided, api_token)


def _error(code: str, status: int) -> Response:
    return Response.json({"error": code}, status=status)


class VideoHttpController:
    """Handlers HTTP branchés sur un ``VideoRepository`` + un stockage."""

    def __init__(
        self,
        repository: VideoRepository,
        config: VideoConfig,
        *,
        api_token: str | None = None,
    ) -> None:
        self._repo = repository
        self._config = config
        self._api_token = api_token

    def stream(self, request: Any) -> Response:
        if not _is_authorized(request, self._api_token):
            return _error("unauthorized", 401)

        uuid = request.route("uuid")
        try:
            row = self._repo.get_by_uuid(uuid)
        except Exception:
            logger.exception("Forge Video — erreur DB sur get_by_uuid")
            return _error("internal_server_error", 500)

        if row is None:
            return _error("not_found", 404)

        # Chemin issu de la BASE (jamais de l'URL) : mp4 transcodé si dispo,
        # sinon la source. Pas de path traversal possible.
        rel = row.get("mp4_path") or row.get("original_path")
        if not rel:
            return _error("not_available", 409)

        path = Path(self._config.storage_root) / rel
        if not path.is_file():
            logger.warning("Forge Video — fichier absent pour %s : %s", uuid, path)
            return _error("file_missing", 404)

        # Streaming + Range délégués à la primitive core.
        return Response.file(path, request)


def register_video_routes(
    router: Any,
    *,
    repository: VideoRepository | None = None,
    config: VideoConfig | None = None,
) -> Any:
    """Enregistre la route de lecture vidéo sur un ``Router`` Forge.

    Appelée **explicitement** par l'application (couche ``optins/video/``).
    Si ``config.api_token`` est défini, la route exige un Bearer token.
    Retourne le ``router`` (chaînable).
    """
    if config is None:
        config = load_video_config()
    if repository is None:
        repository = VideoRepository()
    controller = VideoHttpController(repository, config, api_token=config.api_token)

    router.add(
        "GET", ROUTE_PLAYBACK, controller.stream,
        name="video_stream",
        public=True, csrf=False, api=False,
    )
    return router
