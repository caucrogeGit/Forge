# pyright: strict
"""Configuration Forge Video — VIDEO-ROADMAP-OPEN-001.

Charge la configuration du module vidéo depuis un mapping (``os.environ``
par défaut, ou un dict injecté pour les tests).

Module **pur** : il ne lit aucun fichier, ne lance aucun ``ffmpeg`` et
n'écrit nulle part. Il fixe uniquement le contrat de configuration.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

__all__ = [
    "DEFAULT_FFMPEG_BIN",
    "DEFAULT_FFPROBE_BIN",
    "DEFAULT_STORAGE_ROOT",
    "DEFAULT_MAX_UPLOAD_MB",
    "DEFAULT_MAX_DURATION_SECONDS",
    "ENV_FFMPEG_BIN",
    "ENV_FFPROBE_BIN",
    "ENV_STORAGE_ROOT",
    "ENV_MAX_UPLOAD_MB",
    "ENV_MAX_DURATION_SECONDS",
    "ENV_API_TOKEN",
    "ENV_MAX_TOTAL_MB",
    "ENV_MAX_TOTAL_DURATION_SECONDS",
    "DEFAULT_MAX_TOTAL_MB",
    "DEFAULT_MAX_TOTAL_DURATION_SECONDS",
    "VideoConfigError",
    "VideoConfig",
    "load_video_config",
]

DEFAULT_FFMPEG_BIN = "ffmpeg"
DEFAULT_FFPROBE_BIN = "ffprobe"
DEFAULT_STORAGE_ROOT = "storage/video"
DEFAULT_MAX_UPLOAD_MB = 1000
DEFAULT_MAX_DURATION_SECONDS = 3600
#: Aucun plafond cumulé par défaut : le paquet ne borne pas ce que
#: l'exploitant n'a pas demandé (VIDEO-QUOTA-001).
DEFAULT_MAX_TOTAL_MB: "int | None" = None
DEFAULT_MAX_TOTAL_DURATION_SECONDS: "int | None" = None

ENV_FFMPEG_BIN = "FORGE_VIDEO_FFMPEG_BIN"
ENV_FFPROBE_BIN = "FORGE_VIDEO_FFPROBE_BIN"
ENV_STORAGE_ROOT = "FORGE_VIDEO_STORAGE_ROOT"
ENV_MAX_UPLOAD_MB = "FORGE_VIDEO_MAX_UPLOAD_MB"
ENV_MAX_DURATION_SECONDS = "FORGE_VIDEO_MAX_DURATION_SECONDS"
ENV_API_TOKEN = "FORGE_VIDEO_API_TOKEN"
ENV_MAX_TOTAL_MB = "FORGE_VIDEO_MAX_TOTAL_MB"
ENV_MAX_TOTAL_DURATION_SECONDS = "FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS"


@dataclass(frozen=True)
class VideoConfig:
    """Contrat de configuration du module vidéo."""

    ffmpeg_bin: str = DEFAULT_FFMPEG_BIN
    ffprobe_bin: str = DEFAULT_FFPROBE_BIN
    storage_root: str = DEFAULT_STORAGE_ROOT
    max_upload_mb: int = DEFAULT_MAX_UPLOAD_MB
    max_duration_seconds: int = DEFAULT_MAX_DURATION_SECONDS
    # Plafonds cumulés sur toute la vidéothèque (VIDEO-QUOTA-001). Les deux
    # champs ci dessus bornent UN fichier ; ceux ci bornent leur somme, sans
    # quoi rien n'empêche cinq cents vidéos de neuf cent quatre vingt dix neuf
    # mégaoctets. `None` veut dire « sans plafond ».
    max_total_mb: "int | None" = DEFAULT_MAX_TOTAL_MB
    max_total_duration_seconds: "int | None" = DEFAULT_MAX_TOTAL_DURATION_SECONDS
    # Protection optionnelle des routes de lecture : si défini, un en-tête
    # ``Authorization: Bearer <token>`` est exigé ; sinon les routes sont
    # ouvertes (mode local/pédagogique). None = pas de token.
    api_token: str | None = None


class VideoConfigError(ValueError):
    """Valeur de configuration illisible."""


def _int(source: Mapping[str, str], key: str, default: int) -> int:
    """Entier positif lu dans l'environnement.

    Une valeur illisible **lève** depuis `VIDEO-QUOTA-001`. Elle retombait
    auparavant sur le défaut en silence : `FORGE_VIDEO_MAX_DURATION_SECONDS=7200x`
    donnait 3600, les vidéos de deux heures étaient refusées, et rien n'expliquait
    pourquoi. Le même choix vaut pour le quota de `forge-mvc-files` et pour les
    limites de `forge-mvc-images`.
    """
    raw = source.get(key)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(str(raw).strip())
    except ValueError:
        raise VideoConfigError(
            f"{key} doit être un entier. Reçu : {str(raw).strip()!r}."
        ) from None
    if value <= 0:
        raise VideoConfigError(
            f"{key} doit être strictement positif. Reçu : {value}."
        )
    return value


def _int_or_none(source: Mapping[str, str], key: str) -> "int | None":
    """Entier positif, ou `None` si la variable n'est pas posée.

    `None` et zéro ne se confondent pas : le premier veut dire « sans
    plafond », le second serait « rien n'est autorisé ».
    """
    raw = source.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    return _int(source, key, 0)


def load_video_config(source: Mapping[str, str] | None = None) -> VideoConfig:
    """Construit un ``VideoConfig`` depuis ``source`` (``os.environ`` par défaut)."""
    env = source if source is not None else os.environ
    return VideoConfig(
        ffmpeg_bin=(env.get(ENV_FFMPEG_BIN) or DEFAULT_FFMPEG_BIN).strip(),
        ffprobe_bin=(env.get(ENV_FFPROBE_BIN) or DEFAULT_FFPROBE_BIN).strip(),
        storage_root=(env.get(ENV_STORAGE_ROOT) or DEFAULT_STORAGE_ROOT).strip(),
        max_upload_mb=_int(env, ENV_MAX_UPLOAD_MB, DEFAULT_MAX_UPLOAD_MB),
        max_duration_seconds=_int(
            env, ENV_MAX_DURATION_SECONDS, DEFAULT_MAX_DURATION_SECONDS
        ),
        max_total_mb=_int_or_none(env, ENV_MAX_TOTAL_MB),
        max_total_duration_seconds=_int_or_none(env, ENV_MAX_TOTAL_DURATION_SECONDS),
        api_token=env.get(ENV_API_TOKEN) or None,
    )
