import io
from types import SimpleNamespace

import pytest
pytest.importorskip("forge_mvc_images")
from PIL import Image

import core.forge as forge
from core.forms.upload_exceptions import (
    UploadInvalidExtensionError,
    UploadStorageError,
    UploadTooLargeError,
)
# IMAGES-MOVE-PROCESSING-001 (ADR-018) : le traitement d'image vit dans l'opt-in.
from forge_mvc_images import (
    ALLOWED_IMAGE_EXTENSIONS,
    MediaRecord,
    generate_image_variants,
    image_variant_relative_paths,
    image_variant_paths,
    save_image,
)
from forge_cli.uploads import init_media_storage


def _real_image_bytes(content_type="image/jpeg"):
    """Octets d'une vraie image décodable (SEC-UPLOAD-IMAGE-VERIFY-001)."""
    fmt = {"image/png": "PNG", "image/webp": "WEBP", "image/jpeg": "JPEG"}.get(
        content_type, "JPEG"
    )
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(210, 40, 70)).save(buf, format=fmt)
    return buf.getvalue()


def _img(filename="photo.jpg", content=None, content_type="image/jpeg"):
    # Depuis SEC-UPLOAD-IMAGE-VERIFY-001, save_image vérifie le contenu :
    # par défaut on fournit donc une vraie image. ``content=`` permet
    # d'injecter un contenu arbitraire (taille, contenu non-image).
    if content is None:
        content = _real_image_bytes(content_type)
    return SimpleNamespace(filename=filename, content=content, content_type=content_type)


@pytest.fixture(autouse=True)
def _isolate_upload_env(monkeypatch):
    """ADR-032 : vide les variables d'upload extraites du core avant chaque test."""
    for key in (
        "UPLOAD_ALLOWED_EXTENSIONS",
        "UPLOAD_ALLOWED_MIME_TYPES",
        "UPLOAD_MAX_IMAGE_PIXELS",
    ):
        monkeypatch.delenv(key, raising=False)


def _cfg(tmp_path, monkeypatch, max_size=100_000):
    # ADR-032 : upload_root, extensions et types MIME lus depuis l'environnement.
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    monkeypatch.setenv("UPLOAD_ALLOWED_EXTENSIONS", ",".join(ALLOWED_IMAGE_EXTENSIONS))
    monkeypatch.setenv("UPLOAD_ALLOWED_MIME_TYPES", "image/jpeg,image/png,image/webp")
    forge.configure(upload_max_size=max_size)


def _write_image(path, *, size=(2000, 1000), fmt="PNG"):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color=(210, 40, 70))
    image.save(path, format=fmt)


# ── Validation extension ─────────────────────────────────────────────────────

