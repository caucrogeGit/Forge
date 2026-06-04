"""Shim transitoire — galerie média déplacée vers forge-mvc-images.

IMAGES-MOVE-APPLICATIVE-001 (ADR-018) : la galerie/couverture des médias est
désormais détenue par ``forge_mvc_images``. Ce module ne fait que réexporter
l'implémentation pour ne pas casser les imports
``from forge_mvc_media.media_gallery import ...`` pendant la migration. Il sera
**supprimé** avec le paquet ``forge-mvc-media`` au ticket ``REMOVE-MEDIA-PKG-001``.
"""

from forge_mvc_images.media_gallery import (
    get_cover_media,
    get_media_gallery,
    media_url,
)

__all__ = [
    "get_cover_media",
    "get_media_gallery",
    "media_url",
]
