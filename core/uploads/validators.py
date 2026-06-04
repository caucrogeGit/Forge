"""Shim transitoire — validators d'upload relocalisés dans core/forms.

FILES-VALIDATORS-KEEP-001 (ADR-019) : les validators **purs**
(``validate_extension``/``mime_type``/``size``, ``validate_upload_metadata``…)
restent dans le core mais ont été déplacés vers ``core.forms.upload_validation``
(hors de ``core/uploads/``, qui partira vers ``forge-mvc-files``). Ce module
réexporte pour ne pas casser les imports ``from core.uploads.validators import
...`` pendant la migration ; il sera supprimé avec ``core/uploads/`` au ticket
``CORE-DROP-UPLOADS-001``. Nouveau code : importer depuis
``core.forms.upload_validation``.
"""

from core.forms.upload_validation import (
    filename_extension,
    normalize_extensions,
    validate_extension,
    validate_filename,
    validate_mime_type,
    validate_size,
    validate_upload_metadata,
)

__all__ = [
    "filename_extension",
    "normalize_extensions",
    "validate_extension",
    "validate_filename",
    "validate_mime_type",
    "validate_size",
    "validate_upload_metadata",
]