def test_save_image_accepte_extensions_valides(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    for ext, mime in [("jpg", "image/jpeg"), ("png", "image/png"), ("webp", "image/webp")]:
        record = save_image(_img(f"photo.{ext}", content_type=mime))
        assert record.filename.endswith(f".{ext}")


def test_save_image_refuse_extension_non_image(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    with pytest.raises(UploadInvalidExtensionError):
        save_image(_img("facture.pdf", content_type="application/pdf"))


def test_save_image_refuse_extension_executable(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    with pytest.raises(UploadInvalidExtensionError):
        save_image(_img("shell.php", content_type="application/x-php"))


def test_save_image_refuse_svg(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    with pytest.raises(UploadInvalidExtensionError):
        save_image(_img("icone.svg", content_type="image/svg+xml"))


def test_save_image_refuse_gif(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    with pytest.raises(UploadInvalidExtensionError):
        save_image(_img("animation.gif", content_type="image/gif"))


# ── Validation taille ────────────────────────────────────────────────────────

def test_save_image_refuse_fichier_trop_lourd(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch, max_size=5)
    with pytest.raises(UploadTooLargeError):
        save_image(_img(content=b"x" * 6))


# ── Validation contenu (SEC-UPLOAD-IMAGE-VERIFY-001) ─────────────────────────

def test_save_image_refuse_contenu_non_image(tmp_path, monkeypatch):
    """Extension + MIME d'image valides mais contenu falsifié → rejet.

    Le Content-Type est fourni par le client (falsifiable) : un fichier
    non-image déguisé en .jpg image/jpeg doit être rejeté AVANT écriture.
    """
    _cfg(tmp_path, monkeypatch)
    fake = _img(
        "photo.jpg",
        content=b"%PDF-1.4 ceci n'est pas une image",
        content_type="image/jpeg",
    )
    with pytest.raises(UploadStorageError, match="n'est pas une image valide"):
        save_image(fake)

    # Et rien ne doit avoir été écrit sur le disque.
    images_dir = tmp_path / "uploads" / "images"
    written = list(images_dir.glob("*")) if images_dir.exists() else []
    assert not written, f"un fichier a été écrit malgré un contenu invalide : {written}"


# ── Nom dangereux ─────────────────────────────────────────────────────────────

def test_save_image_neutralise_nom_dangereux(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    record = save_image(_img("../../../evil.jpg"))
    assert ".." not in record.filename
    assert record.filename.endswith(".jpg")
    assert (tmp_path / "uploads" / "images" / record.filename).exists()


# ── Dossier de stockage ──────────────────────────────────────────────────────

def test_save_image_stocke_dans_dossier_images_par_defaut(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    record = save_image(_img())
    assert record.category == "images"
    assert (tmp_path / "uploads" / "images" / record.filename).exists()


def test_save_image_remplit_media_record(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    record = save_image(
        _img("portrait.jpg"),
        entity_name="Personne",
        entity_id=7,
        usage="cover",
        position=1,
        is_main=True,
    )
    assert isinstance(record, MediaRecord)
    assert record.entity_name == "Personne"
    assert record.entity_id == 7
    assert record.usage == "cover"
    assert record.position == 1
    assert record.is_main is True
    assert record.original_name == "portrait.jpg"
    assert record.mime_type == "image/jpeg"


def test_save_image_stocke_chemin_relatif(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    record = save_image(_img())
    from pathlib import Path
    assert not Path(record.path).is_absolute(), f"chemin absolu inattendu : {record.path!r}"
    assert record.path.startswith("images/"), f"chemin inattendu : {record.path!r}"


def test_save_image_chemin_reconstituable_depuis_root(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    record = save_image(_img())
    root = tmp_path / "uploads"
    full = (root / record.path).resolve()
    assert full.exists(), f"fichier introuvable via root + chemin relatif : {full}"


def test_save_image_none_leve_storage_error(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    with pytest.raises(UploadStorageError, match="Aucun fichier reçu"):
        save_image(None)


# ── Variantes ────────────────────────────────────────────────────────────────

def test_image_variant_paths_retourne_trois_variantes(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch)
    record = save_image(_img())
    root = tmp_path / "uploads"
    variants = image_variant_paths(record.path, root=root)
    assert set(variants.keys()) == {"original", "thumbnail", "medium"}
    # original → directement dans images/ (CHOIX A, pas images/original/)
    assert variants["original"].exists()
    assert variants["original"].parent == (root / "images").resolve()
    # thumbnail et medium → sous-dossiers de images/
    assert variants["thumbnail"].parent == (root / "images" / "thumbnail").resolve()
    assert variants["medium"].parent == (root / "images" / "medium").resolve()
    # même nom de fichier pour les trois variantes
    assert variants["thumbnail"].name == variants["original"].name
    assert variants["medium"].name == variants["original"].name


def test_image_variant_relative_paths_retourne_chemins_relatifs_normalises():
    variants = image_variant_relative_paths("storage/uploads/images/photo.png")

    assert variants == {
        "original": "images/photo.png",
        "medium": "images/medium/photo.png",
        "thumbnail": "images/thumbnail/photo.png",
    }


def test_generate_image_variants_depuis_png(tmp_path):
    root = tmp_path / "uploads"
    source = root / "images" / "photo.png"
    _write_image(source)

    variants = generate_image_variants("images/photo.png", root=root)

    assert variants == {
        "original": "images/photo.png",
        "medium": "images/medium/photo.png",
        "thumbnail": "images/thumbnail/photo.png",
    }
    for relative_path in variants.values():
        assert not relative_path.startswith("/")
        assert ".." not in relative_path
        assert (root / relative_path).exists()


def test_generate_image_variants_conserve_original(tmp_path):
    root = tmp_path / "uploads"
    source = root / "images" / "photo.png"
    _write_image(source, size=(640, 480))
    before = source.read_bytes()

    generate_image_variants("images/photo.png", root=root)

    assert source.read_bytes() == before


def test_generate_image_variants_conserve_proportions(tmp_path):
    root = tmp_path / "uploads"
    source = root / "images" / "photo.png"
    _write_image(source, size=(2000, 1000))

    variants = generate_image_variants("images/photo.png", root=root)

    with Image.open(root / variants["medium"]) as medium:
        assert medium.size == (1280, 640)
    with Image.open(root / variants["thumbnail"]) as thumbnail:
        assert thumbnail.size == (300, 150)


def test_generate_image_variants_cree_dossiers_si_absents(tmp_path):
    root = tmp_path / "uploads"
    source = root / "images" / "photo.png"
    _write_image(source)

    generate_image_variants("images/photo.png", root=root)

    assert (root / "images" / "medium").is_dir()
    assert (root / "images" / "thumbnail").is_dir()


def test_generate_image_variants_refuse_source_inexistante(tmp_path):
    with pytest.raises(UploadStorageError, match="introuvable"):
        generate_image_variants("images/missing.png", root=tmp_path / "uploads")


def test_generate_image_variants_refuse_chemin_dangereux(tmp_path):
    with pytest.raises(UploadStorageError):
        generate_image_variants("../secret.png", root=tmp_path / "uploads")


def test_generate_image_variants_refuse_fichier_non_image(tmp_path):
    root = tmp_path / "uploads"
    source = root / "images" / "fake.png"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("not an image", encoding="utf-8")

    with pytest.raises(UploadStorageError, match="non reconnu"):
        generate_image_variants("images/fake.png", root=root)


def test_generate_image_variants_refuse_svg(tmp_path):
    root = tmp_path / "uploads"
    source = root / "images" / "icone.svg"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("<svg></svg>", encoding="utf-8")

    with pytest.raises(UploadStorageError, match="non supporte"):
        generate_image_variants("images/icone.svg", root=root)


def test_generate_image_variants_ne_sort_pas_de_upload_root(tmp_path):
    root = tmp_path / "uploads"
    source = root / "images" / "photo.png"
    _write_image(source)

    variants = generate_image_variants(r"images\photo.png", root=root)

    for relative_path in variants.values():
        assert (root / relative_path).resolve().is_relative_to(root.resolve())


# ── media:init idempotent ────────────────────────────────────────────────────

def test_media_init_cree_dossiers_variantes(tmp_path):
    root = tmp_path / "storage" / "uploads"
    init_media_storage(root)
    assert (root / "images" / "thumbnail").is_dir()
    assert (root / "images" / "medium").is_dir()
    assert (root / "images" / "thumbnail" / ".gitkeep").exists()
    assert (root / "images" / "medium" / ".gitkeep").exists()


def test_media_init_est_idempotent(tmp_path):
    root = tmp_path / "storage" / "uploads"
    init_media_storage(root)
    init_media_storage(root)
    assert (root / "images" / "thumbnail").is_dir()
    assert (root / "images" / "medium").is_dir()
