# pyright: strict
"""Lecture HTTP des fichiers audio — streaming Range, sans état.

Branche une route de **lecture en streaming** sur un ``Router`` Forge :

- ``GET /audio/{uuid}`` — sert le fichier audio en streaming avec support HTTP
  **Range** (seek), via la primitive core ``Response.file``.

Le chemin servi est **retrouvé sur le disque** à partir de l'``uuid`` (préférence
au MP3 transcodé, sinon la source) — jamais depuis l'URL, et l'``uuid`` est
validé comme UUID canonique → aucun *path traversal* possible.

Sécurité (optionnelle, mirror Video/IoT) : si ``FORGE_AUDIO_API_TOKEN`` est
défini, la route exige ``Authorization: Bearer <token>`` ; sinon elle est
ouverte (mode local/pédagogique). L'auth vit dans ce module, **jamais** dans
Forge Core.

Le module reste **opt-in** : l'application appelle ``register_audio_routes``
explicitement. Aucune écriture dans ``mvc/routes.py`` (charte §9).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from core.http.bearer import is_bearer_authorized
from core.http.response import Response

from forge_mvc_audio.config import AudioConfig, load_audio_config
from forge_mvc_audio.storage import resolve_playable_relpath

__all__ = ["AudioHttpController", "register_audio_routes", "ROUTE_PLAYBACK"]

logger = logging.getLogger(__name__)

ROUTE_PLAYBACK = "/audio/{uuid}"

def _error(code: str, status: int) -> Response:
    return Response.json({"error": code}, status=status)


class AudioHttpController:
    """Handler HTTP de lecture audio, sans état (lookup disque par uuid)."""

    def __init__(self, config: AudioConfig, *, api_token: str | None = None) -> None:
        self._config = config
        self._api_token = api_token

    def stream(self, request: Any) -> Response:
        if not is_bearer_authorized(request, self._api_token):
            return _error("unauthorized", 401)

        uuid = request.route("uuid")
        # Chemin retrouvé sur le disque (jamais depuis l'URL) ; uuid validé en
        # interne par resolve_playable_relpath → pas de path traversal.
        rel = resolve_playable_relpath(uuid, storage_root=self._config.storage_root)
        if not rel:
            return _error("not_found", 404)

        path = Path(self._config.storage_root) / rel
        if not path.is_file():
            logger.warning("Forge Audio — fichier absent pour %s : %s", uuid, path)
            return _error("file_missing", 404)

        # Streaming + Range délégués à la primitive core.
        return Response.file(path, request)


def register_audio_routes(
    router: Any,
    *,
    config: AudioConfig | None = None,
) -> Any:
    """Enregistre la route de lecture audio sur un ``Router`` Forge.

    Appelée **explicitement** par l'application. Si ``config.api_token`` est
    défini, la route exige un Bearer token. Retourne le ``router`` (chaînable).
    """
    if config is None:
        config = load_audio_config()
    controller = AudioHttpController(config, api_token=config.api_token)

    router.add(
        "GET", ROUTE_PLAYBACK, controller.stream,
        name="audio_stream",
        public=True, csrf=False, api=False,
    )
    return router
