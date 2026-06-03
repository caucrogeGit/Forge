"""Branchement de la route de lecture de l'opt-in Forge Video.

Délègue à l'**API publique** du paquet `forge-mvc-video` : le code métier
vit dans le paquet, ce fichier ne fait que le brancher localement. Appelé
par ``optins/registry.py``.
"""

from __future__ import annotations

from forge_mvc_video import register_video_routes


def register(router) -> None:
    """Expose la route de lecture vidéo officielle (streaming HTTP Range) :

    - ``GET /videos/{uuid}``

    Si ``FORGE_VIDEO_API_TOKEN`` est défini, la route exige un en-tête
    ``Authorization: Bearer <token>``.
    """
    register_video_routes(router)
