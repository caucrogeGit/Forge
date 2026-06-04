from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path

from core.forge import get as _cfg
from core.http.response import Response

# FILES-MOVE-PIPELINE-001 (ADR-019) : le pipeline d'upload vit désormais dans
# forge-mvc-files. La validation pure (validators + exceptions) reste dans le
# core (core/forms), réutilisée ici (le core ne peut pas dépendre de l'opt-in).
from core.forms.upload_exceptions import UploadStorageError
from core.forms.upload_validation import validate_upload_metadata
from forge_mvc_files import storage


@dataclass(frozen=True)
class SavedUpload:
    filename: str
    original_name: str
    path: str
    category: str
    size: int
    mime_type: str | None = None
    variants: dict[str, str] = field(default_factory=dict)


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


def _require_image_processing(name: str):
    """Résout un helper de traitement d'image depuis l'opt-in forge-mvc-images.

    IMAGES-MOVE-PROCESSING-001 (ADR-018) : le traitement d'image (Pillow) a été
    extrait du core vers ``forge-mvc-images``. Depuis
    CORE-SAVEUPLOAD-GENERIC-CLEANUP, ``save_upload`` est purement générique ; il
    ne reste qu'un seul appelant de ce delegate dans le core :
    ``delete_media_file(variants=True)``, qui a besoin des chemins de variantes
    (``image_variant_relative_paths``) pour supprimer les fichiers dérivés. Si
    l'opt-in est absent, l'erreur est explicite plutôt qu'un ``ImportError`` brut
    (charte §7 — sécuriser/échouer clairement).
    """
    try:
        import forge_mvc_images
    except ImportError as exc:  # pragma: no cover - dépend de l'environnement
        raise UploadStorageError(
            "Le traitement d'image requiert l'opt-in forge-mvc-images "
            "(pip install forge-mvc-images)."
        ) from exc
    return getattr(forge_mvc_images, name)


def save_upload(file, category: str = "documents") -> SavedUpload:
    """Upload brut **générique** : valide, écrit, retourne un SavedUpload.

    CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : ``save_upload`` ne connaît plus
    rien des images (ni vérification de contenu, ni variantes). Le chemin
    image-aware (vérification + variantes) appartient à l'opt-in
    ``forge-mvc-images`` (``save_image_upload``), qui s'appuie lui-même sur cette
    primitive générique. ``variants`` renvoyé est toujours vide ici.
    """
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
    root = upload_root()
    saved_path = storage.save_bytes(
        data,
        original_name=filename,
        category=category,
        root=root,
    )
    relative_path = saved_path.relative_to(root.resolve()).as_posix()
    normalized_path = storage.normalize_media_path(relative_path)

    return SavedUpload(
        filename=saved_path.name,
        original_name=filename,
        path=normalized_path,
        category=category,
        size=len(data),
        mime_type=mime_type,
        variants={},
    )


def delete_upload(path) -> bool:
    return storage.delete_file(path, root=upload_root())


def delete_media_file(path: str, *, root: str | Path | None = None, variants: bool = False) -> dict[str, bool]:
    if root is None:
        root = upload_root()

    relative_path = storage.normalize_media_path(path)
    paths = {"original": relative_path}
    if variants:
        image_variant_relative_paths = _require_image_processing(
            "image_variant_relative_paths"
        )
        paths = image_variant_relative_paths(relative_path)

    return {
        media_path: storage.delete_file(media_path, root=root)
        for media_path in paths.values()
    }


def serve_media_file(path: str, *, root: str | Path | None = None) -> Response:
    if root is None:
        root = upload_root()

    try:
        relative_path = storage.normalize_media_path(path)
        target = storage.media_path_to_storage_path(relative_path, root=root)
        if not target.exists() or not target.is_file():
            return Response(404, b"Not found", "text/plain; charset=utf-8")
        content = target.read_bytes()
    except (OSError, UploadStorageError):
        return Response(404, b"Not found", "text/plain; charset=utf-8")

    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return Response(200, content, content_type)


def get_upload_path(filename: str, category: str = "documents") -> Path:
    return storage.get_upload_path(filename, category, root=upload_root())
