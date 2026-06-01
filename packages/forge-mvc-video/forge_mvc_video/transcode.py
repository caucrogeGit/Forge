"""Runner ffmpeg : transcodage MP4 + poster — VIDEO-FFMPEG-RUNNER-001.

Construit et exécute les commandes ffmpeg du profil standard Forge Video. Les
constructeurs de commande sont **purs** (testables sans ffmpeg) ; l'exécution
est déléguée à un *runner* injectable.

Sécurité d'invocation :
- arguments en **liste** (jamais ``shell=True``) → aucune injection ;
- chemins passés en arguments (le caller fournit des chemins uuid-based,
  jamais le nom de fichier utilisateur) ;
- ``timeout`` obligatoire (un ffmpeg sans borne peut tourner indéfiniment).

Profil MP4 standard (le détail clé : ``-movflags +faststart`` rend le MP4
lisible en streaming progressif — moov atom au début) :

    -c:v libx264 -preset medium -crf 23
    -c:a aac -b:a 128k -ac 2
    -vf scale='min(1920,iw)':-2     (downscale si > 1080p, jamais d'upscale)
    -movflags +faststart
    -map_metadata -1                (retire les métadonnées d'origine)
"""
from __future__ import annotations

from collections.abc import Callable

__all__ = [
    "FfmpegError",
    "DEFAULT_TRANSCODE_TIMEOUT",
    "DEFAULT_POSTER_TIMEOUT",
    "build_transcode_command",
    "build_poster_command",
    "transcode_to_mp4",
    "generate_poster",
]

# Un runner prend (cmd, timeout) et retourne (returncode, stderr).
FfmpegRunner = Callable[[list[str], int], tuple[int, str]]

DEFAULT_TRANSCODE_TIMEOUT = 3600  # 1 h — borne haute d'un transcodage
DEFAULT_POSTER_TIMEOUT = 60


class FfmpegError(Exception):
    """ffmpeg a échoué, est absent, ou a dépassé le délai."""


def build_transcode_command(
    ffmpeg_bin: str, input_path: str, output_path: str
) -> list[str]:
    """Commande de transcodage MP4 H.264/AAC (profil standard, faststart)."""
    return [
        ffmpeg_bin,
        "-y",
        "-i", input_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-vf", "scale='min(1920,iw)':-2",
        "-movflags", "+faststart",
        "-map_metadata", "-1",
        output_path,
    ]


def build_poster_command(
    ffmpeg_bin: str, input_path: str, output_path: str, *, at_seconds: int = 1
) -> list[str]:
    """Commande d'extraction d'une frame en poster JPG (seek rapide)."""
    return [
        ffmpeg_bin,
        "-y",
        "-ss", str(at_seconds),  # avant -i : seek rapide
        "-i", input_path,
        "-frames:v", "1",
        "-q:v", "3",
        output_path,
    ]


def _default_ffmpeg_runner(cmd: list[str], timeout: int) -> tuple[int, str]:
    import subprocess

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise FfmpegError(f"ffmpeg introuvable : {cmd[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise FfmpegError(f"ffmpeg a dépassé le délai ({timeout}s)") from exc
    return result.returncode, result.stderr


def _run(cmd: list[str], timeout: int, runner: FfmpegRunner | None) -> None:
    code, stderr = (runner or _default_ffmpeg_runner)(cmd, timeout)
    if code != 0:
        raise FfmpegError(f"ffmpeg a échoué (code {code}) : {stderr.strip()}")


def transcode_to_mp4(
    input_path: str,
    output_path: str,
    *,
    ffmpeg_bin: str = "ffmpeg",
    runner: FfmpegRunner | None = None,
    timeout: int = DEFAULT_TRANSCODE_TIMEOUT,
) -> None:
    """Transcode ``input_path`` en MP4 standard à ``output_path``."""
    _run(build_transcode_command(ffmpeg_bin, input_path, output_path), timeout, runner)


def generate_poster(
    input_path: str,
    output_path: str,
    *,
    ffmpeg_bin: str = "ffmpeg",
    at_seconds: int = 1,
    runner: FfmpegRunner | None = None,
    timeout: int = DEFAULT_POSTER_TIMEOUT,
) -> None:
    """Génère un poster JPG depuis une frame de ``input_path``."""
    _run(
        build_poster_command(ffmpeg_bin, input_path, output_path, at_seconds=at_seconds),
        timeout,
        runner,
    )
