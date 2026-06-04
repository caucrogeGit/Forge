"""Garde-fou SEC-UPLOAD-DECOMPRESSION-BOMB-001.

Vérifie qu'une image dont la surface en pixels dépasse le plafond configuré
(`upload_max_image_pixels`) est refusée AVANT décodage / écriture disque, et
qu'une image dans le budget passe normalement.

Le test règle volontairement un plafond très bas (quelques pixels) sur de
petites images réelles : la logique de garde est exercée sans allouer d'image
démesurée en mémoire.
"""
import io
from types import SimpleNamespace

import pytest
pytest.importorskip("forge_mvc_images")
from PIL import Image

import core.forge as forge
from core.forms.upload_exceptions import UploadStorageError
# IMAGES-MOVE-PROCESSING-001 (ADR-018) : le traitement d'image vit dans l'opt-in.
from forge_mvc_images import (
    ALLOWED_IMAGE_EXTENSIONS,
    generate_image_variants,
    save_image,
    verify_image_content,
)


def _image_bytes(size=(8, 8), fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", size, color=(210, 40, 70)).save(buf, format=fmt)
    return buf.getvalue()


def _configure(tmp_path, *, max_pixels):
    forge.configure(
        upload_root=str(tmp_path / "uploads"),
        upload_max_size=10_000_000,
        upload_max_image_pixels=max_pixels,
        upload_allowed_extensions=list(ALLOWED_IMAGE_EXTENSIONS),
        upload_allowed_mime_types=["image/jpeg", "image/png", "image/webp"],
    )


@pytest.fixture(autouse=True)
def _restore_pixel_cap():
    """Isolation : restaure le plafond global après chaque test (la config
    Forge est mutable et partagée — sinon un plafond bas fuirait vers les
    autres tests d'upload et les ferait échouer par effet d'ordre)."""
    original = forge.get("upload_max_image_pixels")
    yield
    forge.configure(upload_max_image_pixels=original)


# ── Config ───────────────────────────────────────────────────────────────────

def test_config_upload_max_image_pixels_existe():
    """La clé de config existe et a une valeur entière positive."""
    value = forge.get("upload_max_image_pixels")
    assert isinstance(value, int) and value > 0


# ── verify_image_content (défense à l'upload, sur l'en-tête) ──────────────────

def test_verify_rejette_image_au_dela_du_plafond(tmp_path):
    _configure(tmp_path, max_pixels=50)  # 8×8 = 64 px > 50
    with pytest.raises(UploadStorageError) as exc:
        verify_image_content(_image_bytes(size=(8, 8)))
    assert "pixels" in str(exc.value).lower()


def test_verify_accepte_image_dans_le_plafond(tmp_path):
    _configure(tmp_path, max_pixels=1_000_000)  # 8×8 = 64 px ≤ 1e6
    # Ne doit lever aucune exception.
    verify_image_content(_image_bytes(size=(8, 8)))


# ── save_image (intégration : rejet avant écriture disque) ────────────────────

def test_save_image_rejette_bomb_avant_ecriture(tmp_path):
    _configure(tmp_path, max_pixels=50)
    uploads = tmp_path / "uploads"
    file = SimpleNamespace(
        filename="bomb.png", content=_image_bytes(size=(8, 8)), content_type="image/png"
    )
    with pytest.raises(UploadStorageError):
        save_image(file)
    # Aucune image n'a été écrite (rejet AVANT storage.save_bytes).
    written = list(uploads.rglob("*.png")) if uploads.exists() else []
    assert written == []


# ── generate_image_variants (défense en profondeur) ──────────────────────────

def test_generate_variants_rejette_image_au_dela_du_plafond(tmp_path):
    _configure(tmp_path, max_pixels=1_000_000)
    root = tmp_path / "uploads"
    original = root / "images" / "photo.png"
    original.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (2000, 1000), color=(10, 20, 30)).save(original, format="PNG")

    # Plafond resserré sous la taille réelle (2 000 000 px) → rejet.
    _configure(tmp_path, max_pixels=500_000)
    with pytest.raises(UploadStorageError):
        generate_image_variants("images/photo.png", root=str(root))


def test_generate_variants_accepte_image_dans_le_plafond(tmp_path):
    _configure(tmp_path, max_pixels=10_000_000)
    root = tmp_path / "uploads"
    original = root / "images" / "photo.png"
    original.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (400, 300), color=(10, 20, 30)).save(original, format="PNG")

    result = generate_image_variants("images/photo.png", root=str(root))
    assert "medium" in result and "thumbnail" in result
