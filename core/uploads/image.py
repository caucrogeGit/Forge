"""Service image générique Forge — upload, variantes, liaison entité."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.forge import get as _cfg
from core.uploads import storage
from core.uploads.exceptions import UploadStorageError
from core.uploads.manager import _read_upload, upload_root
from core.uploads.validators import validate_upload_metadata


ALLOWED_IMAGE_EXTENSIONS: frozenset[str] = frozenset({"jpg", "jpeg", "png", "webp"})
ALLOWED_IMAGE_MIME_TYPES: frozenset[str] = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})
IMAGE_VARIANT_SIZES: dict[str, tuple[int, int]] = {
    "medium": (1280, 1280),
    "thumbnail": (300, 300),
}


@dataclass(frozen=True)
class MediaRecord:
    """Association générique entre un fichier média et une entité Forge.

    Persistance à la charge de l'application (pas de table SQL imposée en V1).
    """

    filename: str
    original_name: str
    path: str
    category: str
    size: int
    mime_type: str | None = None
    entity_name: str | None = None
    entity_id: int | None = None
    usage: str = "main"
    position: int = 0
    is_main: bool = True


def save_image(
    file,
    *,
    category: str = "images",
    entity_name: str | None = None,
    entity_id: int | None = None,
    usage: str = "main",
    position: int = 0,
    is_main: bool = True,
) -> MediaRecord:
    """Upload et sauvegarde une image ; retourne un MediaRecord.

    Valide l'extension contre ALLOWED_IMAGE_EXTENSIONS et le MIME contre
    ALLOWED_IMAGE_MIME_TYPES. Limite de taille lue depuis UPLOAD_MAX_SIZE.
    """
    if file is None:
        raise UploadStorageError("Aucun fichier reçu.")

    filename, mime_type, data = _read_upload(file)

    validate_upload_metadata(
        filename=filename,
        size=len(data),
        mime_type=mime_type,
        allowed_extensions=list(ALLOWED_IMAGE_EXTENSIONS),
        allowed_mime_types=list(ALLOWED_IMAGE_MIME_TYPES),
        max_size=int(_cfg("upload_max_size")),
    )

    root = upload_root()
    saved_path = storage.save_bytes(
        data,
        original_name=filename,
        category=category,
        root=root,
    )
    relative_path = saved_path.relative_to(Path(root).resolve())

    return MediaRecord(
        filename=saved_path.name,
        original_name=filename,
        path=relative_path.as_posix(),
        category=category,
        size=len(data),
        mime_type=mime_type,
        entity_name=entity_name,
        entity_id=entity_id,
        usage=usage,
        position=position,
        is_main=is_main,
    )


def image_variant_paths(path: str | Path, *, root: str | Path | None = None) -> dict[str, Path]:
    """Retourne les chemins physiques des trois variantes d'une image."""
    if root is None:
        root = upload_root()
    relative_path = storage.normalize_media_path(str(path))
    original = storage.media_path_to_storage_path(relative_path, root=root)
    parent = original.parent
    stem = original.stem
    suffix = original.suffix

    return {
        "original": original,
        "thumbnail": parent / "thumbnail" / f"{stem}{suffix}",
        "medium": parent / "medium" / f"{stem}{suffix}",
    }


def image_variant_relative_paths(path: str | Path) -> dict[str, str]:
    """Retourne les chemins relatifs normalises des variantes d'une image."""
    original = storage.normalize_media_path(str(path))
    original_path = Path(original)
    parent = original_path.parent.as_posix()
    stem = original_path.stem
    suffix = original_path.suffix
    return {
        "original": original,
        "medium": storage.normalize_media_path(f"{parent}/medium/{stem}{suffix}"),
        "thumbnail": storage.normalize_media_path(f"{parent}/thumbnail/{stem}{suffix}"),
    }


def generate_image_variants(path: str | Path, *, root: str | Path | None = None) -> dict[str, str]:
    """Genere les variantes medium et thumbnail d'une image stockee.

    Le fichier original est conserve tel quel. La fonction retourne uniquement
    des chemins relatifs normalises, compatibles avec `Media.path`.
    """
    if root is None:
        root = upload_root()

    relative_paths = image_variant_relative_paths(path)
    physical_paths = image_variant_paths(relative_paths["original"], root=root)
    original = physical_paths["original"]
    if not original.exists() or not original.is_file():
        raise UploadStorageError("Image source introuvable.")

    extension = original.suffix.lower().lstrip(".")
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise UploadStorageError(f"Format image non supporte : {extension or '<aucun>'}.")

    try:
        with Image.open(original) as image:
            image.verify()
        with Image.open(original) as image:
            for variant, size in IMAGE_VARIANT_SIZES.items():
                target = physical_paths[variant]
                _write_resized_image(image, target, size)
    except UnidentifiedImageError as exc:
        raise UploadStorageError("Fichier source non reconnu comme image compatible.") from exc
    except OSError as exc:
        raise UploadStorageError(f"Impossible de generer les variantes image : {exc}") from exc

    return relative_paths


def _write_resized_image(image: Image.Image, target: Path, max_size: tuple[int, int]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    variant = image.copy()
    variant.thumbnail(max_size, Image.Resampling.LANCZOS)
    if target.suffix.lower() in {".jpg", ".jpeg"} and variant.mode not in {"RGB", "L"}:
        variant = variant.convert("RGB")
    variant.save(target)
