"""Branchement HTTP du module vidéo — VIDEO-ROADMAP-OPEN-001 (squelette).

``register_video_routes(router)`` est le point d'entrée **explicite** : une
application opt-in l'appelle depuis sa couche ``optins/video/`` pour brancher
les routes vidéo (upload, lecture en streaming). Aucune modification
automatique de ``mvc/routes.py`` (charte §9).

État squelette : la fonction est définie et stable, mais n'enregistre **encore
aucune route**. Les routes arrivent dans les tickets ultérieurs :

- ``VIDEO-PLAYBACK-RANGE-001`` : lecture sous auth via ``Response.file`` (Range) ;
- ``VIDEO-UPLOAD-STORE-001``   : upload contrôlé (réutilise ``core/uploads``).

La signature et le nom sont figés dès maintenant (API publique = contrat).
"""
from __future__ import annotations

from typing import Any

__all__ = ["register_video_routes"]


def register_video_routes(router: Any) -> Any:
    """Branche les routes vidéo sur un ``Router`` Forge.

    Squelette : ne branche encore aucune route (voir les tickets de la phase
    vidéo). Retourne le ``router`` pour permettre le chaînage. Appelé
    explicitement par le projet, jamais par Forge Core.
    """
    return router
