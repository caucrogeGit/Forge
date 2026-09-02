# pyright: strict
"""Plafonds cumulés de la vidéothèque (`VIDEO-QUOTA-001`).

Le paquet bornait déjà **un** fichier, par sa taille à l'entrée
(`FORGE_VIDEO_MAX_UPLOAD_MB`) et par sa durée au sondage
(`FORGE_VIDEO_MAX_DURATION_SECONDS`). Ces deux contrôles existaient avant ce
ticket et fonctionnaient.

Rien ne bornait leur **somme**. Cinq cents vidéos d'une heure et de neuf cent
quatre vingt dix neuf mégaoctets passent chacune le contrôle, et remplissent le
disque de cinq cents gigaoctets.

| Variable | Ce qu'elle borne |
|---|---|
| `FORGE_VIDEO_MAX_UPLOAD_MB` | un fichier, déjà présente |
| `FORGE_VIDEO_MAX_DURATION_SECONDS` | un fichier, déjà présente |
| `FORGE_VIDEO_MAX_TOTAL_MB` | la somme des tailles |
| `FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS` | la somme des durées |

Sans les deux dernières, rien n'est cumulé : le paquet ne borne pas ce que
l'exploitant n'a pas demandé.

## Le décalage de la durée, dit plutôt que caché

La taille est connue avant d'écrire, la durée seulement après le sondage.

Le plafond de durée est donc vérifié **au traitement**, quand la vidéo est déjà
stockée. Un dépassement fait échouer le traitement et laisse le fichier source,
que l'application supprime si elle le souhaite. Sonder avant d'écrire
demanderait un fichier temporaire et un appel à `ffprobe` de plus par envoi,
pour déplacer le problème sans le résoudre.
"""
from __future__ import annotations

from typing import Any, Protocol

from forge_mvc_video.config import VideoConfig, load_video_config

__all__ = [
    "VideoQuotaError",
    "VideoTotals",
    "library_totals",
    "check_size_quota",
    "check_duration_quota",
]


class VideoQuotaError(ValueError):
    """Un plafond cumulé de la vidéothèque serait dépassé."""


class _TotalsSource(Protocol):
    def totals(self) -> "dict[str, int]": ...


class VideoTotals:
    """État de la vidéothèque face à ses plafonds, de quoi afficher une jauge."""

    def __init__(self, totals: "dict[str, int]", config: VideoConfig) -> None:
        self.videos = int(totals.get("videos", 0))
        self.total_bytes = int(totals.get("total_bytes", 0))
        self.total_duration = int(totals.get("total_duration", 0))
        self.max_bytes = (
            None if config.max_total_mb is None else config.max_total_mb * 1024 * 1024
        )
        self.max_duration = config.max_total_duration_seconds

    @property
    def remaining_bytes(self) -> "int | None":
        """Jamais négatif : un plafond abaissé après coup laisse au dessus."""
        if self.max_bytes is None:
            return None
        return max(0, self.max_bytes - self.total_bytes)

    @property
    def remaining_duration(self) -> "int | None":
        if self.max_duration is None:
            return None
        return max(0, self.max_duration - self.total_duration)

    def as_dict(self) -> "dict[str, Any]":
        return {
            "videos": self.videos,
            "total_bytes": self.total_bytes,
            "total_duration": self.total_duration,
            "max_bytes": self.max_bytes,
            "max_duration": self.max_duration,
            "remaining_bytes": self.remaining_bytes,
            "remaining_duration": self.remaining_duration,
        }


def library_totals(
    *, repository: "_TotalsSource | None" = None, config: "VideoConfig | None" = None
) -> VideoTotals:
    """État courant de la vidéothèque, sans rien refuser."""
    from forge_mvc_video.storage.repository import VideoRepository

    cfg = config or load_video_config()
    repo = repository if repository is not None else VideoRepository()
    return VideoTotals(repo.totals(), cfg)


def check_size_quota(
    incoming_bytes: int,
    *,
    repository: "_TotalsSource | None" = None,
    config: "VideoConfig | None" = None,
) -> None:
    """Refuse l'envoi qui ferait dépasser le plafond cumulé de taille.

    Sans plafond déclaré, ne touche pas la base : rien à comparer, donc rien à
    lire, et un déploiement sans quota ne paye pas une requête par envoi.

    Raises:
        VideoQuotaError: la somme dépasserait `FORGE_VIDEO_MAX_TOTAL_MB`.
    """
    cfg = config or load_video_config()
    if cfg.max_total_mb is None:
        return

    etat = library_totals(repository=repository, config=cfg)
    plafond = etat.max_bytes
    if plafond is None:
        return
    if etat.total_bytes + incoming_bytes > plafond:
        raise VideoQuotaError(
            "plafond de stockage vidéo dépassé : "
            f"{etat.total_bytes} octets déjà utilisés sur {plafond}, "
            f"et cet envoi en ajoute {incoming_bytes} "
            f"(FORGE_VIDEO_MAX_TOTAL_MB={cfg.max_total_mb})"
        )


def check_duration_quota(
    incoming_seconds: int,
    *,
    repository: "_TotalsSource | None" = None,
    config: "VideoConfig | None" = None,
) -> None:
    """Refuse la vidéo qui ferait dépasser le plafond cumulé de durée.

    Appelé **au traitement**, la durée n'étant connue qu'après le sondage. Le
    fichier source est alors déjà écrit, ce que la documentation dit plutôt que
    de le laisser découvrir.

    Raises:
        VideoQuotaError: la somme dépasserait
            `FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS`.
    """
    cfg = config or load_video_config()
    if cfg.max_total_duration_seconds is None:
        return

    etat = library_totals(repository=repository, config=cfg)
    plafond = etat.max_duration
    if plafond is None:
        return
    if etat.total_duration + incoming_seconds > plafond:
        raise VideoQuotaError(
            "plafond de durée vidéo dépassé : "
            f"{etat.total_duration}s déjà enregistrées sur {plafond}s, "
            f"et cette vidéo en ajoute {incoming_seconds}s "
            f"(FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS={plafond})"
        )
