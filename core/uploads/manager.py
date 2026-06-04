"""Shim transitoire — manager d'upload déplacé vers forge-mvc-files.

FILES-MOVE-PIPELINE-001 (ADR-019) : ``save_upload``, ``SavedUpload``,
``serve_media_file``, la suppression et les helpers d'upload vivent désormais
dans ``forge_mvc_files.manager``. Ce module réexporte pour ne pas casser les
imports ``from core.uploads.manager import ...`` pendant la migration ; il sera
supprimé avec ``core/uploads/`` au ticket ``CORE-DROP-UPLOADS-001``. Nouveau
code : importer depuis ``forge_mvc_files``.
"""

from forge_mvc_files.manager import (
    SavedUpload,
    _read_upload,
    _require_image_processing,
    delete_media_file,
    delete_upload,
    get_upload_path,
    save_upload,
    serve_media_file,
    upload_root,
)

__all__ = [
    "SavedUpload",
    "_read_upload",
    "_require_image_processing",
    "delete_media_file",
    "delete_upload",
    "get_upload_path",
    "save_upload",
    "serve_media_file",
    "upload_root",
]
