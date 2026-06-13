from io import BytesIO
from types import SimpleNamespace

import pytest
pytest.importorskip("forge_mvc_files")
pytest.importorskip("forge_mvc_images")
from PIL import Image

import core.forge as forge
from core.forms.upload_exceptions import (
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)

# ADR-032 (UPLOAD-CONFIG-DECOUPLE-001) : upload_root, extensions et types MIME
# autorisés ne sont plus dans le registre core.forge ; l'opt-in files les lit
# depuis l'environnement. Seul upload_max_size reste détenu par le noyau.
_UPLOAD_ENV_KEYS = (
    "UPLOAD_ALLOWED_EXTENSIONS",
    "UPLOAD_ALLOWED_MIME_TYPES",
    "UPLOAD_MAX_IMAGE_PIXELS",
)


@pytest.fixture(autouse=True)
def _isolate_upload_env(monkeypatch):
    """Vide les variables d'upload avant chaque test (elles ont des défauts
    côté opt-in) ; chaque test pose ensuite ce dont il a besoin."""
    for key in _UPLOAD_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _configure_uploads(monkeypatch, *, upload_root, upload_max_size=None,
                       upload_allowed_extensions=None, upload_allowed_mime_types=None):
    """Pose la config d'upload : env pour les clés extraites (ADR-032),
    registre core.forge pour upload_max_size (resté dans le noyau)."""
    monkeypatch.setenv("UPLOAD_ROOT", str(upload_root))
    if upload_allowed_extensions is not None:
        monkeypatch.setenv("UPLOAD_ALLOWED_EXTENSIONS", ",".join(upload_allowed_extensions))
    if upload_allowed_mime_types is not None:
        monkeypatch.setenv("UPLOAD_ALLOWED_MIME_TYPES", ",".join(upload_allowed_mime_types))
    if upload_max_size is not None:
        forge.configure(upload_max_size=upload_max_size)
from forge_mvc_files.manager import delete_media_file, delete_upload, get_upload_path, save_upload

# CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : save_upload est purement générique ;
# le chemin image-aware (vérification + variantes) appartient à forge-mvc-images.
from forge_mvc_images import save_image_upload
from forge_mvc_files.storage import (
    ensure_upload_dirs,
    is_safe_media_path,
    media_path_to_storage_path,
    normalize_media_path,
    secure_filename,
)
from core.forms.upload_validation import validate_upload_metadata
from forge_cli.uploads import init_upload_storage


def _file(filename="avatar.png", content=b"abc", content_type="image/png"):
    return SimpleNamespace(filename=filename, content=content, content_type=content_type)


def _image_file(filename="photo.png", *, size=(2000, 1000), content_type="image/png"):
    buffer = BytesIO()
    image = Image.new("RGB", size, color=(80, 130, 210))
    image.save(buffer, format="PNG")
    return _file(filename=filename, content=buffer.getvalue(), content_type=content_type)


def test_validate_upload_metadata_accepte_fichier_valide():
    extension = validate_upload_metadata(
        filename="photo.PNG",
        size=42,
        mime_type="image/png",
        allowed_extensions=["png"],
        allowed_mime_types=["image/png"],
        max_size=100,
    )
    assert extension == "png"


def test_validate_upload_metadata_refuse_extension():
    with pytest.raises(UploadInvalidExtensionError):
        validate_upload_metadata(
            filename="shell.php",
            size=1,
            mime_type="application/x-php",
            allowed_extensions=["png"],
            allowed_mime_types=["image/png"],
            max_size=100,
        )


def test_validate_upload_metadata_refuse_taille():
    with pytest.raises(UploadTooLargeError):
        validate_upload_metadata(
            filename="doc.pdf",
            size=101,
            mime_type="application/pdf",
            allowed_extensions=["pdf"],
            allowed_mime_types=["application/pdf"],
            max_size=100,
        )


def test_validate_upload_metadata_refuse_mime():
    with pytest.raises(UploadInvalidMimeTypeError):
        validate_upload_metadata(
            filename="photo.png",
            size=10,
            mime_type="text/plain",
            allowed_extensions=["png"],
            allowed_mime_types=["image/png"],
            max_size=100,
        )


