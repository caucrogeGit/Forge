# pyright: strict
"""Extraction de métadonnées audio via ffprobe.

``probe_audio`` lance ``ffprobe`` (lecture seule) sur une source et en extrait
durée, codec, bitrate, sample rate et nombre de canaux. Sert aussi de
**validation profonde** : un fichier sans flux audio (ou que ffprobe refuse) est
rejeté — bien plus fiable que l'extension validée à l'upload.

L'exécution de ffprobe est déléguée à un *runner* injectable → le parsing et la
validation sont testables **sans ffprobe réel**. Invocation sûre : arguments en
**liste** (jamais ``shell=True``), chemin en argument, timeout.

Aucun ffmpeg lancé : ffprobe lit, ne transcode pas.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from forge_mvc_audio.config import AudioConfig, load_audio_config

__all__ = ["AudioMetadata", "AudioProbeError", "probe_audio", "parse_probe_json"]

# Un runner prend (ffprobe_bin, path) et retourne la sortie JSON de ffprobe.
ProbeRunner = Callable[[str, str], str]

_PROBE_TIMEOUT_SECONDS = 30


class AudioProbeError(Exception):
    """ffprobe a échoué, ou la source n'est pas un audio exploitable."""


@dataclass(frozen=True)
class AudioMetadata:
    duration_seconds: int | None
    audio_codec: str | None
    bitrate_kbps: int | None
    sample_rate_hz: int | None
    channels: int | None
    container: str | None


def _default_runner(ffprobe_bin: str, path: str) -> str:
    """Lance ffprobe et retourne sa sortie JSON (stdout)."""
    import subprocess

    # Préfixe ./ si le chemin commence par '-' pour qu'il ne soit pas lu comme
    # une option ffprobe (MEDIA-FFMPEG-ARG-HARDENING-001).
    safe_path = f"./{path}" if path.startswith("-") else path
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        safe_path,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_PROBE_TIMEOUT_SECONDS
        )
    except FileNotFoundError as exc:
        raise AudioProbeError(f"ffprobe introuvable : {ffprobe_bin}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioProbeError("ffprobe a dépassé le délai") from exc
    if result.returncode != 0:
        raise AudioProbeError(
            f"ffprobe a échoué (code {result.returncode}) : {result.stderr.strip()}"
        )
    return result.stdout


def _as_dict(value: object) -> dict[str, Any]:
    """Vue typée d'une valeur JSON décodée si c'est un objet, sinon ``{}``."""
    return cast("dict[str, Any]", value) if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    """Vue typée d'une valeur JSON décodée si c'est un tableau, sinon ``[]``."""
    return cast("list[Any]", value) if isinstance(value, list) else []


def _int_or_none(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_probe_json(payload: str | dict[str, Any]) -> AudioMetadata:
    """Parse la sortie ffprobe (``-print_format json``) en ``AudioMetadata``.

    Lève ``AudioProbeError`` si la sortie est illisible ou sans flux audio.
    """
    raw: object = json.loads(payload) if isinstance(payload, str) else payload
    data = _as_dict(raw)
    streams = _as_list(data.get("streams"))
    fmt = _as_dict(data.get("format"))

    audio = next(
        (sd for s in streams if (sd := _as_dict(s)).get("codec_type") == "audio"),
        None,
    )
    if audio is None:
        raise AudioProbeError("aucun flux audio détecté")

    duration = fmt.get("duration") or audio.get("duration")
    bitrate = fmt.get("bit_rate") or audio.get("bit_rate")
    bitrate_kbps = _int_or_none(bitrate)
    if bitrate_kbps is not None:
        bitrate_kbps = bitrate_kbps // 1000

    return AudioMetadata(
        duration_seconds=_int_or_none(duration),
        audio_codec=audio.get("codec_name"),
        bitrate_kbps=bitrate_kbps,
        sample_rate_hz=_int_or_none(audio.get("sample_rate")),
        channels=_int_or_none(audio.get("channels")),
        container=fmt.get("format_name"),
    )


def probe_audio(
    path: str,
    *,
    config: AudioConfig | None = None,
    runner: ProbeRunner | None = None,
) -> AudioMetadata:
    """Sonde ``path`` et retourne ses métadonnées (valide le flux + la durée)."""
    cfg = config or load_audio_config()
    run: ProbeRunner = runner or _default_runner

    meta = parse_probe_json(run(cfg.ffprobe_bin, str(path)))

    if (
        cfg.max_duration_seconds
        and meta.duration_seconds is not None
        and meta.duration_seconds > cfg.max_duration_seconds
    ):
        raise AudioProbeError(
            f"durée {meta.duration_seconds}s > maximum "
            f"{cfg.max_duration_seconds}s (FORGE_AUDIO_MAX_DURATION_SECONDS)"
        )
    return meta
