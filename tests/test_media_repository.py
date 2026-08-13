import pytest
pytest.importorskip("forge_mvc_files")
pytest.importorskip("forge_mvc_images")

from types import SimpleNamespace

from core.forms.upload_exceptions import UploadStorageError
from forge_mvc_files.storage import normalize_media_path
from forge_mvc_images.media_repository import (
    attach_media_to_entity,
    create_media_record,
    delete_media_record,
    get_media_record,
    list_media_for_entity,
    update_media_alt_text,
    update_media_position,
)
from forge_mvc_images import media_repository as _media_repository_module


class FakeMediaDb:
    def __init__(self):
        self.rows: list[dict] = []
        self.next_id = 1
        self.calls: list[tuple[str, str, tuple]] = []

    def insert(self, sql, params):
        self.calls.append(("insert", sql, params))
        media_id = self.next_id
        self.next_id += 1
        (entity_name, entity_id, path, original_name, mime_type, size, role, position, alt_text, created_at) = params
        self.rows.append({
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
        })
        return media_id

    def fetch_one(self, sql, params):
        self.calls.append(("fetch_one", sql, params))
        media_id = params[0]
        return next((row for row in self.rows if row["id"] == media_id), None)

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

    def execute(self, sql, params):
        self.calls.append(("execute", sql, params))
        if "UPDATE media SET Position" in sql:
            position, media_id = params
            for row in self.rows:
                if row["id"] == media_id:
                    row["position"] = position
                    return 1
            return 0
        if "UPDATE media SET AltText" in sql:
            alt_text, media_id = params
            for row in self.rows:
                if row["id"] == media_id:
                    row["alt_text"] = alt_text
                    return 1
            return 0
        media_id = params[0]
        before = len(self.rows)
        self.rows = [row for row in self.rows if row["id"] != media_id]
        return before - len(self.rows)


def test_create_media_record_insere_un_media():
    db = FakeMediaDb()

    media_id = create_media_record(
        entity_name="hebergement",
        entity_id=12,
        path="images/photo.png",
        original_name="photo.png",
        mime_type="image/png",
        size=123,
        role="gallery",
        position=1,
        alt_text="Facade",
        db=db,
    )

    assert media_id == 1
    assert db.rows[0]["path"] == "images/photo.png"
    assert db.rows[0]["role"] == "gallery"
    assert db.rows[0]["position"] == 1
    assert "INSERT INTO media" in db.calls[0][1]
    # L'horodatage est pose par Python et non par le moteur
    # (`IMAGES-MEDIA-TIMESTAMP-UTC-001`, ADR-081) : `CURRENT_TIMESTAMP`
    # rendait l'heure locale du serveur sur MariaDB, deux heures d'ecart
    # avec l'UTC employe partout ailleurs.
    assert "CURRENT_TIMESTAMP" not in db.calls[0][1]
    assert "?" in db.calls[0][1]


def test_create_media_record_normalise_le_path():
    db = FakeMediaDb()

    create_media_record(
        entity_name="article",
        entity_id=1,
        path="storage/uploads/images/photo.png",
        db=db,
    )

    assert db.rows[0]["path"] == "images/photo.png"
    assert db.rows[0]["original_name"] == "photo.png"


def test_create_media_record_refuse_path_dangereux():
    with pytest.raises(UploadStorageError):
        create_media_record(entity_name="article", entity_id=1, path="../secret.txt", db=FakeMediaDb())


def test_create_media_record_refuse_entity_name_vide():
    with pytest.raises(ValueError, match="entity_name"):
        create_media_record(entity_name="", entity_id=1, path="images/photo.png", db=FakeMediaDb())


@pytest.mark.parametrize("entity_id", [0, -1, "12"])
def test_create_media_record_refuse_entity_id_invalide(entity_id):
    with pytest.raises(ValueError, match="entity_id"):
        create_media_record(entity_name="article", entity_id=entity_id, path="images/photo.png", db=FakeMediaDb())


def test_create_media_record_applique_role_et_position_par_defaut():
    db = FakeMediaDb()

    create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)

    assert db.rows[0]["role"] == "default"
    assert db.rows[0]["position"] == 0
    assert db.rows[0]["mime_type"] == "application/octet-stream"
    assert db.rows[0]["size"] == 0


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"role": ""}, "role"),
        ({"position": -1}, "position"),
        ({"size": -1}, "size"),
    ],
)
def test_create_media_record_refuse_valeurs_invalides(kwargs, message):
    params = {"entity_name": "article", "entity_id": 1, "path": "images/photo.png", "db": FakeMediaDb()}
    params.update(kwargs)

    with pytest.raises(ValueError, match=message):
        create_media_record(**params)


