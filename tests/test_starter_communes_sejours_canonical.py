"""Tests — STARTERS-MIGRATE-005 : communes-sejours en format canonique.

Vérifie que le starter communes-sejours utilise le format JSON canonique
Forge (schema_version: "1.0") pour ses 4 entités et ses 3 relations.
La section media de hebergement.json a été supprimée (Option B — hors schéma).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.starters.builder import build
from forge_cli.starters.registry import resolve

STARTER_DIR  = Path("forge_cli/starters/data/communes-sejours")
ENTITY_DIR   = STARTER_DIR / "files" / "mvc" / "entities"
COMMUNE_JSON      = ENTITY_DIR / "commune" / "commune.json"
PROP_JSON         = ENTITY_DIR / "proprietaire" / "proprietaire.json"
HEBERG_JSON       = ENTITY_DIR / "hebergement" / "hebergement.json"
DEMANDE_JSON      = ENTITY_DIR / "demande_sejour" / "demande_sejour.json"
RELATIONS_JSON    = ENTITY_DIR / "relations.json"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture()
def starter_project(tmp_path, monkeypatch):
    """Projet Forge minimal pour skeleton build."""
    root = tmp_path / "CommunesTest"
    root.mkdir()
    _write(root / "app.py", "# app")
    _write(root / "config.py", "APP_NAME = 'CommunesTest'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=CommunesTest\nAPP_ROUTES_MODULE=mvc.routes\n"
        "DB_NAME=test_db\nDB_APP_HOST=localhost\nDB_APP_PORT=3306\n"
        "DB_APP_LOGIN=test\nDB_APP_PWD=\n"
        "DB_ADMIN_HOST=localhost\nDB_ADMIN_PORT=3306\n"
        "DB_ADMIN_LOGIN=root\nDB_ADMIN_PWD=\n"
        "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n",
    )
    _write(root / "env" / "dev", "DB_NAME=test_db\n")
    (root / "mvc" / "controllers").mkdir(parents=True)
    (root / "mvc" / "views").mkdir(parents=True)
    (root / "mvc" / "entities").mkdir(parents=True)
    _write(
        root / "mvc" / "routes.py",
        "from core.http.router import Router\nrouter = Router()\n",
    )
    monkeypatch.setattr("forge_cli.entities.db_apply.apply_model_sql", lambda _root: [])
    monkeypatch.chdir(root)
    return root


# ── Format canonique — commune.json ───────────────────────────────────────────


def test_commune_json_existe():
    assert COMMUNE_JSON.exists()


def test_commune_json_schema_version():
    data = json.loads(COMMUNE_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_commune_json_pas_de_format_version():
    assert "format_version" not in COMMUNE_JSON.read_text(encoding="utf-8")


def test_commune_json_pas_de_sql_type():
    assert "sql_type" not in COMMUNE_JSON.read_text(encoding="utf-8")


def test_commune_json_pas_de_primary_key():
    assert "primary_key" not in COMMUNE_JSON.read_text(encoding="utf-8")


def test_commune_json_pas_id_dans_fields():
    data = json.loads(COMMUNE_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


# ── Format canonique — proprietaire.json ──────────────────────────────────────


def test_proprietaire_json_existe():
    assert PROP_JSON.exists()


def test_proprietaire_json_schema_version():
    data = json.loads(PROP_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_proprietaire_json_pas_de_format_version():
    assert "format_version" not in PROP_JSON.read_text(encoding="utf-8")


def test_proprietaire_json_pas_de_sql_type():
    assert "sql_type" not in PROP_JSON.read_text(encoding="utf-8")


def test_proprietaire_json_pas_de_primary_key():
    assert "primary_key" not in PROP_JSON.read_text(encoding="utf-8")


def test_proprietaire_json_pas_id_dans_fields():
    data = json.loads(PROP_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


# ── Format canonique — hebergement.json ──────────────────────────────────────


def test_hebergement_json_existe():
    assert HEBERG_JSON.exists()


def test_hebergement_json_schema_version():
    data = json.loads(HEBERG_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_hebergement_json_pas_de_format_version():
    assert "format_version" not in HEBERG_JSON.read_text(encoding="utf-8")


def test_hebergement_json_pas_de_sql_type():
    assert "sql_type" not in HEBERG_JSON.read_text(encoding="utf-8")


def test_hebergement_json_pas_de_primary_key():
    assert "primary_key" not in HEBERG_JSON.read_text(encoding="utf-8")


def test_hebergement_json_pas_id_dans_fields():
    data = json.loads(HEBERG_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


def test_hebergement_json_pas_de_media_hors_schema():
    data = json.loads(HEBERG_JSON.read_text(encoding="utf-8"))
    assert "media" not in data, "La clé racine 'media' ne doit plus être présente dans l'entité canonique"


# ── Format canonique — demande_sejour.json ────────────────────────────────────


def test_demande_sejour_json_existe():
    assert DEMANDE_JSON.exists()


def test_demande_sejour_json_schema_version():
    data = json.loads(DEMANDE_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_demande_sejour_json_pas_de_format_version():
    assert "format_version" not in DEMANDE_JSON.read_text(encoding="utf-8")


def test_demande_sejour_json_pas_de_sql_type():
    assert "sql_type" not in DEMANDE_JSON.read_text(encoding="utf-8")


def test_demande_sejour_json_pas_de_primary_key():
    assert "primary_key" not in DEMANDE_JSON.read_text(encoding="utf-8")


def test_demande_sejour_json_pas_id_dans_fields():
    data = json.loads(DEMANDE_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


# ── Format canonique — relations.json ─────────────────────────────────────────


def test_relations_json_existe():
    assert RELATIONS_JSON.exists()


def test_relations_json_schema_version():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_relations_json_pas_de_format_version():
    assert "format_version" not in RELATIONS_JSON.read_text(encoding="utf-8")


def test_relations_json_pas_de_from_entity():
    content = RELATIONS_JSON.read_text(encoding="utf-8")
    assert "from_entity" not in content
    assert "to_entity" not in content
    assert "foreign_key_name" not in content


def test_relations_json_utilise_from_to():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    for rel in data.get("relations", []):
        assert "from" in rel
        assert "to" in rel
        assert "foreign_key" in rel


def test_relations_json_on_delete_minuscules():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    for rel in data.get("relations", []):
        if "on_delete" in rel:
            assert rel["on_delete"] == rel["on_delete"].lower()


def test_relations_json_trois_relations():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    assert len(data.get("relations", [])) == 3


# ── Validation JSON Schema ─────────────────────────────────────────────────────


def test_entites_valides_json_schema():
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema non disponible")

    import shutil
    import tempfile

    from forge_cli.entities.entity_validate import collect_entity_validation_results

    tmpdir = Path(tempfile.mkdtemp())
    for entity_name, src in [
        ("commune", COMMUNE_JSON),
        ("proprietaire", PROP_JSON),
        ("hebergement", HEBERG_JSON),
        ("demande_sejour", DEMANDE_JSON),
    ]:
        d = tmpdir / entity_name
        d.mkdir()
        shutil.copy(src, d / f"{entity_name}.json")

    results = collect_entity_validation_results(tmpdir)
    assert results is not None
    assert not results.get("errors"), f"entity:validate errors : {results['errors']}"


# ── Validation projet temporaire (skeleton build) ─────────────────────────────


class TestCommunesSejoursBuild:
    @pytest.fixture(autouse=True)
    def _build(self, starter_project):
        self.root = starter_project
        meta = resolve("5")
        build(meta, force=False)

    def test_entity_commune_json_copie(self):
        path = self.root / "mvc" / "entities" / "commune" / "commune.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Commune"

    def test_entity_proprietaire_json_copie(self):
        path = self.root / "mvc" / "entities" / "proprietaire" / "proprietaire.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Proprietaire"

    def test_entity_hebergement_json_copie(self):
        path = self.root / "mvc" / "entities" / "hebergement" / "hebergement.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Hebergement"
        assert "media" not in data

    def test_entity_demande_sejour_json_copie(self):
        path = self.root / "mvc" / "entities" / "demande_sejour" / "demande_sejour.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "DemandeSejour"

    def test_relations_json_copie(self):
        path = self.root / "mvc" / "entities" / "relations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert len(data.get("relations", [])) == 3

    def test_controller_copie(self):
        assert (self.root / "mvc" / "controllers" / "communes_sejours_controller.py").exists()

    def test_entity_validate_sans_erreur(self):
        try:
            import jsonschema  # noqa: F401
        except ImportError:
            pytest.skip("jsonschema non disponible")

        from forge_cli.entities.entity_validate import collect_entity_validation_results

        entities_root = self.root / "mvc" / "entities"
        results = collect_entity_validation_results(entities_root)
        assert results is not None
        assert not results.get("errors"), f"entity:validate errors : {results['errors']}"
