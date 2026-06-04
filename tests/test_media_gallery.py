import pytest
pytest.importorskip("forge_mvc_media")

from core.forms.upload_exceptions import UploadStorageError
from forge_mvc_media.media_gallery import get_cover_media, get_media_gallery, media_url


class FakeGalleryDb:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def fetch_all(self, sql, params):
        self.calls.append(("fetch_all", sql, params))
        entity_name, entity_id, *rest = params
        role = rest[0] if rest else None
        rows = [
            row for row in self.rows
            if row["entity_name"] == entity_name and row["entity_id"] == entity_id
        ]
        if role is not None:
            rows = [row for row in rows if row["role"] == role]
        return sorted(rows, key=lambda row: (row["position"], row["id"]))


def _media(
    media_id,
    *,
    entity_name="hebergement",
    entity_id=12,
    path="images/photo.png",
    role="gallery",
    position=1,
    alt_text="Vue exterieure",
    original_name="photo.png",
    mime_type="image/png",
    size=12345,
):
    return {
        "id": media_id,
        "entity_name": entity_name,
        "entity_id": entity_id,
        "path": path,
        "original_name": original_name,
        "mime_type": mime_type,
        "size": size,
        "role": role,
        "position": position,
        "alt_text": alt_text,
        "created_at": "2026-01-01 10:00:00",
    }


def test_media_url_retourne_url_media():
    assert media_url("images/photo.png") == "/media/images/photo.png"


def test_media_url_normalise_les_doubles_slashs():
    assert media_url("images//2026/photo.png") == "/media/images/2026/photo.png"


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "../secret.txt",
        "https://example.com/file.png",
    ],
)
def test_media_url_refuse_chemin_dangereux(path):
    with pytest.raises(UploadStorageError):
        media_url(path)


def test_get_media_gallery_retourne_role_gallery_par_defaut():
    db = FakeGalleryDb([
        _media(1, role="gallery"),
        _media(2, role="cover"),
    ])

    gallery = get_media_gallery("hebergement", 12, db=db)

    assert [item["id"] for item in gallery] == [1]
    assert db.calls[-1][2] == ("hebergement", 12, "gallery")


def test_get_media_gallery_accepte_role_personnalise():
    db = FakeGalleryDb([
        _media(1, role="gallery"),
        _media(2, role="cover"),
    ])

    gallery = get_media_gallery("hebergement", 12, role="cover", db=db)

    assert [item["id"] for item in gallery] == [2]
    assert db.calls[-1][2] == ("hebergement", 12, "cover")


def test_get_media_gallery_respecte_tri_repository():
    db = FakeGalleryDb([
        _media(3, position=2),
        _media(1, position=1),
        _media(2, position=1),
    ])

    gallery = get_media_gallery("hebergement", 12, db=db)

    assert [item["id"] for item in gallery] == [1, 2, 3]


def test_get_media_gallery_ajoute_urls_et_variantes_pour_image():
    db = FakeGalleryDb([_media(1, path="images/photo.png")])

    item = get_media_gallery("hebergement", 12, db=db)[0]

    assert item["path"] == "images/photo.png"
    assert item["url"] == "/media/images/photo.png"
    assert item["medium_path"] == "images/medium/photo.png"
    assert item["medium_url"] == "/media/images/medium/photo.png"
    assert item["thumbnail_path"] == "images/thumbnail/photo.png"
    assert item["thumbnail_url"] == "/media/images/thumbnail/photo.png"


def test_get_media_gallery_normalise_path_image():
    db = FakeGalleryDb([_media(1, path="storage/uploads/images/photo.png")])

    item = get_media_gallery("hebergement", 12, db=db)[0]

    assert item["path"] == "images/photo.png"
    assert item["url"] == "/media/images/photo.png"


def test_get_media_gallery_ne_cree_pas_de_variantes_pour_document():
    db = FakeGalleryDb([
        _media(
            1,
            path="documents/contrat.pdf",
            original_name="contrat.pdf",
            mime_type="application/pdf",
        )
    ])

    item = get_media_gallery("hebergement", 12, db=db)[0]

    assert item["path"] == "documents/contrat.pdf"
    assert item["url"] == "/media/documents/contrat.pdf"
    assert item["medium_path"] is None
    assert item["medium_url"] is None
    assert item["thumbnail_path"] is None
    assert item["thumbnail_url"] is None


def test_get_media_gallery_conserve_metadonnees():
    db = FakeGalleryDb([_media(1, alt_text="Vue exterieure", position=4, size=987)])

    item = get_media_gallery("hebergement", 12, db=db)[0]

    assert item["alt_text"] == "Vue exterieure"
    assert item["original_name"] == "photo.png"
    assert item["mime_type"] == "image/png"
    assert item["size"] == 987
    assert item["position"] == 4


def test_get_media_gallery_retourne_liste_vide_si_aucun_media():
    assert get_media_gallery("hebergement", 12, db=FakeGalleryDb()) == []


def test_get_media_gallery_refuse_role_vide():
    with pytest.raises(ValueError, match="role"):
        get_media_gallery("hebergement", 12, role="", db=FakeGalleryDb())


def test_get_media_gallery_refuse_entity_name_vide():
    with pytest.raises(ValueError, match="entity_name"):
        get_media_gallery("", 12, db=FakeGalleryDb())


def test_get_media_gallery_refuse_entity_id_invalide():
    with pytest.raises(ValueError, match="entity_id"):
        get_media_gallery("hebergement", 0, db=FakeGalleryDb())


