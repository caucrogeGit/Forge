from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.forge import get as _cfg
from core.uploads import storage
from core.uploads.exceptions import UploadStorageError
from core.uploads.validators import validate_upload_metadata


@dataclass(frozen=True)
class SavedUpload:
    filename: str
    original_name: str
    path: str
    category: str
    size: int
    mime_type: str | None = None


def _read_upload(file) -> tuple[str, str | None, bytes]:
    filename = getattr(file, "filename", None) or getattr(file, "name", None)
    mime_type = (
        getattr(file, "content_type", None)
        or getattr(file, "mimetype", None)
        or getattr(file, "mime_type", None)
    )

    if hasattr(file, "content"):
        data = file.content
    elif hasattr(file, "read"):
        data = file.read()
    elif hasattr(file, "stream") and hasattr(file.stream, "read"):
        data = file.stream.read()
    else:
        data = file

    if isinstance(data, str):
        data = data.encode("utf-8")
    if data is None:
        data = b""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Le fichier uploadé doit fournir des bytes ou une méthode read().")

    return filename, mime_type, bytes(data)


def upload_root() -> Path:
    return Path(str(_cfg("upload_root")))


def save_upload(file, category: str = "documents") -> SavedUpload:
    if file is None:
        raise UploadStorageError("Aucun fichier reçu.")
    filename, mime_type, data = _read_upload(file)
    validate_upload_metadata(
        filename=filename,
        size=len(data),
        mime_type=mime_type,
        allowed_extensions=_cfg("upload_allowed_extensions"),
        allowed_mime_types=_cfg("upload_allowed_mime_types"),
        max_size=int(_cfg("upload_max_size")),
    )
    saved_path = storage.save_bytes(
        data,
        original_name=filename,
        category=category,
        root=upload_root(),
    )
    return SavedUpload(
        filename=saved_path.name,
        original_name=filename,
        path=saved_path.as_posix(),
        category=category,
        size=len(data),
        mime_type=mime_type,
    )


def delete_upload(path) -> bool:
    return storage.delete_file(path, root=upload_root())


def get_upload_path(filename: str, category: str = "documents") -> Path:
    return storage.get_upload_path(filename, category, root=upload_root())
