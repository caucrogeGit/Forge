from __future__ import annotations

from pathlib import PurePosixPath

# IMAGES-MOVE-APPLICATIVE-001 (ADR-018) : repository + galerie rapatriés dans
# forge_mvc_images. Import depuis les sous-modules (et non la racine du paquet)
# pour rester insensible à l'ordre de binding de __init__.
from forge_mvc_images.processing import (
    ALLOWED_IMAGE_EXTENSIONS,
    image_variant_relative_paths,
)
from forge_mvc_images.media_repository import list_media_for_entity
from core.uploads.storage import normalize_media_path


def media_url(path: str) -> str:
    return f"/media/{normalize_media_path(path)}"


def get_media_gallery(
    entity_name: str,
    entity_id: int,
    *,
    role: str = "gallery",
    db=None,
) -> list[dict]:
    if not isinstance(role, str) or not role.strip():
        raise ValueError("role est obligatoire.")

    medias = list_media_for_entity(entity_name, entity_id, role=role, db=db)
    return [_gallery_item(media) for media in medias]


def get_cover_media(
    entity_name: str,
    entity_id: int,
    *,
    role: str = "cover",
    fallback_to_gallery: bool = False,
    db=None,
) -> dict | None:
    if not isinstance(role, str) or not role.strip():
        raise ValueError("role est obligatoire.")

    covers = list_media_for_entity(entity_name, entity_id, role=role, db=db)
    if covers:
        return _gallery_item(covers[0])

    if not fallback_to_gallery:
        return None

    for media in list_media_for_entity(entity_name, entity_id, role="gallery", db=db):
        item = _gallery_item(media)
        if item["medium_url"] is not None:
            return item
    return None


def _gallery_item(media: dict) -> dict:
    path = normalize_media_path(media["path"])
    item = dict(media)
    item["path"] = path
    item["url"] = media_url(path)
    item["medium_path"] = None
    item["medium_url"] = None
    item["thumbnail_path"] = None
    item["thumbnail_url"] = None

    if _is_image_path(path):
        variants = image_variant_relative_paths(path)
        item["medium_path"] = variants["medium"]
        item["medium_url"] = media_url(variants["medium"])
        item["thumbnail_path"] = variants["thumbnail"]
        item["thumbnail_url"] = media_url(variants["thumbnail"])

    return item


def _is_image_path(path: str) -> bool:
    extension = PurePosixPath(path).suffix.lower().lstrip(".")
    return extension in ALLOWED_IMAGE_EXTENSIONS
