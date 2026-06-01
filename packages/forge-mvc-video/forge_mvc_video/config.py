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
    "VideoConfig",
    "load_video_config",
]

DEFAULT_FFMPEG_BIN = "ffmpeg"
DEFAULT_FFPROBE_BIN = "ffprobe"
DEFAULT_STORAGE_ROOT = "storage/video"
DEFAULT_MAX_UPLOAD_MB = 1000
DEFAULT_MAX_DURATION_SECONDS = 3600

ENV_FFMPEG_BIN = "FORGE_VIDEO_FFMPEG_BIN"
ENV_FFPROBE_BIN = "FORGE_VIDEO_FFPROBE_BIN"
ENV_STORAGE_ROOT = "FORGE_VIDEO_STORAGE_ROOT"
ENV_MAX_UPLOAD_MB = "FORGE_VIDEO_MAX_UPLOAD_MB"
ENV_MAX_DURATION_SECONDS = "FORGE_VIDEO_MAX_DURATION_SECONDS"


@dataclass(frozen=True)
class VideoConfig:
    """Contrat de configuration du module vidéo."""

    ffmpeg_bin: str = DEFAULT_FFMPEG_BIN
    ffprobe_bin: str = DEFAULT_FFPROBE_BIN
    storage_root: str = DEFAULT_STORAGE_ROOT
    max_upload_mb: int = DEFAULT_MAX_UPLOAD_MB
    max_duration_seconds: int = DEFAULT_MAX_DURATION_SECONDS


def _int(source: Mapping[str, str], key: str, default: int) -> int:
    raw = source.get(key)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(str(raw).strip())
    except ValueError:
        return default
    return value if value > 0 else default


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
    )
