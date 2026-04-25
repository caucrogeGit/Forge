from __future__ import annotations

from pathlib import Path

from core.uploads.exceptions import (
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)


def normalize_extensions(extensions) -> set[str]:
    """Retourne les extensions autorisees sous forme normalisee, sans point."""
    return {
        str(ext).strip().lower().lstrip(".")
        for ext in (extensions or [])
        if str(ext).strip()
    }


def filename_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def validate_filename(filename: str | None) -> str:
    filename = (filename or "").strip()
    if not filename:
        raise UploadStorageError("Nom de fichier vide.")
    return filename


def validate_extension(filename: str, allowed_extensions) -> str:
    allowed = normalize_extensions(allowed_extensions)
    extension = filename_extension(filename)
    if not extension or extension not in allowed:
        raise UploadInvalidExtensionError(
            f"Extension non autorisee : {extension or '<aucune>'}."
        )
    return extension


def validate_size(size: int, max_size: int) -> None:
    if size < 0:
        raise UploadStorageError("Taille de fichier invalide.")
    if size > int(max_size):
        raise UploadTooLargeError(
            f"Fichier trop volumineux : {size} octets, maximum {int(max_size)}."
        )


def validate_mime_type(mime_type: str | None, allowed_mime_types) -> None:
    allowed = {str(m).strip().lower() for m in (allowed_mime_types or []) if str(m).strip()}
    if not allowed:
        return
    if not mime_type:
        raise UploadInvalidMimeTypeError("Type MIME absent — fichier refusé.")
    normalized = mime_type.split(";", 1)[0].strip().lower()
    if normalized not in allowed:
        raise UploadInvalidMimeTypeError(f"Type MIME non autorise : {normalized}.")


def validate_upload_metadata(
    *,
    filename: str | None,
    size: int,
    mime_type: str | None,
    allowed_extensions,
    allowed_mime_types,
    max_size: int,
) -> str:
    """Valide les metadonnees d'un fichier et retourne son extension normalisee."""
    safe_name = validate_filename(filename)
    extension = validate_extension(safe_name, allowed_extensions)
    validate_size(size, max_size)
    validate_mime_type(mime_type, allowed_mime_types)
    return extension
