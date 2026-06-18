# pyright: strict
"""Traitement d'une vidéo (worker) — VIDEO-PROCESS-MP4-001.

``process_video`` assemble les briques : il fait avancer une vidéo
``uploaded`` → ``processing`` → (probe + poster + transcode MP4) →
``ready`` (avec ``mp4_path``/``poster_path``) ou ``failed`` (avec
``error_message`` lisible, et nettoyage des sorties partielles).

Modèle **worker CLI → base** : appelé hors requête HTTP (par
``forge video:process``, ticket suivant). Toutes les briques externes
(probe, poster, transcode) sont **injectables** → testable sans ffmpeg réel.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from forge_mvc_video.config import VideoConfig, load_video_config
from forge_mvc_video.probe import VideoMetadata, VideoProbeError, probe_video
from forge_mvc_video.storage.files import mp4_relpath, poster_relpath
from forge_mvc_video.storage.repository import VideoRepository
from forge_mvc_video.transcode import FfmpegError, generate_poster, transcode_to_mp4

__all__ = ["VideoProcessError", "process_video"]

# Briques injectables : probe (chemin → métadonnées) et poster/transcode
# (source, destination → effet de bord ffmpeg).
_ProbeFn = Callable[[str], VideoMetadata]
_OutputFn = Callable[[str, str], None]


class VideoProcessError(Exception):
    """Vidéo introuvable ou sans source — erreur d'orchestration (pas un échec ffmpeg)."""


def process_video(
    video_id: int,
    *,
    config: VideoConfig | None = None,
    repository: VideoRepository | None = None,
    probe_fn: _ProbeFn | None = None,
    poster_fn: _OutputFn | None = None,
    transcode_fn: _OutputFn | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Traite la vidéo ``video_id`` ; retourne ``{id, status, ...}``.

    ``status`` vaut ``ready`` ou ``failed``. Lève ``VideoProcessError`` si la
    vidéo est introuvable ou n'a pas de source (erreur d'usage, pas de transcodage).
    """
    cfg = config or load_video_config()
    repo = repository or VideoRepository()
    moment = now or datetime.now(UTC).replace(tzinfo=None)

    row = repo.get_by_id(video_id)
    if row is None:
        raise VideoProcessError(f"vidéo introuvable : id={video_id}")
    if not row.get("original_path"):
        raise VideoProcessError(f"vidéo sans source : id={video_id}")

    root = Path(cfg.storage_root)
    original_abs = str(root / row["original_path"])

    probe: _ProbeFn = probe_fn or (lambda p: probe_video(p, config=cfg))
    poster: _OutputFn = poster_fn or (
        lambda src, dst: generate_poster(src, dst, ffmpeg_bin=cfg.ffmpeg_bin)
    )
    transcode: _OutputFn = transcode_fn or (
        lambda src, dst: transcode_to_mp4(src, dst, ffmpeg_bin=cfg.ffmpeg_bin)
    )

    mp4_rel = mp4_relpath(row["uuid"], now=moment)
    poster_rel = poster_relpath(row["uuid"], now=moment)
    mp4_abs = root / mp4_rel
    poster_abs = root / poster_rel

    repo.update_status(video_id, "processing", now=moment)
    try:
        meta = probe(original_abs)
        repo.update_metadata(
            video_id,
            duration_seconds=meta.duration_seconds,
            width=meta.width,
            height=meta.height,
            now=moment,
        )

        mp4_abs.parent.mkdir(parents=True, exist_ok=True)
        poster_abs.parent.mkdir(parents=True, exist_ok=True)
        poster(original_abs, str(poster_abs))
        transcode(original_abs, str(mp4_abs))

        repo.mark_ready(
            video_id, mp4_path=mp4_rel, poster_path=poster_rel, now=moment
        )
        return {
            "id": video_id,
            "status": "ready",
            "mp4_path": mp4_rel,
            "poster_path": poster_rel,
        }
    except (VideoProbeError, FfmpegError, OSError) as exc:
        for partial in (mp4_abs, poster_abs):
            try:
                if partial.exists():
                    partial.unlink()
            except OSError:  # pragma: no cover - nettoyage best-effort
                pass
        repo.update_status(video_id, "failed", error_message=str(exc), now=moment)
        return {"id": video_id, "status": "failed", "error": str(exc)}
