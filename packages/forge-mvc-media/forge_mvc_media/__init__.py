"""Forge MVC Media — shim transitoire vers forge-mvc-images.

IMAGES-MOVE-APPLICATIVE-001 (ADR-018) : le repository SQL et les helpers de
galerie ont été rapatriés dans ``forge_mvc_images`` (unique propriétaire de tout
l'image). Ce paquet ne fait plus que réexporter cette API pour préserver les
imports ``from forge_mvc_media import ...`` pendant la migration ; il sera
**supprimé** au ticket ``REMOVE-MEDIA-PKG-001``. Nouveau code : importer depuis
``forge_mvc_images``.
"""

__version__ = "1.0.0b13"

from forge_mvc_media.media_repository import (
    attach_media_to_entity,
    create_media_record,
    delete_media,
    delete_media_record,
    get_media_record,
    list_media_for_entity,
    update_media_alt_text,
    update_media_position,
)
from forge_mvc_media.media_gallery import (
    get_cover_media,
    get_media_gallery,
    media_url,
)

__all__ = [
    "attach_media_to_entity",
    "create_media_record",
    "delete_media",
    "delete_media_record",
    "get_cover_media",
    "get_media_gallery",
    "get_media_record",
    "list_media_for_entity",
    "media_url",
    "update_media_alt_text",
    "update_media_position",
]
