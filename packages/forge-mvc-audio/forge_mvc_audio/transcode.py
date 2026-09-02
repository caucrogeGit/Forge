# pyright: strict
"""Runner ffmpeg : transcodage MP3.

Construit et exécute la commande ffmpeg du profil MP3 standard Forge Audio. Le
constructeur de commande est **pur** (testable sans ffmpeg) ; l'exécution est
déléguée à un *runner* injectable.

Sécurité d'invocation :
- arguments en **liste** (jamais ``shell=True``) → aucune injection ;
- chemins passés en arguments (le caller fournit des chemins uuid-based,
  jamais le nom de fichier utilisateur) ;
- ``timeout`` obligatoire (un ffmpeg sans borne peut tourner indéfiniment).

Profil MP3 standard :

    -c:a libmp3lame -b:a 192k -ac 2
    -map_metadata -1   (retire les métadonnées d'origine)
    -vn                (ignore toute piste vidéo/pochette → audio pur)
"""
from __future__ import annotations

from collections.abc import Callable

__all__ = [
    "FfmpegError",
    "DEFAULT_TRANSCODE_TIMEOUT",
    "build_transcode_command",
    "safe_path_arg",
    "default_ffmpeg_runner",
    "FfmpegRunner",
    "transcode_to_mp3",
]

# Un runner prend (cmd, timeout) et retourne (returncode, stderr).
FfmpegRunner = Callable[[list[str], int], tuple[int, str]]

DEFAULT_TRANSCODE_TIMEOUT = 1800  # 30 min — borne haute d'un transcodage audio


class FfmpegError(Exception):
    """ffmpeg a échoué, est absent, ou a dépassé le délai."""


def safe_path_arg(path: str) -> str:
    """Empêche qu'un chemin commençant par ``-`` soit lu comme une option ffmpeg
    (MEDIA-FFMPEG-ARG-HARDENING-001). Neutre pour les chemins uuid/absolus.

    Publique depuis ``AUDIO-TRIM-001`` : la découpe construit sa propre ligne de
    commande et doit appliquer le même durcissement. En dupliquer une seconde
    copie ferait diverger les deux le jour où l'une serait corrigée.
    """
    return f"./{path}" if path.startswith("-") else path


def build_transcode_command(
    ffmpeg_bin: str, input_path: str, output_path: str, *, bitrate_kbps: int = 192
) -> list[str]:
    """Commande de transcodage MP3 (libmp3lame, stéréo, sans métadonnées)."""
    return [
        ffmpeg_bin,
        "-y",
        "-i", safe_path_arg(input_path),
        "-vn",
        "-c:a", "libmp3lame", "-b:a", f"{bitrate_kbps}k", "-ac", "2",
        "-map_metadata", "-1",
        safe_path_arg(output_path),
    ]


def default_ffmpeg_runner(cmd: list[str], timeout: int) -> tuple[int, str]:
    """Exécution par défaut de ffmpeg. Publique pour la même raison."""
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


def transcode_to_mp3(
    input_path: str,
    output_path: str,
    *,
    ffmpeg_bin: str = "ffmpeg",
    bitrate_kbps: int = 192,
    runner: FfmpegRunner | None = None,
    timeout: int = DEFAULT_TRANSCODE_TIMEOUT,
) -> None:
    """Transcode ``input_path`` en MP3 standard à ``output_path``."""
    cmd = build_transcode_command(
        ffmpeg_bin, input_path, output_path, bitrate_kbps=bitrate_kbps
    )
    code, stderr = (runner or default_ffmpeg_runner)(cmd, timeout)
    if code != 0:
        raise FfmpegError(f"ffmpeg a échoué (code {code}) : {stderr.strip()}")
