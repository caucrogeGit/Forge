"""Tests — STARTERS-MIGRATE-003 : carnet-contacts en format canonique.

Vérifie que le starter carnet-contacts utilise le format JSON canonique
Forge (schema_version: "1.0") et que build:model passe sur un projet temporaire.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.starters.builder import build
from forge_cli.starters.registry import resolve

STARTER_DIR = Path("forge_cli/starters/data/carnet-contacts")
CONTACT_JSON = STARTER_DIR / "entities" / "contact.json"
VILLE_JSON = STARTER_DIR / "entities" / "ville.json"
RELATIONS_JSON = STARTER_DIR / "relations.json"
CONTACT_MODEL = STARTER_DIR / "files" / "mvc" / "models" / "contact_model.py"
VILLE_MODEL = STARTER_DIR / "files" / "mvc" / "models" / "ville_model.py"
CONTACT_CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "contact_controller.py"


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture()
def starter_project(tmp_path, monkeypatch):
    """Projet Forge minimal avec db_apply mockée."""
    root = tmp_path / "CarnetTest"
    root.mkdir()
    _write(root / "app.py", "# app")
    _write(root / "config.py", "APP_NAME = 'CarnetTest'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=CarnetTest\nAPP_ROUTES_MODULE=mvc.routes\n"
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


# ── Format canonique — contact.json ───────────────────────────────────────────


def test_contact_json_existe():
    assert CONTACT_JSON.exists()


def test_contact_json_schema_version():
    data = json.loads(CONTACT_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_contact_json_pas_de_format_version():
    assert "format_version" not in CONTACT_JSON.read_text(encoding="utf-8")


def test_contact_json_pas_de_sql_type():
    assert "sql_type" not in CONTACT_JSON.read_text(encoding="utf-8")


def test_contact_json_pas_de_primary_key():
    assert "primary_key" not in CONTACT_JSON.read_text(encoding="utf-8")


def test_contact_json_pas_de_column():
    data = json.loads(CONTACT_JSON.read_text(encoding="utf-8"))
    for field in data.get("fields", []):
        assert "column" not in field, f"Clé 'column' trouvée sur champ {field['name']}"


def test_contact_json_pas_id_dans_fields():
    data = json.loads(CONTACT_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


# ── Format canonique — ville.json ─────────────────────────────────────────────


def test_ville_json_existe():
    assert VILLE_JSON.exists()


def test_ville_json_schema_version():
    data = json.loads(VILLE_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_ville_json_pas_de_format_version():
    assert "format_version" not in VILLE_JSON.read_text(encoding="utf-8")


def test_ville_json_pas_de_sql_type():
    assert "sql_type" not in VILLE_JSON.read_text(encoding="utf-8")


def test_ville_json_pas_de_column():
    data = json.loads(VILLE_JSON.read_text(encoding="utf-8"))
    for field in data.get("fields", []):
        assert "column" not in field, f"Clé 'column' trouvée sur champ {field['name']}"


def test_ville_json_pas_id_dans_fields():
    data = json.loads(VILLE_JSON.read_text(encoding="utf-8"))
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
        assert "from" in rel, "Clé 'from' manquante dans la relation canonique"
        assert "to" in rel, "Clé 'to' manquante dans la relation canonique"


# ── Colonne ID canonique dans les modèles ─────────────────────────────────────


def test_contact_model_pas_contact_id():
    content = CONTACT_MODEL.read_text(encoding="utf-8")
    assert "ContactId" not in content


def test_ville_model_pas_ville_id_pk():
    content = VILLE_MODEL.read_text(encoding="utf-8")
    assert "VilleId" not in content
    assert "SELECT Id" in content


def test_contact_controller_pas_ville_id_comme_pk():
    content = CONTACT_CONTROLLER.read_text(encoding="utf-8")
    assert "ville[\"VilleId\"]" not in content
    assert "ville[\"Id\"]" in content


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
    for entity_name, src in [("contact", CONTACT_JSON), ("ville", VILLE_JSON)]:
        d = tmpdir / entity_name
        d.mkdir()
        shutil.copy(src, d / f"{entity_name}.json")

    results = collect_entity_validation_results(tmpdir)
    assert results is not None
    assert not results.get("errors"), f"entity:validate errors : {results['errors']}"


# ── Validation projet temporaire ──────────────────────────────────────────────


class TestCarnetContactsBuild:
    @pytest.fixture(autouse=True)
    def _build(self, starter_project):
        self.root = starter_project
        meta = resolve("3")
        build(meta, force=False)

    def test_entity_contact_json_canonique(self):
        path = self.root / "mvc" / "entities" / "contact" / "contact.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Contact"

    def test_entity_ville_json_canonique(self):
        path = self.root / "mvc" / "entities" / "ville" / "ville.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Ville"

    def test_relations_json_canonique(self):
        path = self.root / "mvc" / "entities" / "relations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert "relations" in data

    def test_contact_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact.sql").exists()

    def test_ville_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "ville" / "ville.sql").exists()

    def test_contact_model_copie(self):
        assert (self.root / "mvc" / "models" / "contact_model.py").exists()

    def test_ville_model_copie(self):
        assert (self.root / "mvc" / "models" / "ville_model.py").exists()

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
