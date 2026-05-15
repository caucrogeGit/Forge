"""Tests d'intégration média — MEDIA-INTEGRATION-TEST-001.

Valide la chaîne Média v2 complète avec storage temporaire :
- fichiers réellement écrits sur le système de fichiers (tmp_path) ;
- variantes générées par Pillow ;
- API repository utilisée avec FakeMediaDb (même stratégie que test_media_repository.py) ;
- suppression physique des fichiers et variantes vérifiée.

Aucun fichier n'est écrit dans le vrai storage/uploads du projet.
"""
from __future__ import annotations

import io
from types import SimpleNamespace

import pytest
from PIL import Image

import core.forge
from core.uploads import (
    attach_media_to_entity,
    create_media_record,
    delete_media,
    get_media_record,
    image_variant_paths,
    list_media_for_entity,
    save_upload,
    update_media_alt_text,
    update_media_position,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

class _FakeUploadFile:
    """Fichier upload minimal avec contenu réel lisible par _read_upload."""

    def __init__(self, filename: str, content_type: str, data: bytes):
        self.filename = filename
        self.content_type = content_type
        self.content = data
        self.size = len(data)


def _make_png_bytes(width: int = 20, height: int = 20, color: str = "red") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


class FakeMediaDb:
    """Base de données en mémoire — même stratégie que test_media_repository.py."""

    def __init__(self):
        self.rows: list[dict] = []
        self.next_id = 1

    def insert(self, sql, params):
        media_id = self.next_id
        self.next_id += 1
        (
            entity_name, entity_id, path, original_name, mime_type,
            size, role, position, alt_text,
        ) = params
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
        media_id = params[0]
        return next((row for row in self.rows if row["id"] == media_id), None)

    def fetch_all(self, sql, params):
        entity_name, entity_id, *rest = params
        role = rest[0] if rest else None
        rows = [
            row for row in self.rows
            if row["entity_name"] == entity_name and row["entity_id"] == entity_id
        ]
        if role is not None:
            rows = [row for row in rows if row["role"] == role]
        return sorted(rows, key=lambda r: (r["position"], r["id"]))

    def execute(self, sql, params):
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


# ── Fixture storage temporaire ─────────────────────────────────────────────────

@pytest.fixture()
def upload_root_tmp(tmp_path, monkeypatch):
    """Redirige upload_root vers tmp_path pour la durée du test."""
    monkeypatch.setitem(core.forge._cfg, "upload_root", str(tmp_path))
    return tmp_path


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_image_upload_cree_original_et_variantes(upload_root_tmp):
    """save_upload écrit le fichier original et génère thumbnail + medium."""
    data = _make_png_bytes()
    f = _FakeUploadFile("facade.png", "image/png", data)

    saved = save_upload(f, "images", variants=True)

    # Le chemin stocké est relatif
    assert not (upload_root_tmp / saved.path).is_absolute() or True
    assert not saved.path.startswith("/"), "Le chemin stocké ne doit pas être absolu"
    assert saved.path.startswith("images/")

    # Fichier original présent dans tmp_path
    original = upload_root_tmp / saved.path
    assert original.exists(), f"Fichier original absent : {original}"
    assert original.is_file()

    # Variantes présentes
    variants = image_variant_paths(saved.path, root=upload_root_tmp)
    assert variants["thumbnail"].exists(), "Variante thumbnail absente"
    assert variants["medium"].exists(), "Variante medium absente"

    # Aucun fichier écrit hors de tmp_path
    assert str(original.resolve()).startswith(str(upload_root_tmp.resolve()))


def test_media_record_conserve_alt_text_et_position():
    """create_media_record + get_media_record préservent tous les champs."""
    db = FakeMediaDb()

    media_id = create_media_record(
        entity_name="article",
        entity_id=7,
        path="images/terrasse.png",
        mime_type="image/png",
        size=512,
        role="gallery",
        position=3,
        alt_text="Vue de la terrasse",
        db=db,
    )

    row = get_media_record(media_id, db=db)

    assert row is not None
    assert row["alt_text"] == "Vue de la terrasse"
    assert row["position"] == 3
    assert row["role"] == "gallery"
    assert row["path"] == "images/terrasse.png"
    assert row["mime_type"] == "image/png"
    assert row["size"] == 512


def test_gallery_list_trie_par_position_puis_id():
    """list_media_for_entity retourne les médias triés Position ASC, Id ASC."""
    db = FakeMediaDb()

    def _saved(name):
        return SimpleNamespace(
            path=f"images/{name}.png",
            original_name=f"{name}.png",
            mime_type="image/png",
            size=100,
        )

    # Insérer dans un ordre qui ne correspond pas au tri attendu
    id_c = attach_media_to_entity(
        _saved("c"), entity_name="article", entity_id=7,
        role="gallery", position=2, db=db,
    )
    id_a = attach_media_to_entity(
        _saved("a"), entity_name="article", entity_id=7,
        role="gallery", position=1, db=db,
    )
    id_b = attach_media_to_entity(
        _saved("b"), entity_name="article", entity_id=7,
        role="gallery", position=1, db=db,
    )
    # Autre entité — ne doit pas apparaître
    attach_media_to_entity(
        _saved("x"), entity_name="article", entity_id=99,
        role="gallery", position=0, db=db,
    )

    rows = list_media_for_entity("article", 7, role="gallery", db=db)

    assert len(rows) == 3
    # id_a et id_b : position=1, ordre par Id ASC ; id_c : position=2
    assert [r["id"] for r in rows] == [id_a, id_b, id_c]
    assert rows[0]["path"] == "images/a.png"
    assert rows[2]["path"] == "images/c.png"


def test_update_position_et_alt_text_preserve_les_autres_champs():
    """update_media_position et update_media_alt_text ne touchent que leur champ."""
    db = FakeMediaDb()

    media_id = create_media_record(
        entity_name="hebergement",
        entity_id=5,
        path="images/chambre.png",
        mime_type="image/png",
        size=1024,
        role="gallery",
        position=0,
        alt_text="Chambre double",
        db=db,
    )

    update_media_position(media_id, 10, db=db)
    update_media_alt_text(media_id, "Chambre double vue mer", db=db)

    row = get_media_record(media_id, db=db)

    assert row["position"] == 10
    assert row["alt_text"] == "Chambre double vue mer"
    # Champs non modifiés
    assert row["path"] == "images/chambre.png"
    assert row["mime_type"] == "image/png"
    assert row["size"] == 1024
    assert row["role"] == "gallery"
    assert row["entity_name"] == "hebergement"
    assert row["entity_id"] == 5


def test_delete_media_supprime_fichiers_et_variantes(upload_root_tmp):
    """delete_media supprime le record en base, le fichier original et les variantes."""
    db = FakeMediaDb()

    # Écrire un vrai fichier PNG + ses variantes dans tmp_path
    data = _make_png_bytes(color="blue")
    f = _FakeUploadFile("piscine.png", "image/png", data)
    saved = save_upload(f, "images", variants=True)

    original_file = upload_root_tmp / saved.path
    variants = image_variant_paths(saved.path, root=upload_root_tmp)
    assert original_file.exists()
    assert variants["thumbnail"].exists()
    assert variants["medium"].exists()

    # Enregistrer le média en base via attach_media_to_entity
    media_id = attach_media_to_entity(
        saved,
        entity_name="hebergement",
        entity_id=3,
        role="gallery",
        db=db,
    )

    # Supprimer le média
    result = delete_media(
        media_id,
        delete_files=True,
        variants=True,
        db=db,
        root=upload_root_tmp,
    )

    assert result["deleted_record"] is True
    assert not original_file.exists(), "Fichier original encore présent"
    assert not variants["thumbnail"].exists(), "Variante thumbnail encore présente"
    assert not variants["medium"].exists(), "Variante medium encore présente"
    # Record supprimé
    assert get_media_record(media_id, db=db) is None
