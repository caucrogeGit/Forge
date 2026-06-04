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

À ce stade (``IMAGES-PKG-SCAFFOLD-001``), le paquet est un **squelette** : la
dépendance Pillow est déclarée mais aucune logique n'a encore été déplacée.
Le core conserve l'upload brut générique (``core/uploads``) jusqu'aux tickets
de déplacement. Voir ``docs/adr/018-image-module-extraction.md``.
"""

__version__ = "1.0.0b13"

__all__: list[str] = []
