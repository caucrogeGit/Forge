"""Forge MVC Images — module opt-in propriétaire de tout l'image.

Ce paquet **remplace** ``forge-mvc-media`` (ADR-018, convention pré-1.0 :
suppression sèche, pas d'alias). Il deviendra l'unique propriétaire de :

- le **traitement d'image** (déplacé du core par ``IMAGES-MOVE-PROCESSING-001``) :
  ``save_image``, génération de variantes/miniatures, ``verify_image_content``,
  garde anti-bombe de décompression, constantes ``ALLOWED_IMAGE_*`` /
  ``IMAGE_VARIANT_SIZES``, ``MediaRecord``. **Pillow** est une dépendance de
  ce module, retirée du core ;
- la **couche médias applicative** (déplacée de ``forge-mvc-media`` par
  ``IMAGES-MOVE-APPLICATIVE-001``) : repository SQL, galerie, couverture,
  ``alt_text``.

Depuis ``IMAGES-MOVE-PROCESSING-001`` le **traitement d'image** vit ici
(``processing``) ; depuis ``IMAGES-MOVE-APPLICATIVE-001`` la **couche médias
applicative** (``media_repository``, ``media_gallery``) y est rapatriée :
``forge_mvc_images`` est désormais l'unique propriétaire de tout l'image.
``forge-mvc-media`` a été supprimé (ticket ``REMOVE-MEDIA-PKG-001``).
Voir ``docs/adr/018-image-module-extraction.md``.
"""

__version__ = "1.0.0b16"

from forge_mvc_images.processing import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIME_TYPES,
    IMAGE_VARIANT_SIZES,
    MediaRecord,
    generate_image_variants,
    image_variant_paths,
    image_variant_relative_paths,
    save_image,
    save_image_upload,
    verify_image_content,
)
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
from forge_mvc_images.media_gallery import (
    get_cover_media,
    get_media_gallery,
    media_url,
)

__all__ = [
    # Traitement d'image (IMAGES-MOVE-PROCESSING-001)
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_IMAGE_MIME_TYPES",
    "IMAGE_VARIANT_SIZES",
    "MediaRecord",
    "generate_image_variants",
    "image_variant_paths",
    "image_variant_relative_paths",
    "save_image",
    "save_image_upload",
    "verify_image_content",
    # Couche médias applicative (IMAGES-MOVE-APPLICATIVE-001)
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
