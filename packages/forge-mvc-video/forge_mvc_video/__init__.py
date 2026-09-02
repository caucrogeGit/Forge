# pyright: strict
"""Forge Video — module opt-in (squelette VIDEO-ROADMAP-OPEN-001).

API publique stable :

- ``forge_mvc_video.http.register_video_routes`` — branchement explicite des
  routes vidéo sur un ``Router`` Forge (couche ``optins/`` côté projet) ;
- ``forge_mvc_video.config.load_video_config`` — contrat de configuration
  ``FORGE_VIDEO_*`` ;
- commandes ``forge video:*`` (``video:doctor`` en v1 squelette) ;
- ``describe_video_status`` — état de traitement restituable dans une
  interface, sans jamais rendre la sortie d'erreur de ffmpeg ;
- ``check_size_quota`` / ``check_duration_quota`` — plafonds cumulés ;
- ``store_subtitle`` / ``validate_vtt`` — pistes WebVTT.

Le module reste **opt-in** : Forge Core ne dépend de rien ici. Le travail
lourd (transcodage) suit le modèle worker-CLI (``forge video:process``,
ajouté par un ticket ultérieur), jamais pendant une requête HTTP.
"""
from __future__ import annotations

from forge_mvc_video.http import register_video_routes
from forge_mvc_video.quota import (
    VideoQuotaError,
    VideoTotals,
    check_duration_quota,
    check_size_quota,
    library_totals,
)
from forge_mvc_video.status import (
    FINAL_STATUSES,
    PENDING_STATUSES,
    STATUS_LABELS,
    VideoStatusView,
    describe_video_status,
)
from forge_mvc_video.subtitles import (
    VTT_MIME_TYPE,
    SubtitleError,
    SubtitleTrack,
    normalize_lang,
    store_subtitle,
    validate_vtt,
)

__version__ = "1.0.0rc7"

__all__ = [
    "register_video_routes",
    # État de traitement restituable (VIDEO-STATUS-UI-001)
    "VideoStatusView",
    "describe_video_status",
    "STATUS_LABELS",
    "PENDING_STATUSES",
    "FINAL_STATUSES",
    # Plafonds cumulés de la vidéothèque (VIDEO-QUOTA-001)
    "library_totals",
    "check_size_quota",
    "check_duration_quota",
    "VideoTotals",
    "VideoQuotaError",
    # Pistes de sous-titres (VIDEO-SUBTITLES-001)
    "SubtitleTrack",
    "SubtitleError",
    "normalize_lang",
    "validate_vtt",
    "store_subtitle",
    "VTT_MIME_TYPE",
]
