import pytest
pytest.importorskip("forge_mvc_media")

from core.uploads import delete_media_file
from core.uploads.exceptions import UploadStorageError
from forge_mvc_media.media_repository import (
    attach_media_to_entity,
    create_media_record,
    delete_media,
    delete_media_record,
)
from tests.test_media_attach import _saved_upload
from tests.test_media_repository import FakeMediaDb


def _write_media_files(root, filename="photo.png", *, medium=True, thumbnail=True):
    original = root / "images" / filename
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(b"original")
    if medium:
        medium_path = root / "images" / "medium" / filename
        medium_path.parent.mkdir(parents=True, exist_ok=True)
        medium_path.write_bytes(b"medium")
    if thumbnail:
        thumbnail_path = root / "images" / "thumbnail" / filename
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        thumbnail_path.write_bytes(b"thumbnail")
    return original


def test_delete_media_sans_delete_files_supprime_seulement_ligne_sql(tmp_path):
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)
    original = _write_media_files(tmp_path / "uploads")

    result = delete_media(media_id, delete_files=False, db=db, root=tmp_path / "uploads")

    assert result == {
        "deleted_record": True,
        "deleted_files": {},
    }
    assert db.rows == []
    assert original.exists()


def test_delete_media_delete_files_true_variants_false_supprime_original_seulement(tmp_path):
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)
    root = tmp_path / "uploads"
    _write_media_files(root)

    result = delete_media(media_id, delete_files=True, variants=False, db=db, root=root)

    assert result == {
        "deleted_record": True,
        "deleted_files": {"images/photo.png": True},
    }
    assert not (root / "images" / "photo.png").exists()
    assert (root / "images" / "medium" / "photo.png").exists()
    assert (root / "images" / "thumbnail" / "photo.png").exists()


def test_delete_media_delete_files_true_variants_true_supprime_original_et_variantes(tmp_path):
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)
    root = tmp_path / "uploads"
    _write_media_files(root)

    result = delete_media(media_id, delete_files=True, variants=True, db=db, root=root)

    assert result == {
        "deleted_record": True,
        "deleted_files": {
            "images/photo.png": True,
            "images/medium/photo.png": True,
            "images/thumbnail/photo.png": True,
        },
    }
    assert not (root / "images" / "photo.png").exists()
    assert not (root / "images" / "medium" / "photo.png").exists()
    assert not (root / "images" / "thumbnail" / "photo.png").exists()


def test_delete_media_absent_retourne_false():
    result = delete_media(99, db=FakeMediaDb())

    assert result == {
        "deleted_record": False,
        "deleted_files": {},
    }


def test_delete_media_variante_absente_ne_fait_pas_echouer(tmp_path):
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)
    root = tmp_path / "uploads"
    _write_media_files(root, medium=False, thumbnail=True)

    result = delete_media(media_id, delete_files=True, variants=True, db=db, root=root)

    assert result["deleted_record"] is True
    assert result["deleted_files"] == {
        "images/photo.png": True,
        "images/medium/photo.png": False,
        "images/thumbnail/photo.png": True,
    }


@pytest.mark.parametrize("media_id", [0, -1, "1"])
def test_delete_media_refuse_media_id_invalide(media_id):
    with pytest.raises(ValueError, match="media_id"):
        delete_media(media_id, db=FakeMediaDb())


def test_delete_media_path_dangereux_refuse_sans_supprimer_ligne(tmp_path):
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)
    db.rows[0]["path"] = "../secret.png"

    with pytest.raises(UploadStorageError):
        delete_media(media_id, delete_files=True, db=db, root=tmp_path / "uploads")

    assert db.rows[0]["id"] == media_id


def test_delete_media_record_non_regression():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)

    assert delete_media_record(media_id, db=db) is True
    assert delete_media_record(media_id, db=db) is False


def test_delete_media_file_non_regression(tmp_path):
    root = tmp_path / "uploads"
    _write_media_files(root, medium=False, thumbnail=False)

    assert delete_media_file("images/photo.png", root=root) == {"images/photo.png": True}
    assert delete_media_file("images/photo.png", root=root) == {"images/photo.png": False}


def test_attach_media_to_entity_non_regression():
    db = FakeMediaDb()

    media_id = attach_media_to_entity(_saved_upload(), entity_name="article", entity_id=1, db=db)

    assert media_id == 1
    assert db.rows[0]["path"] == "images/photo.png"


def test_delete_media_est_exporte_dans_api_publique():
    from forge_mvc_media import delete_media as pkg_delete_media
    assert pkg_delete_media is delete_media