def test_secure_filename_nettoie_le_nom():
    assert secure_filename("../Mon fichier!.png") == "Mon_fichier_.png"


@pytest.mark.parametrize(
    "path",
    [
        "images/photo.jpg",
        "documents/contrat.pdf",
        "images/2026/photo.jpg",
        "tmp/upload.bin",
    ],
)
def test_normalize_media_path_accepte_chemins_relatifs(path):
    assert normalize_media_path(path) == path


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "../secret.txt",
        "images/../../secret.txt",
        "/home/roger/file.jpg",
        r"C:\Users\roger\file.jpg",
        "https://example.com/file.jpg",
        "http://example.com/file.jpg",
        "file:///tmp/test.jpg",
        "",
        None,
    ],
)
def test_normalize_media_path_refuse_chemins_dangereux(path):
    with pytest.raises(UploadStorageError):
        normalize_media_path(path)


def test_normalize_media_path_normalise_separateurs_et_doubles_slashs():
    assert normalize_media_path(r"images\2026//photo.jpg") == "images/2026/photo.jpg"


def test_normalize_media_path_conserve_espaces_internes():
    assert normalize_media_path("images/photo test.jpg") == "images/photo test.jpg"


def test_normalize_media_path_retire_prefixe_storage_uploads():
    assert normalize_media_path("storage/uploads/images/photo.jpg") == "images/photo.jpg"


def test_is_safe_media_path_retourne_booleen():
    assert is_safe_media_path("images/photo.jpg") is True
    assert is_safe_media_path("../secret.txt") is False


def test_media_path_to_storage_path_reste_sous_upload_root(tmp_path):
    target = media_path_to_storage_path("images/photo.jpg", root=tmp_path / "uploads")

    assert target == (tmp_path / "uploads" / "images" / "photo.jpg").resolve()


def test_media_path_to_storage_path_refuse_traversal(tmp_path):
    with pytest.raises(UploadStorageError):
        media_path_to_storage_path("images/../../secret.txt", root=tmp_path / "uploads")


