# pyright: strict
"""Forge Video — module opt-in (squelette VIDEO-ROADMAP-OPEN-001).

API publique stable :

- ``forge_mvc_video.http.register_video_routes`` — branchement explicite des
  routes vidéo sur un ``Router`` Forge (couche ``optins/`` côté projet) ;
- ``forge_mvc_video.config.load_video_config`` — contrat de configuration
  ``FORGE_VIDEO_*`` ;
- commandes ``forge video:*`` (``video:doctor`` en v1 squelette).

Le module reste **opt-in** : Forge Core ne dépend de rien ici. Le travail
lourd (transcodage) suit le modèle worker-CLI (``forge video:process``,
ajouté par un ticket ultérieur), jamais pendant une requête HTTP.
"""
from __future__ import annotations

from forge_mvc_video.http import register_video_routes

__version__ = "1.0.0rc4"

__all__ = ["register_video_routes"]
