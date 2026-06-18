# pyright: strict
"""Traitement d'image Forge — validation de contenu, upload, variantes.

Déplacé du core (``core/uploads/image.py``) vers l'opt-in ``forge-mvc-images``
par ``IMAGES-MOVE-PROCESSING-001`` (ADR-018). Pillow devient une dépendance de
ce module et quitte le runtime du core (principe 8 — noyau minimal).

Le module s'appuie sur les briques d'upload **génériques** restées dans le core
(``core.uploads`` : storage, validators, exceptions, ``_read_upload``,
``upload_root``). Le core conserve l'upload brut ; ``forge-mvc-images`` fournit
le chemin image-aware (validation de contenu + écriture + variantes).
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from PIL import Image, UnidentifiedImageError

from core.forge import get as _cfg

# FILES-IMAGES-REPOINT-001 (ADR-019) : le pipeline d'upload vit dans
# forge-mvc-files (dépendance déclarée) ; la validation pure reste dans le core.
from core.forms.upload_exceptions import UploadStorageError
from core.forms.upload_validation import validate_upload_metadata
from forge_mvc_files import storage
from forge_mvc_files.manager import (
    SavedUpload,
    _read_upload,  # pyright: ignore[reportPrivateUsage]
    save_upload as _core_save_upload,
    upload_root,
)


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


_VERIFIABLE_IMAGE_FORMATS: frozenset[str] = frozenset({"JPEG", "PNG", "WEBP"})


def _ensure_within_pixel_budget(width: int, height: int) -> None:
    """Rejette une image dont la surface dépasse ``upload_max_image_pixels``.

    SEC-UPLOAD-DECOMPRESSION-BOMB-001 — le contrôle porte sur les dimensions
    lues dans l'EN-TÊTE (``Image.open`` n'a pas encore décodé les pixels) : une
    « décompression-bomb » (fichier léger se décompressant en une image
    démesurée) est refusée AVANT tout décodage et toute écriture disque, à coût
    mémoire négligeable. Le plafond est configurable par projet.
    """
    # ADR-032 : plafond anti-bombe lu depuis l'environnement, propriété de
    # l'opt-in images (le core ne déclare plus ce slot).
    max_pixels = int(os.getenv("UPLOAD_MAX_IMAGE_PIXELS", "24000000"))
    if width * height > max_pixels:
        raise UploadStorageError(
            f"Image trop volumineuse ({width}×{height} pixels) ; "
            f"plafond autorisé : {max_pixels} pixels."
        )


def verify_image_content(data: bytes) -> None:
    """Vérifie que ``data`` est bien une image raster d'un format autorisé.

    SEC-UPLOAD-IMAGE-VERIFY-001 / 002 — défense contre un fichier non-image
    présenté avec une extension/MIME d'image (Content-Type falsifiable).
    Helper partagé : appelé par ``save_image`` et par le chemin image-aware de
    ``core.uploads.save_upload`` (catégorie ``images``) AVANT toute écriture
    disque.

    On s'appuie sur ``Image.open`` (identification du format par en-tête) plutôt
    que sur ``Image.verify`` : ce dernier vérifie l'intégrité CRC et rejette des
    images réelles mais légèrement malformées (faux positifs). Ici l'objectif
    est de distinguer une vraie image d'un fichier déguisé (PDF, script, SVG…) ;
    l'identification du format suffit, complétée par une liste blanche alignée
    sur ``ALLOWED_IMAGE_MIME_TYPES``.
    """
    try:
        with Image.open(io.BytesIO(data)) as probe:
            image_format = probe.format
            width, height = probe.size
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise UploadStorageError(
            "Le fichier fourni n'est pas une image valide."
        ) from exc
    # SEC-UPLOAD-DECOMPRESSION-BOMB-001 — rejet des images démesurées avant
    # toute écriture disque ou décodage de variantes.
    _ensure_within_pixel_budget(width, height)
    if image_format not in _VERIFIABLE_IMAGE_FORMATS:
        raise UploadStorageError(
            "Le fichier fourni n'est pas une image valide "
            f"(format détecté : {image_format})."
        )


def save_image(
    file: object,
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

    # SEC-UPLOAD-IMAGE-VERIFY-001 — la validation ci-dessus ne porte que
    # sur des métadonnées déclaratives (extension + Content-Type fournis
    # par le client). On vérifie ici que le contenu est réellement une
    # image décodable AVANT de l'écrire sur le disque (charte §7).
    verify_image_content(data)

    # validate_upload_metadata lève si le nom est absent : filename est ici un str.
    safe_name = cast("str", filename)
    root = upload_root()
    saved_path = storage.save_bytes(
        data,
        original_name=safe_name,
        category=category,
        root=root,
    )
    relative_path = saved_path.relative_to(Path(root).resolve())

    return MediaRecord(
        filename=saved_path.name,
        original_name=safe_name,
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
            _ensure_within_pixel_budget(image.width, image.height)
            image.verify()
        with Image.open(original) as image:
            _ensure_within_pixel_budget(image.width, image.height)
            for variant, size in IMAGE_VARIANT_SIZES.items():
                target = physical_paths[variant]
                _write_resized_image(image, target, size)
    except UnidentifiedImageError as exc:
        raise UploadStorageError("Fichier source non reconnu comme image compatible.") from exc
    except Image.DecompressionBombError as exc:
        # Défense en profondeur : backstop de Pillow si une image démesurée
        # atteignait malgré tout le décodage (SEC-UPLOAD-DECOMPRESSION-BOMB-001).
        raise UploadStorageError(
            "Image source trop volumineuse (protection décompression-bomb)."
        ) from exc
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


def save_image_upload(file: object, category: str = "images", *, variants: bool = True) -> SavedUpload:
    """Chemin d'upload **image-aware** : vérifie le contenu, écrit, génère les variantes.

    CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : ``core.uploads.save_upload`` est
    désormais purement générique (aucune connaissance des images). Ce point
    d'entrée appartient à ``forge-mvc-images`` ; c'est lui que génèrent les CRUD
    pour les champs image. Il :

    1. vérifie que le contenu est une vraie image AVANT toute écriture disque
       (``verify_image_content`` — SEC-UPLOAD-IMAGE-VERIFY, garde anti-bombe) ;
    2. écrit le fichier via le ``save_upload`` **générique** du core ;
    3. génère, si demandé, les variantes ``medium`` / ``thumbnail``.

    Retourne le même ``SavedUpload`` que ``core.uploads.save_upload`` (avec le
    dictionnaire ``variants`` renseigné si ``variants=True``).
    """
    if file is None:
        raise UploadStorageError("Aucun fichier reçu.")

    filename, mime_type, data = _read_upload(file)
    # SEC-UPLOAD-IMAGE-VERIFY — contenu réellement décodable AVANT écriture.
    verify_image_content(data)

    raw = SimpleNamespace(filename=filename, content=data, content_type=mime_type)
    saved = _core_save_upload(raw, category)

    if variants:
        generated = generate_image_variants(saved.path)
        saved = replace(
            saved,
            variants={
                "medium": generated["medium"],
                "thumbnail": generated["thumbnail"],
            },
        )
    return saved