def test_save_upload_ecrit_dans_la_categorie_configuree(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=100_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    # save_upload est générique (CORE-SAVEUPLOAD-GENERIC-CLEANUP) : il écrit
    # dans la catégorie demandée sans vérifier le contenu image. On fournit une
    # vraie image pour rester réaliste.
    image = _image_file()
    data = image.content
    saved = save_upload(image, category="images")

    assert saved.category == "images"
    assert saved.filename.endswith(".png")
    assert saved.path == f"images/{saved.filename}"
    assert not saved.path.startswith("/")
    assert saved.variants == {}
    assert saved.size == len(data)
    assert (tmp_path / "uploads" / "images" / saved.filename).read_bytes() == data


def test_save_upload_image_sans_variants_ne_genere_pas_de_variantes(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=10_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    saved = save_upload(_image_file(), category="images")

    assert saved.path == f"images/{saved.filename}"
    assert saved.variants == {}
    assert not (tmp_path / "uploads" / "images" / "medium" / saved.filename).exists()
    assert not (tmp_path / "uploads" / "images" / "thumbnail" / saved.filename).exists()


def test_save_upload_image_avec_variants_genere_medium_et_thumbnail(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=10_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    saved = save_image_upload(_image_file(), category="images", variants=True)

    assert saved.path == f"images/{saved.filename}"
    assert saved.variants == {
        "medium": f"images/medium/{saved.filename}",
        "thumbnail": f"images/thumbnail/{saved.filename}",
    }
    assert (tmp_path / "uploads" / saved.variants["medium"]).exists()
    assert (tmp_path / "uploads" / saved.variants["thumbnail"]).exists()


def test_save_upload_image_variants_conservent_les_proportions(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=10_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    saved = save_image_upload(_image_file(size=(2000, 1000)), category="images", variants=True)

    with Image.open(tmp_path / "uploads" / saved.variants["medium"]) as medium:
        assert medium.size == (1280, 640)
    with Image.open(tmp_path / "uploads" / saved.variants["thumbnail"]) as thumbnail:
        assert thumbnail.size == (300, 150)


def test_save_upload_image_variants_retourne_chemins_relatifs_surs(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=10_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    saved = save_image_upload(_image_file(), category="images", variants=True)

    assert not saved.path.startswith("/")
    assert ".." not in saved.path
    for relative_path in saved.variants.values():
        assert not relative_path.startswith("/")
        assert ".." not in relative_path


# CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : `test_save_upload_variants_refuse_categorie_non_image`
# retiré — save_upload n'a plus de paramètre `variants` ni de notion d'image ;
# la garde « variantes réservées aux images » n'a plus lieu d'être (save_image_upload
# est toujours image).


def test_save_image_upload_refuse_fichier_non_image(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=10_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    with pytest.raises(UploadStorageError, match="n'est pas une image valide"):
        save_image_upload(_file("fake.png", b"not an image", "image/png"), category="images", variants=True)


def test_save_image_upload_refuse_svg(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=10_000,
        upload_allowed_extensions=["svg"],
        upload_allowed_mime_types=["image/svg+xml"],
    )

    with pytest.raises(UploadStorageError, match="n'est pas une image valide"):
        save_image_upload(
            _file("icone.svg", b"<svg></svg>", "image/svg+xml"),
            category="images",
            variants=True,
        )


def test_save_image_upload_refuse_contenu_falsifie_sans_ecrire(tmp_path, monkeypatch):
    """SEC-UPLOAD-IMAGE-VERIFY-002 — contenu non-image en catégorie images.

    Extension + MIME d'image valides mais contenu falsifié : rejet AVANT
    écriture disque, que les variantes soient demandées ou non. Aucun
    fichier ne doit subsister sur le disque.
    """
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=100_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )
    images_dir = tmp_path / "uploads" / "images"

    for variants in (False, True):
        fake = _file("photo.png", b"%PDF-1.4 ceci n'est pas une image", "image/png")
        with pytest.raises(UploadStorageError, match="n'est pas une image valide"):
            save_image_upload(fake, category="images", variants=variants)
        written = (
            [p for p in images_dir.glob("*") if p.is_file()]
            if images_dir.exists()
            else []
        )
        assert not written, (
            f"un fichier a été écrit malgré un contenu invalide "
            f"(variants={variants}) : {written}"
        )


def test_save_upload_evite_ecrasement(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=100_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    first = save_upload(_image_file(), category="images")
    second = save_upload(_image_file(), category="images")

    assert first.filename != second.filename


def test_delete_upload_supprime_sous_upload_root(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=100_000,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )
    saved = save_upload(_image_file(), category="images")

    assert delete_upload(saved.path) is True
    assert delete_upload(saved.path) is False


def test_delete_media_file_supprime_fichier_simple(tmp_path):
    root = tmp_path / "uploads"
    target = root / "images" / "photo.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"image")

    result = delete_media_file("images/photo.png", root=root)

    assert result == {"images/photo.png": True}
    assert not target.exists()


def test_delete_media_file_supprime_image_et_variantes(tmp_path):
    root = tmp_path / "uploads"
    paths = [
        root / "images" / "photo.png",
        root / "images" / "medium" / "photo.png",
        root / "images" / "thumbnail" / "photo.png",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")

    result = delete_media_file("images/photo.png", root=root, variants=True)

    assert result == {
        "images/photo.png": True,
        "images/medium/photo.png": True,
        "images/thumbnail/photo.png": True,
    }
    assert all(not path.exists() for path in paths)


def test_delete_media_file_variantes_manquantes_ne_font_pas_echouer(tmp_path):
    root = tmp_path / "uploads"
    original = root / "images" / "photo.png"
    thumbnail = root / "images" / "thumbnail" / "photo.png"
    original.parent.mkdir(parents=True, exist_ok=True)
    thumbnail.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(b"image")
    thumbnail.write_bytes(b"image")

    result = delete_media_file("images/photo.png", root=root, variants=True)

    assert result == {
        "images/photo.png": True,
        "images/medium/photo.png": False,
        "images/thumbnail/photo.png": True,
    }


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "../secret.txt",
        "images/../../secret.txt",
        "https://example.com/photo.png",
        r"C:\Users\roger\photo.png",
    ],
)
def test_delete_media_file_refuse_chemins_dangereux(tmp_path, path):
    with pytest.raises(UploadStorageError):
        delete_media_file(path, root=tmp_path / "uploads")


def test_delete_media_file_refuse_dossier(tmp_path):
    root = tmp_path / "uploads"
    directory = root / "images" / "album"
    directory.mkdir(parents=True)

    with pytest.raises(UploadStorageError, match="n'est pas un fichier"):
        delete_media_file("images/album", root=root)


def test_delete_media_file_ne_supprime_pas_hors_uploads(tmp_path):
    root = tmp_path / "uploads"
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(UploadStorageError):
        delete_media_file(str(outside), root=root)
    assert outside.exists()


def test_delete_media_file_refuse_symlink_vers_hors_uploads(tmp_path):
    root = tmp_path / "uploads"
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "images" / "photo.png"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)

    with pytest.raises(UploadStorageError):
        delete_media_file("images/photo.png", root=root)
    assert outside.exists()


def test_delete_media_file_est_exporte_dans_api_publique():
    from forge_mvc_files import delete_media_file as exported_delete_media_file

    assert exported_delete_media_file is delete_media_file


def test_delete_upload_refuse_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(UploadStorageError):
        delete_upload(outside)


def test_get_upload_path_reste_dans_la_categorie(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    path = get_upload_path("doc.pdf", "documents")

    assert path == tmp_path / "uploads" / "documents" / "doc.pdf"


def test_upload_init_cree_dossiers_et_gitkeep(tmp_path):
    root = tmp_path / "storage" / "uploads"

    paths = init_upload_storage(root)

    assert root in paths
    for rel in ("", "images", "documents", "tmp"):
        assert (root / rel / ".gitkeep").exists()


def test_ensure_upload_dirs_refuse_categorie_invalide(tmp_path):
    with pytest.raises(UploadStorageError):
        ensure_upload_dirs(tmp_path, categories=("../bad",))


# ── Corrections main ────────────────────────────────────────────────────────

def test_save_upload_none_leve_storage_error(tmp_path, monkeypatch):
    _configure_uploads(
        monkeypatch,
        upload_root=tmp_path / "uploads",
        upload_max_size=100,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )
    with pytest.raises(UploadStorageError, match="Aucun fichier reçu"):
        save_upload(None, category="images")


def test_validate_mime_absent_avec_liste_non_vide_leve_erreur():
    with pytest.raises(UploadInvalidMimeTypeError, match="absent"):
        validate_upload_metadata(
            filename="photo.png",
            size=10,
            mime_type=None,
            allowed_extensions=["png"],
            allowed_mime_types=["image/png"],
            max_size=100,
        )


def test_validate_mime_absent_avec_liste_vide_est_accepte():
    extension = validate_upload_metadata(
        filename="photo.png",
        size=10,
        mime_type=None,
        allowed_extensions=["png"],
        allowed_mime_types=[],
        max_size=100,
    )
    assert extension == "png"


def test_upload_root_est_absolu(tmp_path, monkeypatch):
    # ADR-032 : upload_root est lu depuis l'environnement par l'opt-in files
    # (config.UPLOAD_ROOT n'existe plus). Le stockage résout toujours la racine
    # en chemin absolu : un chemin sauvegardé pointe sous une racine absolue.
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    from forge_mvc_files.manager import upload_root

    assert upload_root().resolve().is_absolute()


def test_get_upload_path_neutralise_traversal_dans_nom(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
    path = get_upload_path("../evil.pdf", "documents")
    assert path.name == "evil.pdf"
    assert str(path).startswith(str(tmp_path / "uploads"))
