"""Forge MVC Media — module opt-in pour la gestion applicative des médias.

Contient le repository SQL et les helpers de galerie extraits depuis core/uploads/.
Les briques génériques (upload sécurisé, validation, storage, images, rate limit)
restent dans core/uploads/ et ne nécessitent pas ce module opt-in.
"""

__version__ = "1.0.0b6"

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
    "__version__",
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
