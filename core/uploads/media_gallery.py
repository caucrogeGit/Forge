"""Shim de compatibilité — MEDIA-REPOSITORY-MOVE-001.

core.uploads.media_gallery a été déplacé vers forge_mvc_media.media_gallery.
Ce module re-exporte les symboles depuis le nouveau chemin canonical.

Importer directement depuis forge_mvc_media.media_gallery.
Ce shim sera supprimé dans une version future.
"""
import warnings

warnings.warn(
    "core.uploads.media_gallery est déplacé vers forge_mvc_media.media_gallery. "
    "Importer depuis forge_mvc_media.media_gallery directement. "
    "Ce shim de compatibilité sera supprimé dans une version future.",
    DeprecationWarning,
    stacklevel=2,
)

from forge_mvc_media.media_gallery import (  # noqa: E402, F401
    get_cover_media,
    get_media_gallery,
    media_url,
)
