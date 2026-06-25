# pyright: strict
"""Validation **pure** des métadonnées de fichier — reste dans le core.

FILES-VALIDATORS-KEEP-001 (ADR-019) : déplacée hors de ``core/uploads/`` (qui
part vers l'opt-in ``forge-mvc-files``). Ces contrôles restent dans le core car
``core/forms`` (``FileField``) en dépend, et le core ne peut pas dépendre d'un
opt-in (ADR-004). Ce sont des fonctions **pures** (extension/MIME/taille), sans
aucune écriture disque.

Le pipeline d'I/O (``save_upload``, storage), lui, part dans ``forge-mvc-files``
qui **réutilise** ces validators (il dépend du core).
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from core.forms.upload_exceptions import (
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)


def normalize_extensions(extensions: Iterable[Any] | None) -> set[str]:
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


def validate_extension(filename: str, allowed_extensions: Iterable[Any] | None) -> str:
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


def validate_mime_type(mime_type: str | None, allowed_mime_types: Iterable[Any] | None) -> None:
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
    allowed_extensions: Iterable[Any] | None,
    allowed_mime_types: Iterable[Any] | None,
    max_size: int,
) -> str:
    """Valide les metadonnees d'un fichier et retourne son extension normalisee."""
    safe_name = validate_filename(filename)
    extension = validate_extension(safe_name, allowed_extensions)
    validate_size(size, max_size)
    validate_mime_type(mime_type, allowed_mime_types)
    return extension


# SEC-UPLOAD-MIME-MAGIC-001 : le `content_type` et l'extension sont fournis par
# le client et ne sont pas dignes de confiance. Pour les types à signature
# connue (image/PDF), on vérifie les magic bytes du contenu réel.
_EXTENSION_TO_TYPE = {
    "jpg": "jpeg", "jpeg": "jpeg", "png": "png",
    "gif": "gif", "webp": "webp", "pdf": "pdf",
}


def sniff_content_type(content: bytes) -> str | None:
    """Retourne le type logique réel d'après les magic bytes, ou None si inconnu."""
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if content.startswith(b"%PDF-"):
        return "pdf"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def validate_magic_bytes(content: bytes, extension: str) -> None:
    """Vérifie que le contenu correspond au type déclaré par l'extension.

    Refuse un fichier dont les magic bytes ne correspondent pas au type attendu
    (ex. contenu HTML nommé ``.png``). Ne contraint que les extensions à
    signature connue (image/PDF) ; les autres ne sont pas vérifiées ici.
    Contrôle léger (premiers octets), distinct d'un décodage d'image complet
    (qui reste côté ``forge-mvc-images``).
    """
    expected = _EXTENSION_TO_TYPE.get(extension.strip().lower())
    if expected is None:
        return
    actual = sniff_content_type(content)
    if actual != expected:
        raise UploadInvalidMimeTypeError(
            f"Contenu incohérent avec l'extension .{extension} : "
            f"signature {actual or 'inconnue'} (attendu : {expected})."
        )