def test_get_media_gallery_refuse_path_dangereux():
    db = FakeGalleryDb([_media(1, path="../secret.png")])

    with pytest.raises(UploadStorageError):
        get_media_gallery("hebergement", 12, db=db)


def test_media_gallery_est_exporte_dans_api_publique():
    from forge_mvc_media import get_cover_media as pkg_get_cover_media
    from forge_mvc_media import get_media_gallery as pkg_get_media_gallery
    from forge_mvc_media import media_url as pkg_media_url

    assert pkg_get_cover_media is get_cover_media
    assert pkg_get_media_gallery is get_media_gallery
    assert pkg_media_url is media_url


def test_get_cover_media_retourne_none_si_aucun_cover():
    db = FakeGalleryDb([_media(1, role="gallery")])

    assert get_cover_media("hebergement", 12, db=db) is None


def test_get_cover_media_retourne_media_role_cover():
    db = FakeGalleryDb([
        _media(1, role="gallery"),
        _media(2, role="cover", path="images/cover.png"),
    ])

    cover = get_cover_media("hebergement", 12, db=db)

    assert cover["id"] == 2
    assert cover["role"] == "cover"
    assert cover["path"] == "images/cover.png"
    assert db.calls[-1][2] == ("hebergement", 12, "cover")


def test_get_cover_media_respecte_tri_position_puis_id():
    db = FakeGalleryDb([
        _media(3, role="cover", position=2),
        _media(2, role="cover", position=1),
        _media(1, role="cover", position=1),
    ])

    cover = get_cover_media("hebergement", 12, db=db)

    assert cover["id"] == 1


def test_get_cover_media_ajoute_urls_et_variantes_pour_image():
    db = FakeGalleryDb([_media(1, role="cover", path="images/cover.png")])

    cover = get_cover_media("hebergement", 12, db=db)

    assert cover["url"] == "/media/images/cover.png"
    assert cover["medium_path"] == "images/medium/cover.png"
    assert cover["medium_url"] == "/media/images/medium/cover.png"
    assert cover["thumbnail_path"] == "images/thumbnail/cover.png"
    assert cover["thumbnail_url"] == "/media/images/thumbnail/cover.png"


def test_get_cover_media_conserve_metadonnees():
    db = FakeGalleryDb([
        _media(
            1,
            role="cover",
            alt_text="Photo principale",
            original_name="cover.png",
            mime_type="image/png",
            size=456,
            position=0,
        )
    ])

    cover = get_cover_media("hebergement", 12, db=db)

    assert cover["alt_text"] == "Photo principale"
    assert cover["original_name"] == "cover.png"
    assert cover["mime_type"] == "image/png"
    assert cover["size"] == 456
    assert cover["position"] == 0


def test_get_cover_media_document_non_image_sans_variantes():
    db = FakeGalleryDb([
        _media(
            1,
            role="cover",
            path="documents/contrat.pdf",
            original_name="contrat.pdf",
            mime_type="application/pdf",
        )
    ])

    cover = get_cover_media("hebergement", 12, db=db)

    assert cover["url"] == "/media/documents/contrat.pdf"
    assert cover["medium_url"] is None
    assert cover["thumbnail_url"] is None


def test_get_cover_media_sans_fallback_ne_retourne_pas_galerie():
    db = FakeGalleryDb([_media(1, role="gallery", path="images/gallery.png")])

    assert get_cover_media("hebergement", 12, fallback_to_gallery=False, db=db) is None


def test_get_cover_media_fallback_retourne_premiere_image_galerie():
    db = FakeGalleryDb([
        _media(1, role="gallery", path="documents/contrat.pdf", position=1, mime_type="application/pdf"),
        _media(2, role="gallery", path="images/gallery.png", position=2),
    ])

    cover = get_cover_media("hebergement", 12, fallback_to_gallery=True, db=db)

    assert cover["id"] == 2
    assert cover["role"] == "gallery"
    assert cover["url"] == "/media/images/gallery.png"


def test_get_cover_media_fallback_ignore_documents_non_image():
    db = FakeGalleryDb([
        _media(1, role="gallery", path="documents/a.pdf", mime_type="application/pdf"),
        _media(2, role="gallery", path="documents/b.pdf", mime_type="application/pdf"),
    ])

    assert get_cover_media("hebergement", 12, fallback_to_gallery=True, db=db) is None


def test_get_cover_media_accepte_role_personnalise():
    db = FakeGalleryDb([
        _media(1, role="cover"),
        _media(2, role="banner", path="images/banner.png"),
    ])

    cover = get_cover_media("hebergement", 12, role="banner", db=db)

    assert cover["id"] == 2
    assert cover["role"] == "banner"
    assert db.calls[-1][2] == ("hebergement", 12, "banner")


def test_get_cover_media_refuse_entity_name_vide():
    with pytest.raises(ValueError, match="entity_name"):
        get_cover_media("", 12, db=FakeGalleryDb())


def test_get_cover_media_refuse_entity_id_invalide():
    with pytest.raises(ValueError, match="entity_id"):
        get_cover_media("hebergement", 0, db=FakeGalleryDb())


def test_get_cover_media_refuse_role_vide():
    with pytest.raises(ValueError, match="role"):
        get_cover_media("hebergement", 12, role="", db=FakeGalleryDb())


def test_get_cover_media_refuse_path_dangereux():
    db = FakeGalleryDb([_media(1, role="cover", path="../secret.png")])

    with pytest.raises(UploadStorageError):
        get_cover_media("hebergement", 12, db=db)
