"""Shim transitoire — repository média déplacé vers forge-mvc-images.

IMAGES-MOVE-APPLICATIVE-001 (ADR-018) : le repository SQL des médias est
désormais détenu par ``forge_mvc_images`` (unique propriétaire de tout l'image).
Ce module ne fait que réexporter l'implémentation pour ne pas casser les imports
``from forge_mvc_media.media_repository import ...`` pendant la migration. Il
sera **supprimé** avec le paquet ``forge-mvc-media`` au ticket ``REMOVE-MEDIA-PKG-001``.
"""

from forge_mvc_images.media_repository import (
    attach_media_to_entity,
    create_media_record,
    delete_media,
    delete_media_record,
    get_media_record,
    list_media_for_entity,
    update_media_alt_text,
    update_media_position,
)

__all__ = [
    "attach_media_to_entity",
    "create_media_record",
    "delete_media",
    "delete_media_record",
    "get_media_record",
    "list_media_for_entity",
    "update_media_alt_text",
    "update_media_position",
]
