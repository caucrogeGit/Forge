# pyright: strict
"""Configuration Forge Audio.

Charge la configuration du module audio depuis un mapping (``os.environ`` par
défaut, ou un dict injecté pour les tests).

Module **pur** : il ne lit aucun fichier, ne lance aucun ``ffmpeg`` et n'écrit
nulle part. Il fixe uniquement le contrat de configuration.
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
    "AudioConfig",
    "load_audio_config",
    "AudioConfigError",
]

DEFAULT_FFMPEG_BIN = "ffmpeg"
DEFAULT_FFPROBE_BIN = "ffprobe"
DEFAULT_STORAGE_ROOT = "storage/audio"
DEFAULT_MAX_UPLOAD_MB = 200
DEFAULT_MAX_DURATION_SECONDS = 7200

ENV_FFMPEG_BIN = "FORGE_AUDIO_FFMPEG_BIN"
ENV_FFPROBE_BIN = "FORGE_AUDIO_FFPROBE_BIN"
ENV_STORAGE_ROOT = "FORGE_AUDIO_STORAGE_ROOT"
ENV_MAX_UPLOAD_MB = "FORGE_AUDIO_MAX_UPLOAD_MB"
ENV_MAX_DURATION_SECONDS = "FORGE_AUDIO_MAX_DURATION_SECONDS"
ENV_API_TOKEN = "FORGE_AUDIO_API_TOKEN"


@dataclass(frozen=True)
class AudioConfig:
    """Contrat de configuration du module audio."""

    ffmpeg_bin: str = DEFAULT_FFMPEG_BIN
    ffprobe_bin: str = DEFAULT_FFPROBE_BIN
    storage_root: str = DEFAULT_STORAGE_ROOT
    max_upload_mb: int = DEFAULT_MAX_UPLOAD_MB
    max_duration_seconds: int = DEFAULT_MAX_DURATION_SECONDS
    # Protection optionnelle des routes de lecture : si défini, un en-tête
    # ``Authorization: Bearer <token>`` est exigé ; sinon les routes sont
    # ouvertes (mode local/pédagogique). None = pas de token.
    api_token: str | None = None


class AudioConfigError(ValueError):
    """Valeur de configuration illisible."""


def _int(source: Mapping[str, str], key: str, default: int) -> int:
    """Entier positif lu dans l'environnement.

    Une valeur illisible **lève** depuis `AUDIO-DOCTOR-HARMONISE-001`. Elle
    retombait sur le défaut en silence, exactement comme le faisait
    `forge-mvc-video` avant `VIDEO-QUOTA-001` :
    `FORGE_AUDIO_MAX_DURATION_SECONDS=7200x` donnait 7200, les fichiers plus
    longs étaient refusés, et rien ne l'expliquait.

    L'harmonisation des deux paquets média porte d'abord sur ce que fait le
    code, pas seulement sur ce qu'affiche `doctor`.
    """
    raw = source.get(key)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(str(raw).strip())
    except ValueError:
        raise AudioConfigError(
            f"{key} doit être un entier. Reçu : {str(raw).strip()!r}."
        ) from None
    if value <= 0:
        raise AudioConfigError(
            f"{key} doit être strictement positif. Reçu : {value}."
        )
    return value


def load_audio_config(source: Mapping[str, str] | None = None) -> AudioConfig:
    """Construit un ``AudioConfig`` depuis ``source`` (``os.environ`` par défaut)."""
    env = source if source is not None else os.environ
    return AudioConfig(
        ffmpeg_bin=(env.get(ENV_FFMPEG_BIN) or DEFAULT_FFMPEG_BIN).strip(),
        ffprobe_bin=(env.get(ENV_FFPROBE_BIN) or DEFAULT_FFPROBE_BIN).strip(),
        storage_root=(env.get(ENV_STORAGE_ROOT) or DEFAULT_STORAGE_ROOT).strip(),
        max_upload_mb=_int(env, ENV_MAX_UPLOAD_MB, DEFAULT_MAX_UPLOAD_MB),
        max_duration_seconds=_int(
            env, ENV_MAX_DURATION_SECONDS, DEFAULT_MAX_DURATION_SECONDS
        ),
        api_token=env.get(ENV_API_TOKEN) or None,
    )
