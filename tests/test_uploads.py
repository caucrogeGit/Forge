from types import SimpleNamespace

import pytest

import core.forge as forge
from core.uploads.exceptions import (
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadStorageError,
    UploadTooLargeError,
)
from core.uploads.manager import delete_upload, get_upload_path, save_upload
from core.uploads.storage import ensure_upload_dirs, secure_filename
from core.uploads.validators import validate_upload_metadata
from forge_cli.uploads import init_upload_storage


def _file(filename="avatar.png", content=b"abc", content_type="image/png"):
    return SimpleNamespace(filename=filename, content=content, content_type=content_type)


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


def test_save_upload_ecrit_dans_la_categorie_configuree(tmp_path):
    forge.configure(
        upload_root=str(tmp_path / "uploads"),
        upload_max_size=100,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    saved = save_upload(_file(), category="images")

    assert saved.category == "images"
    assert saved.filename.endswith(".png")
    assert saved.size == 3
    assert (tmp_path / "uploads" / "images" / saved.filename).read_bytes() == b"abc"


def test_save_upload_evite_ecrasement(tmp_path):
    forge.configure(
        upload_root=str(tmp_path / "uploads"),
        upload_max_size=100,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )

    first = save_upload(_file(content=b"one"), category="images")
    second = save_upload(_file(content=b"two"), category="images")

    assert first.filename != second.filename


def test_delete_upload_supprime_sous_upload_root(tmp_path):
    forge.configure(
        upload_root=str(tmp_path / "uploads"),
        upload_max_size=100,
        upload_allowed_extensions=["png"],
        upload_allowed_mime_types=["image/png"],
    )
    saved = save_upload(_file(), category="images")

    assert delete_upload(saved.path) is True
    assert delete_upload(saved.path) is False


def test_delete_upload_refuse_path_traversal(tmp_path):
    forge.configure(upload_root=str(tmp_path / "uploads"))
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(UploadStorageError):
        delete_upload(outside)


def test_get_upload_path_reste_dans_la_categorie(tmp_path):
    forge.configure(upload_root=str(tmp_path / "uploads"))
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

def test_save_upload_none_leve_storage_error(tmp_path):
    forge.configure(
        upload_root=str(tmp_path / "uploads"),
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


def test_upload_root_est_absolu():
    import os
    import config
    assert os.path.isabs(config.UPLOAD_ROOT)


def test_get_upload_path_neutralise_traversal_dans_nom(tmp_path):
    forge.configure(upload_root=str(tmp_path / "uploads"))
    path = get_upload_path("../evil.pdf", "documents")
    assert path.name == "evil.pdf"
    assert str(path).startswith(str(tmp_path / "uploads"))
