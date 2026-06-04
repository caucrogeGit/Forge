"""Shim transitoire — storage d'upload déplacé vers forge-mvc-files.

FILES-MOVE-PIPELINE-001 (ADR-019) : l'écriture disque sécurisée (anti-traversal)
vit désormais dans ``forge_mvc_files.storage``. Ce module réexporte pour ne pas
casser les imports ``from core.uploads.storage import ...`` pendant la
migration ; il sera supprimé avec ``core/uploads/`` au ticket
``CORE-DROP-UPLOADS-001``. Nouveau code : importer depuis ``forge_mvc_files``.
"""

from forge_mvc_files.storage import (
    category_dir,
    delete_file,
    ensure_upload_dirs,
    generate_unique_filename,
    get_upload_path,
    is_safe_media_path,
    media_path_to_storage_path,
    normalize_media_path,
    safe_category,
    save_bytes,
    secure_filename,
)

__all__ = [
    "category_dir",
    "delete_file",
    "ensure_upload_dirs",
    "generate_unique_filename",
    "get_upload_path",
    "is_safe_media_path",
    "media_path_to_storage_path",
    "normalize_media_path",
    "safe_category",
    "save_bytes",
    "secure_filename",
]
