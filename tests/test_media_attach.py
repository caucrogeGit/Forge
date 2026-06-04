from types import SimpleNamespace

import pytest
pytest.importorskip("forge_mvc_files")
pytest.importorskip("forge_mvc_images")

from forge_mvc_files import SavedUpload
from core.forms.upload_exceptions import UploadStorageError
from forge_mvc_images.media_gallery import get_cover_media, get_media_gallery
from forge_mvc_images.media_repository import attach_media_to_entity
from tests.test_media_repository import FakeMediaDb


def _saved_upload(path="images/photo.png"):
    return SavedUpload(
        filename="photo-uuid.png",
        original_name="photo.png",
        path=path,
        category="images",
        size=12345,
        mime_type="image/png",
        variants={
            "medium": "images/medium/photo-uuid.png",
            "thumbnail": "images/thumbnail/photo-uuid.png",
        },
    )


def test_attach_media_to_entity_attache_un_saved_upload_image():
    db = FakeMediaDb()
    saved = _saved_upload()

    media_id = attach_media_to_entity(
        saved,
        entity_name="hebergement",
        entity_id=12,
        role="gallery",
        position=1,
        alt_text="Vue exterieure",
        db=db,
    )

    assert media_id == 1
    assert db.rows[0]["entity_name"] == "hebergement"
    assert db.rows[0]["entity_id"] == 12


def test_attach_media_to_entity_enregistre_les_metadonnees_upload():
    db = FakeMediaDb()
    saved = _saved_upload()

    attach_media_to_entity(saved, entity_name="hebergement", entity_id=12, db=db)

    row = db.rows[0]
    assert row["path"] == saved.path
    assert row["original_name"] == saved.original_name
    assert row["mime_type"] == saved.mime_type
    assert row["size"] == saved.size


def test_attach_media_to_entity_enregistre_role_position_alt_text():
    db = FakeMediaDb()

    attach_media_to_entity(
        _saved_upload(),
        entity_name="hebergement",
        entity_id=12,
        role="cover",
        position=2,
        alt_text="Photo principale",
        db=db,
    )

    row = db.rows[0]
    assert row["role"] == "cover"
    assert row["position"] == 2
    assert row["alt_text"] == "Photo principale"


def test_attach_media_to_entity_retourne_id_cree():
    db = FakeMediaDb()

    first = attach_media_to_entity(_saved_upload("images/a.png"), entity_name="hebergement", entity_id=12, db=db)
    second = attach_media_to_entity(_saved_upload("images/b.png"), entity_name="hebergement", entity_id=12, db=db)

    assert first == 1
    assert second == 2


@pytest.mark.parametrize(
    "fake",
    [
        None,
        object(),
        SimpleNamespace(path="images/photo.png"),
    ],
)
def test_attach_media_to_entity_refuse_faux_objet(fake):
    with pytest.raises(TypeError, match="SavedUpload"):
        attach_media_to_entity(fake, entity_name="hebergement", entity_id=12, db=FakeMediaDb())


def test_attach_media_to_entity_refuse_entity_name_vide():
    with pytest.raises(ValueError, match="entity_name"):
        attach_media_to_entity(_saved_upload(), entity_name="", entity_id=12, db=FakeMediaDb())


def test_attach_media_to_entity_refuse_entity_id_invalide():
    with pytest.raises(ValueError, match="entity_id"):
        attach_media_to_entity(_saved_upload(), entity_name="hebergement", entity_id=0, db=FakeMediaDb())


def test_attach_media_to_entity_refuse_role_vide():
    with pytest.raises(ValueError, match="role"):
        attach_media_to_entity(_saved_upload(), entity_name="hebergement", entity_id=12, role="", db=FakeMediaDb())


def test_attach_media_to_entity_refuse_position_negative():
    with pytest.raises(ValueError, match="position"):
        attach_media_to_entity(_saved_upload(), entity_name="hebergement", entity_id=12, position=-1, db=FakeMediaDb())


def test_attach_media_to_entity_refuse_path_dangereux():
    with pytest.raises(UploadStorageError):
        attach_media_to_entity(_saved_upload("../secret.png"), entity_name="hebergement", entity_id=12, db=FakeMediaDb())


def test_attach_media_to_entity_ne_modifie_pas_les_variantes():
    db = FakeMediaDb()
    saved = _saved_upload()
    before = dict(saved.variants)

    attach_media_to_entity(saved, entity_name="hebergement", entity_id=12, db=db)

    assert saved.variants == before
    assert all("medium" not in call[1].lower() for call in db.calls)
    assert all("thumbnail" not in call[1].lower() for call in db.calls)


def test_attach_media_to_entity_alimente_la_galerie():
    db = FakeMediaDb()
    attach_media_to_entity(
        _saved_upload(),
        entity_name="hebergement",
        entity_id=12,
        role="gallery",
        position=1,
        db=db,
    )

    gallery = get_media_gallery("hebergement", 12, db=db)

    assert gallery[0]["url"] == "/media/images/photo.png"
    assert gallery[0]["medium_url"] == "/media/images/medium/photo.png"


def test_attach_media_to_entity_alimente_le_cover():
    db = FakeMediaDb()
    attach_media_to_entity(
        _saved_upload("images/cover.png"),
        entity_name="hebergement",
        entity_id=12,
        role="cover",
        db=db,
    )

    cover = get_cover_media("hebergement", 12, db=db)

    assert cover["url"] == "/media/images/cover.png"


def test_attach_media_to_entity_est_exporte_dans_api_publique():
    from forge_mvc_images import attach_media_to_entity as pkg_attach
    assert pkg_attach is attach_media_to_entity
