# pyright: strict
"""Forge MVC Files — module opt-in propriétaire de l'upload générique.

Ce paquet détient le **pipeline d'upload générique** extrait du core (ADR-019) :
écriture disque sécurisée (anti-traversal), service de fichiers (`serve_media_file`,
streaming HTTP Range), suppression, rate-limit d'upload, et l'API
``save_upload`` / ``SavedUpload``.

Depuis ``FILES-MOVE-PIPELINE-001``, ``manager`` + ``storage`` + ``rate_limit``
vivent ici. La **validation pure** (validators + exceptions ``UploadError``)
reste dans le core (``core.forms.upload_validation`` / ``upload_exceptions``),
réutilisée ici : le core ne peut pas dépendre d'un opt-in (ADR-004). Le core
expose des **shims transitoires** (``core/uploads``) supprimés au ticket
``CORE-DROP-UPLOADS-001``. Voir ``docs/adr/019-upload-extraction.md``.

Depuis l'ADR-094, le paquet tient aussi un **registre** de ce qu'il a écrit
(``forge_files``), socle des quotas et de la purge des orphelins. Le registre
est **explicite** : écrire un fichier n'inscrit rien de soi même, et le paquet
reste utilisable sans base pour qui ne veut que des primitives de stockage.
"""

from __future__ import annotations

__version__ = "1.0.0rc7"

# Validation/exceptions : réexport depuis le core (où elles restent).
from core.forms.upload_exceptions import (
    UploadError,
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)
from forge_mvc_files.manager import (
    SavedUpload,
    delete_media_file,
    delete_upload,
    get_upload_path,
    save_upload,
    serve_media_file,
    upload_root,
)
from forge_mvc_files.registry import (
    FileRegistryError,
    forget_file,
    get_file_record,
    list_all_paths,
    list_paths_for_owner,
    owner_file_count,
    owner_usage_bytes,
    record_file,
)
from forge_mvc_files.rate_limit import (
    is_upload_rate_limited,
    record_upload_attempt,
)
from forge_mvc_files.storage import (
    delete_file,
    is_safe_media_path,
    media_path_to_storage_path,
    normalize_media_path,
    save_bytes,
    secure_filename,
)

__all__ = [
    # Exceptions (réexportées du core)
    "UploadError",
    "UploadInvalidExtensionError",
    "UploadInvalidMimeTypeError",
    "UploadStorageError",
    "UploadTooLargeError",
    # Upload / service de fichiers (manager)
    "SavedUpload",
    "save_upload",
    "serve_media_file",
    "delete_upload",
    "delete_media_file",
    "get_upload_path",
    "upload_root",
    # Storage (anti-traversal)
    "save_bytes",
    "delete_file",
    "normalize_media_path",
    "media_path_to_storage_path",
    "is_safe_media_path",
    "secure_filename",
    # Rate-limit d'upload
    "is_upload_rate_limited",
    "record_upload_attempt",
    # Registre des fichiers écrits (ADR-094)
    "record_file",
    "forget_file",
    "get_file_record",
    "owner_usage_bytes",
    "owner_file_count",
    "list_paths_for_owner",
    "list_all_paths",
    "FileRegistryError",
]
