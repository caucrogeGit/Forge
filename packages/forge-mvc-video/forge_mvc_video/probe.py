"""Extraction de métadonnées vidéo via ffprobe — VIDEO-PROBE-METADATA-001.

``probe_video`` lance ``ffprobe`` (lecture seule) sur une source et en extrait
durée, dimensions et codecs. Sert aussi de **validation profonde** : un fichier
sans flux vidéo (ou que ffprobe refuse) est rejeté — bien plus fiable que
l'extension validée à l'upload.

L'exécution de ffprobe est déléguée à un *runner* injectable → le parsing et la
validation sont testables **sans ffprobe réel**. Invocation sûre : arguments en
**liste** (jamais ``shell=True``), chemin en argument, timeout.

Aucun ffmpeg lancé : ffprobe lit, ne transcode pas.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from forge_mvc_video.config import VideoConfig, load_video_config

__all__ = ["VideoMetadata", "VideoProbeError", "probe_video", "parse_probe_json"]

# Un runner prend (ffprobe_bin, path) et retourne la sortie JSON de ffprobe.
ProbeRunner = Callable[[str, str], str]

_PROBE_TIMEOUT_SECONDS = 30


class VideoProbeError(Exception):
    """ffprobe a échoué, ou la source n'est pas une vidéo exploitable."""


@dataclass(frozen=True)
class VideoMetadata:
    duration_seconds: int | None
    width: int | None
    height: int | None
    video_codec: str | None
    audio_codec: str | None
    container: str | None


def _default_runner(ffprobe_bin: str, path: str) -> str:
    """Lance ffprobe et retourne sa sortie JSON (stdout)."""
    import subprocess

    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_PROBE_TIMEOUT_SECONDS
        )
    except FileNotFoundError as exc:
        raise VideoProbeError(f"ffprobe introuvable : {ffprobe_bin}") from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoProbeError("ffprobe a dépassé le délai") from exc
    if result.returncode != 0:
        raise VideoProbeError(
            f"ffprobe a échoué (code {result.returncode}) : {result.stderr.strip()}"
        )
    return result.stdout


def _int_or_none(value) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_probe_json(payload: str | dict) -> VideoMetadata:
    """Parse la sortie ffprobe (``-print_format json``) en ``VideoMetadata``.

    Lève ``VideoProbeError`` si la sortie est illisible ou sans flux vidéo.
    """
    data = json.loads(payload) if isinstance(payload, str) else payload
    streams = data.get("streams", []) if isinstance(data, dict) else []
    fmt = data.get("format", {}) if isinstance(data, dict) else {}

    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise VideoProbeError("aucun flux vidéo détecté")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = fmt.get("duration") or video.get("duration")
    return VideoMetadata(
        duration_seconds=_int_or_none(duration),
        width=_int_or_none(video.get("width")),
        height=_int_or_none(video.get("height")),
        video_codec=video.get("codec_name"),
        audio_codec=audio.get("codec_name") if audio else None,
        container=fmt.get("format_name"),
    )


def probe_video(
    path: str,
    *,
    config: VideoConfig | None = None,
    runner: ProbeRunner | None = None,
) -> VideoMetadata:
    """Sonde ``path`` et retourne ses métadonnées (valide le conteneur + la durée)."""
    cfg = config or load_video_config()
    run: ProbeRunner = runner or _default_runner

    meta = parse_probe_json(run(cfg.ffprobe_bin, str(path)))

    if (
        cfg.max_duration_seconds
        and meta.duration_seconds is not None
        and meta.duration_seconds > cfg.max_duration_seconds
    ):
        raise VideoProbeError(
            f"durée {meta.duration_seconds}s > maximum "
            f"{cfg.max_duration_seconds}s (FORGE_VIDEO_MAX_DURATION_SECONDS)"
        )
    return meta