def test_get_media_record_retourne_le_media():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)

    row = get_media_record(media_id, db=db)

    assert row["id"] == media_id
    assert row["path"] == "images/photo.png"
    assert "AS entity_name" in db.calls[-1][1]


def test_get_media_record_retourne_none_si_absent():
    assert get_media_record(99, db=FakeMediaDb()) is None


def test_list_media_for_entity_retourne_seulement_l_entite_demandee():
    db = FakeMediaDb()
    expected = create_media_record(entity_name="article", entity_id=1, path="images/a.png", db=db)
    create_media_record(entity_name="article", entity_id=2, path="images/b.png", db=db)
    create_media_record(entity_name="contact", entity_id=1, path="images/c.png", db=db)

    rows = list_media_for_entity("article", 1, db=db)

    assert [row["id"] for row in rows] == [expected]


def test_list_media_for_entity_filtre_par_role():
    db = FakeMediaDb()
    create_media_record(entity_name="article", entity_id=1, path="images/a.png", role="cover", db=db)
    gallery_id = create_media_record(entity_name="article", entity_id=1, path="images/b.png", role="gallery", db=db)

    rows = list_media_for_entity("article", 1, role="gallery", db=db)

    assert [row["id"] for row in rows] == [gallery_id]
    assert "Role = ?" in db.calls[-1][1]


def test_list_media_for_entity_trie_par_position_puis_id():
    db = FakeMediaDb()
    third = create_media_record(entity_name="article", entity_id=1, path="images/c.png", position=2, db=db)
    first = create_media_record(entity_name="article", entity_id=1, path="images/a.png", position=1, db=db)
    second = create_media_record(entity_name="article", entity_id=1, path="images/b.png", position=1, db=db)

    rows = list_media_for_entity("article", 1, db=db)

    assert [row["id"] for row in rows] == [first, second, third]
    assert "ORDER BY Position ASC, Id ASC" in db.calls[-1][1]


def test_delete_media_record_supprime_seulement_la_ligne_sql():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)

    deleted = delete_media_record(media_id, db=db)

    assert deleted is True
    assert db.rows == []
    assert db.calls[-1] == ("execute", "DELETE FROM media WHERE Id = ?", (media_id,))


def test_delete_media_record_retourne_false_si_absent():
    assert delete_media_record(99, db=FakeMediaDb()) is False


def test_repository_est_exporte_dans_api_publique():
    from forge_mvc_images import create_media_record as pkg_create_media_record
    assert pkg_create_media_record is create_media_record
    assert _media_repository_module.create_media_record is create_media_record


def test_normalisation_media_existante_reste_valide():
    assert normalize_media_path("storage/uploads/images/photo.jpg") == "images/photo.jpg"


# ── Tests alt_text ────────────────────────────────────────────────────────────

def test_create_media_record_sans_alt_text_stocke_none():
    db = FakeMediaDb()
    create_media_record(entity_name="article", entity_id=1, path="images/photo.png", db=db)
    assert db.rows[0]["alt_text"] is None


def test_create_media_record_avec_alt_text_conserve_valeur():
    db = FakeMediaDb()
    create_media_record(
        entity_name="article", entity_id=1, path="images/photo.png",
        alt_text="Façade principale", db=db,
    )
    assert db.rows[0]["alt_text"] == "Façade principale"


def test_get_media_record_contient_alt_text():
    db = FakeMediaDb()
    media_id = create_media_record(
        entity_name="article", entity_id=1, path="images/photo.png",
        alt_text="Vue de face", db=db,
    )
    row = get_media_record(media_id, db=db)
    assert row["alt_text"] == "Vue de face"


def test_list_media_for_entity_contient_alt_text():
    db = FakeMediaDb()
    create_media_record(
        entity_name="article", entity_id=1, path="images/a.png",
        alt_text="Premier média", db=db,
    )
    create_media_record(
        entity_name="article", entity_id=1, path="images/b.png",
        db=db,
    )
    rows = list_media_for_entity("article", 1, db=db)
    assert rows[0]["alt_text"] == "Premier média"
    assert rows[1]["alt_text"] is None


def test_attach_media_to_entity_transmet_alt_text():
    db = FakeMediaDb()
    saved = SimpleNamespace(
        path="images/cover.png",
        original_name="cover.png",
        mime_type="image/png",
        size=512,
    )
    attach_media_to_entity(
        saved, entity_name="article", entity_id=5,
        role="cover", alt_text="Image de couverture", db=db,
    )
    assert db.rows[0]["alt_text"] == "Image de couverture"


