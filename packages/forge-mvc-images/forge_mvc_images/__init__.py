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

Depuis ``IMAGES-MOVE-PROCESSING-001``, le **traitement d'image** est déplacé ici
(``processing``) : Pillow a quitté le core. La couche applicative (repository,
galerie) sera rapatriée par ``IMAGES-MOVE-APPLICATIVE-001``. Voir
``docs/adr/018-image-module-extraction.md``.
"""

__version__ = "1.0.0b13"

from forge_mvc_images.processing import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIME_TYPES,
    IMAGE_VARIANT_SIZES,
    MediaRecord,
    generate_image_variants,
    image_variant_paths,
    image_variant_relative_paths,
    save_image,
    verify_image_content,
)

__all__ = [
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_IMAGE_MIME_TYPES",
    "IMAGE_VARIANT_SIZES",
    "MediaRecord",
    "generate_image_variants",
    "image_variant_paths",
    "image_variant_relative_paths",
    "save_image",
    "verify_image_content",
]
