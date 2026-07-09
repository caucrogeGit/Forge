"""Tests E2E — PIVOT-ADVANCED-005 : flux complet Pivot advanced.

Couvre la chaîne :
  relations.json canonique
  → make:pivot-crud (génération des fichiers)
  → PivotAdvancedService (cycle CRUD complet sur SQLite in-memory)

Aucune connexion MariaDB réelle, aucun démarrage de serveur HTTP.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_entities")
from forge_mvc_entities.make_pivot_crud import make_pivot_crud
from forge_mvc_entities import PivotAdvancedService, PivotRow


# ── Fixture relations.json canonique ──────────────────────────────────────────

_RELATIONS_JSON = {
    "schema_version": "1.0",
    "relations": [
        {
            "type": "many_to_many",
            "from": "Article",
            "to": "Tag",
            "name": "tags",
            "inverse_name": "articles",
            "pivot": {
                "table": "article_tag",
                "from_key": "article_id",
                "to_key": "tag_id",
                "id": True,
                "unique_pair": True,
                "fields": [
                    {"name": "position", "type": "integer", "nullable": True},
                    {"name": "note", "type": "string", "max_length": 120, "nullable": True},
                ],
            },
        }
    ],
}


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    """Projet Forge temporaire minimal avec relations.json."""
    rel_path = tmp_path / "mvc" / "entities" / "relations.json"
    rel_path.parent.mkdir(parents=True, exist_ok=True)
    rel_path.write_text(json.dumps(_RELATIONS_JSON), encoding="utf-8")
    return tmp_path


# ── SQLite in-memory helpers ──────────────────────────────────────────────────

@pytest.fixture()
def sqlite_service():
    """PivotAdvancedService branché sur une table article_tag SQLite in-memory."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE article_tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            position INTEGER,
            note TEXT,
            UNIQUE(article_id, tag_id)
        )
    """)
    conn.commit()

    def fetch_one(sql: str, params: tuple) -> dict | None:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetch_all(sql: str, params: tuple) -> list[dict]:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def execute(sql: str, params: tuple) -> int:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount

    def insert_fn(sql: str, params: tuple) -> int:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid

    svc = PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_fields=["position", "note"],
        fetch_one=fetch_one,
        fetch_all=fetch_all,
        execute=execute,
        insert_fn=insert_fn,
    )
    yield svc
    conn.close()


# ── E2E : validation du contrat relations.json ────────────────────────────────


def test_e2e_relations_json_canonique_accepte(project):
    rel_path = project / "mvc" / "entities" / "relations.json"
    data = json.loads(rel_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    rel = data["relations"][0]
    assert rel["type"] == "many_to_many"
    assert rel["from"] == "Article"
    assert rel["name"] == "tags"
    fields = rel["pivot"]["fields"]
    assert any(f["name"] == "position" for f in fields)
    assert any(f["name"] == "note" for f in fields)


# ── E2E : make:pivot-crud génère les fichiers ─────────────────────────────────


def test_e2e_make_pivot_crud_cree_les_trois_fichiers(project):
    result = make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
    )
    assert len(result.created) == 3
    paths = [p.name for p in result.created]
    assert "article_tags_pivot_controller.py" in paths
    assert "index.html" in paths
    assert "form.html" in paths


def test_e2e_controleur_genere_importe_pivot_advanced_service(project):
    make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
    )
    ctrl = project / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    text = ctrl.read_text(encoding="utf-8")
    assert "PivotAdvancedService" in text
    assert "from forge_mvc_entities import PivotAdvancedService" in text


def test_e2e_template_index_mentionne_champs_pivot(project):
    make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
    )
    index = project / "mvc" / "templates" / "pivot" / "article_tags" / "index.html"
    text = index.read_text(encoding="utf-8")
    assert "position" in text
    assert "note" in text


def test_e2e_template_form_mentionne_champs_pivot(project):
    make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
    )
    form = project / "mvc" / "templates" / "pivot" / "article_tags" / "form.html"
    text = form.read_text(encoding="utf-8")
    assert "position" in text
    assert "note" in text


# ── E2E : dry-run ─────────────────────────────────────────────────────────────


def test_e2e_dry_run_ne_cree_aucun_fichier(project):
    result = make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
        dry_run=True,
    )
    assert result.dry_run is True
    ctrl = project / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    assert not ctrl.exists()
    # Les fichiers sont listés dans created mais non écrits
    assert len(result.created) == 3


# ── E2E : non-écrasement ──────────────────────────────────────────────────────


def test_e2e_non_ecrasement(project):
    make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
    )
    ctrl = project / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    ctrl.write_text("# marqueur", encoding="utf-8")

    result = make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
    )
    assert ctrl in result.preserved
    assert ctrl.read_text(encoding="utf-8") == "# marqueur"


# ── E2E : cycle complet PivotAdvancedService ──────────────────────────────────


def test_e2e_attach_cree_association(sqlite_service):
    rid = sqlite_service.attach(1, 10, {"position": 1, "note": "Principal"})
    assert isinstance(rid, int)
    assert rid > 0


def test_e2e_get_retourne_association_creee(sqlite_service):
    sqlite_service.attach(1, 10, {"position": 1, "note": "Principal"})
    row = sqlite_service.get(1, 10)
    assert row is not None
    assert isinstance(row, PivotRow)
    assert row.source_id == 1
    assert row.target_id == 10
    assert row.pivot_data.get("position") == 1
    assert row.pivot_data.get("note") == "Principal"


def test_e2e_list_for_source_retourne_associations(sqlite_service):
    sqlite_service.attach(1, 10, {"position": 1, "note": "Principal"})
    sqlite_service.attach(1, 20, {"position": 2, "note": "Secondaire"})
    sqlite_service.attach(2, 10, {"position": 1, "note": "Autre article"})

    rows = sqlite_service.list_for_source(1)
    assert len(rows) == 2
    target_ids = {r.target_id for r in rows}
    assert 10 in target_ids
    assert 20 in target_ids


def test_e2e_update_modifie_attributs_pivot(sqlite_service):
    sqlite_service.attach(1, 10, {"position": 1, "note": "Avant"})
    sqlite_service.update(1, 10, {"note": "Après"})
    row = sqlite_service.get(1, 10)
    assert row is not None
    assert row.pivot_data.get("note") == "Après"


def test_e2e_detach_supprime_association(sqlite_service):
    sqlite_service.attach(1, 10, {"position": 1, "note": "test"})
    assert sqlite_service.get(1, 10) is not None

    sqlite_service.detach(1, 10)
    assert sqlite_service.get(1, 10) is None


def test_e2e_flux_complet(sqlite_service):
    """Cycle complet : attach → get → list → update → detach → get = None."""
    # attach
    sqlite_service.attach(1, 10, {"position": 1, "note": "Principal"})
    # get
    row = sqlite_service.get(1, 10)
    assert row is not None
    assert row.pivot_data.get("position") == 1
    # list
    rows = sqlite_service.list_for_source(1)
    assert len(rows) == 1
    # update
    sqlite_service.update(1, 10, {"position": 2, "note": "Mis à jour"})
    row = sqlite_service.get(1, 10)
    assert row.pivot_data.get("position") == 2
    assert row.pivot_data.get("note") == "Mis à jour"
    # detach
    sqlite_service.detach(1, 10)
    # post-detach
    assert sqlite_service.get(1, 10) is None
    assert sqlite_service.list_for_source(1) == []


# ── E2E : neutralité make:crud et schémas ────────────────────────────────────


def test_e2e_make_crud_non_appele(project):
    """make:pivot-crud ne modifie pas les fichiers CRUD standard."""
    make_pivot_crud(
        "Article", "tags",
        entities_root=project / "mvc" / "entities",
        output_root=project,
    )
    # Aucun fichier CRUD standard ne doit avoir été créé
    assert not (project / "mvc" / "controllers" / "article_controller.py").exists()
    assert not (project / "mvc" / "models" / "article.py").exists()


def test_e2e_schemas_json_non_modifies():
    schema = Path("cli") / "schemas" / "relations.schema.json"
    data = json.loads(schema.read_text(encoding="utf-8"))
    assert data.get("$id") == "https://forge-mvc.dev/schemas/relations.schema.json"
    # pivot.fields est validé par le schéma existant — pas de modification nécessaire
    assert "pivot" in str(data)