# ── Tests position ────────────────────────────────────────────────────────────

def test_attach_media_to_entity_sans_position_stocke_zero():
    db = FakeMediaDb()
    saved = SimpleNamespace(path="images/a.png", original_name="a.png", mime_type="image/png", size=10)
    attach_media_to_entity(saved, entity_name="article", entity_id=1, role="gallery", db=db)
    assert db.rows[0]["position"] == 0


def test_attach_media_to_entity_avec_position_conserve_valeur():
    db = FakeMediaDb()
    saved = SimpleNamespace(path="images/b.png", original_name="b.png", mime_type="image/png", size=10)
    attach_media_to_entity(saved, entity_name="article", entity_id=1, role="gallery", position=5, db=db)
    assert db.rows[0]["position"] == 5


def test_attach_media_to_entity_position_none_vaut_zero():
    db = FakeMediaDb()
    saved = SimpleNamespace(path="images/c.png", original_name="c.png", mime_type="image/png", size=10)
    attach_media_to_entity(saved, entity_name="article", entity_id=1, role="gallery", position=None, db=db)
    assert db.rows[0]["position"] == 0


# ── Tests update_media_position ───────────────────────────────────────────────

def test_update_media_position_met_a_jour_la_position():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/a.png", position=0, db=db)
    update_media_position(media_id, 10, db=db)
    assert db.rows[0]["position"] == 10


def test_update_media_position_accepte_position_zero():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/a.png", position=5, db=db)
    update_media_position(media_id, 0, db=db)
    assert db.rows[0]["position"] == 0


def test_update_media_position_conserve_entier():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/a.png", db=db)
    update_media_position(media_id, 42, db=db)
    assert db.rows[0]["position"] == 42


def test_update_media_position_ne_modifie_pas_les_autres_champs():
    db = FakeMediaDb()
    media_id = create_media_record(
        entity_name="article", entity_id=1, path="images/a.png",
        mime_type="image/png", size=100, role="gallery", db=db,
    )
    update_media_position(media_id, 20, db=db)
    row = db.rows[0]
    assert row["path"] == "images/a.png"
    assert row["mime_type"] == "image/png"
    assert row["size"] == 100
    assert row["role"] == "gallery"
    assert row["position"] == 20


def test_list_media_trie_par_position_apres_update():
    db = FakeMediaDb()
    id_a = create_media_record(entity_name="article", entity_id=1, path="images/a.png", position=0, db=db)
    id_b = create_media_record(entity_name="article", entity_id=1, path="images/b.png", position=0, db=db)
    update_media_position(id_a, 10, db=db)
    update_media_position(id_b, 5, db=db)
    rows = list_media_for_entity("article", 1, db=db)
    assert [r["id"] for r in rows] == [id_b, id_a]


# ── Tests update_media_alt_text ───────────────────────────────────────────────

def test_update_media_alt_text_met_a_jour_le_texte():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/a.png", db=db)
    update_media_alt_text(media_id, "Vue de face", db=db)
    assert db.rows[0]["alt_text"] == "Vue de face"


def test_update_media_alt_text_chaine_vide_devient_none():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/a.png",
                                   alt_text="ancien", db=db)
    update_media_alt_text(media_id, "", db=db)
    assert db.rows[0]["alt_text"] is None


def test_update_media_alt_text_none_accepte():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/a.png",
                                   alt_text="ancien", db=db)
    update_media_alt_text(media_id, None, db=db)
    assert db.rows[0]["alt_text"] is None


def test_update_media_alt_text_trop_long_leve_erreur():
    db = FakeMediaDb()
    media_id = create_media_record(entity_name="article", entity_id=1, path="images/a.png", db=db)
    with pytest.raises(ValueError, match="255"):
        update_media_alt_text(media_id, "x" * 256, db=db)


def test_update_media_alt_text_ne_modifie_pas_les_autres_champs():
    db = FakeMediaDb()
    media_id = create_media_record(
        entity_name="article", entity_id=1, path="images/a.png",
        mime_type="image/png", size=200, role="gallery", position=3, db=db,
    )
    update_media_alt_text(media_id, "Nouvelle description", db=db)
    row = db.rows[0]
    assert row["path"] == "images/a.png"
    assert row["size"] == 200
    assert row["role"] == "gallery"
    assert row["position"] == 3
    assert row["alt_text"] == "Nouvelle description"
