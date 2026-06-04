"""Shim transitoire — exceptions d'upload relocalisées dans core/forms.

FILES-VALIDATORS-KEEP-001 (ADR-019) : la hiérarchie ``UploadError`` reste dans
le core mais a été déplacée vers ``core.forms.upload_exceptions`` (hors de
``core/uploads/``, qui partira vers ``forge-mvc-files``). Ce module réexporte
pour ne pas casser les imports ``from core.uploads.exceptions import ...``
pendant la migration ; il sera supprimé avec ``core/uploads/`` au ticket
``CORE-DROP-UPLOADS-001``. Nouveau code : importer depuis
``core.forms.upload_exceptions``.
"""

from core.forms.upload_exceptions import (
    UploadError,
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)

__all__ = [
    "UploadError",
    "UploadInvalidExtensionError",
    "UploadInvalidMimeTypeError",
    "UploadStorageError",
    "UploadTooLargeError",
]
