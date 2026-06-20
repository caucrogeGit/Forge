# pyright: strict
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

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
    variants: dict[str, str] = field(default_factory=dict[str, str])


def _read_upload(file: object) -> tuple[str | None, str | None, bytes]:
    # Frontière : ``file`` est un objet d'upload duck-typé (multipart, fichier
    # Python, wrapper applicatif). On lit ses attributs par ``getattr`` et on
    # ``cast`` aux types attendus, comme la recette de typage du cœur.
    filename = cast("str | None", getattr(file, "filename", None) or getattr(file, "name", None))
    mime_type = cast(
        "str | None",
        getattr(file, "content_type", None)
        or getattr(file, "mimetype", None)
        or getattr(file, "mime_type", None),
    )

    data: object
    if hasattr(file, "content"):
        data = getattr(file, "content")
    elif hasattr(file, "read"):
        data = cast("Callable[[], object]", getattr(file, "read"))()
    elif hasattr(file, "stream") and hasattr(getattr(file, "stream"), "read"):
        data = cast("Callable[[], object]", getattr(getattr(file, "stream"), "read"))()
    else:
        data = file

    if isinstance(data, str):
        data = data.encode("utf-8")
    if data is None:
        data = b""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Le fichier uploadé doit fournir des bytes ou une méthode read().")

    return filename, mime_type, bytes(data)


# ADR-032 : la config de stockage et de validation d'upload appartient à
# l'opt-in files, lue directement depuis l'environnement. Seul `upload_max_size`
# reste détenu par le noyau (borne le corps multipart dans core/http/request.py).
_DEFAULT_EXTENSIONS = "jpg,jpeg,png,webp,pdf"
_DEFAULT_MIME_TYPES = "image/jpeg,image/png,image/webp,application/pdf"


def _env_list(key: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(key, default).split(",") if item.strip()]


def upload_root() -> Path:
    return Path(os.getenv("UPLOAD_ROOT", "storage/uploads"))


def _require_image_processing(name: str) -> Any:
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
        import forge_mvc_images  # pyright: ignore[reportMissingImports]
    except ImportError as exc:  # pragma: no cover - dépend de l'environnement
        raise UploadStorageError(
            "Le traitement d'image requiert l'opt-in forge-mvc-images "
            "(pip install forge-mvc-images)."
        ) from exc
    return getattr(forge_mvc_images, name)


def save_upload(file: object, category: str = "documents") -> SavedUpload:
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
        allowed_extensions=_env_list("UPLOAD_ALLOWED_EXTENSIONS", _DEFAULT_EXTENSIONS),
        allowed_mime_types=_env_list("UPLOAD_ALLOWED_MIME_TYPES", _DEFAULT_MIME_TYPES),
        max_size=int(_cfg("upload_max_size")),
    )
    # validate_upload_metadata lève si le nom est absent : filename est ici un str.
    safe_name = cast("str", filename)
    root = upload_root()
    saved_path = storage.save_bytes(
        data,
        original_name=safe_name,
        category=category,
        root=root,
    )
    relative_path = saved_path.relative_to(root.resolve()).as_posix()
    normalized_path = storage.normalize_media_path(relative_path)

    return SavedUpload(
        filename=saved_path.name,
        original_name=safe_name,
        path=normalized_path,
        category=category,
        size=len(data),
        mime_type=mime_type,
        variants={},
    )


def delete_upload(path: str | Path) -> bool:
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
        paths = cast("dict[str, str]", image_variant_relative_paths(relative_path))

    return {
        media_path: storage.delete_file(media_path, root=root)
        for media_path in paths.values()
    }


def serve_media_file(
    path: str, *, root: str | Path | None = None, request: Any = None
) -> Response:
    """Sert un média avec streaming et support HTTP Range.

    Après la résolution anti-traversal, le service est délégué à
    ``Response.file`` (FILES-SERVE-RANGE-DELEGATE-001) : le corps n'est jamais
    chargé en mémoire (émission par tranches), et l'en-tête ``Range`` de
    `request` est honoré (206 / 416). Sans `request`, le fichier est servi en
    streaming complet (200). Tout chemin invalide ou absent donne un 404.
    """
    if root is None:
        root = upload_root()

    try:
        relative_path = storage.normalize_media_path(path)
        target = storage.media_path_to_storage_path(relative_path, root=root)
        if not target.exists() or not target.is_file():
            return Response(404, b"Not found", "text/plain; charset=utf-8")
        return Response.file(target, request)
    except (OSError, UploadStorageError):
        return Response(404, b"Not found", "text/plain; charset=utf-8")


def get_upload_path(filename: str, category: str = "documents") -> Path:
    return storage.get_upload_path(filename, category, root=upload_root())
