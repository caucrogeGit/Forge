"""Shim de compatibilité — MEDIA-REPOSITORY-MOVE-001.

core.uploads.media_repository a été déplacé vers forge_mvc_media.media_repository.
Ce module re-exporte les symboles depuis le nouveau chemin canonical.

Importer directement depuis forge_mvc_media.media_repository.
Ce shim sera supprimé dans une version future.
"""
import warnings

warnings.warn(
    "core.uploads.media_repository est déplacé vers forge_mvc_media.media_repository. "
    "Importer depuis forge_mvc_media.media_repository directement. "
    "Ce shim de compatibilité sera supprimé dans une version future.",
    DeprecationWarning,
    stacklevel=2,
)

from forge_mvc_media.media_repository import (  # noqa: E402, F401
    attach_media_to_entity,
    create_media_record,
    delete_media,
    delete_media_record,
    get_media_record,
    list_media_for_entity,
    update_media_alt_text,
    update_media_position,
)
