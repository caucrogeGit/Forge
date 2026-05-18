"""Tests — STARTERS-MIGRATE-001 : contact-simple en format canonique.

Vérifie que le starter contact-simple utilise bien le format JSON canonique
Forge (schema_version: "1.0") et que build:model passe sur un projet temporaire.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.starters.builder import build
from forge_cli.starters.registry import resolve

STARTER_DIR = Path("forge_cli/starters/data/contact-simple")
CONTACT_JSON = STARTER_DIR / "contact.json"


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture()
def starter_project(tmp_path, monkeypatch):
    """Projet Forge minimal avec db_apply mockée."""
    root = tmp_path / "ContactTest"
    root.mkdir()
    _write(root / "app.py", "# app")
    _write(root / "config.py", "APP_NAME = 'ContactTest'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=ContactTest\nAPP_ROUTES_MODULE=mvc.routes\n"
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


# ── Format canonique du fichier source ────────────────────────────────────────


def test_contact_json_existe():
    assert CONTACT_JSON.exists()


def test_contact_json_schema_version():
    data = json.loads(CONTACT_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_contact_json_pas_de_format_version():
    data = json.loads(CONTACT_JSON.read_text(encoding="utf-8"))
    assert "format_version" not in data


def test_contact_json_pas_de_sql_type():
    content = CONTACT_JSON.read_text(encoding="utf-8")
    assert "sql_type" not in content


def test_contact_json_pas_de_python_type():
    content = CONTACT_JSON.read_text(encoding="utf-8")
    assert "python_type" not in content


def test_contact_json_pas_de_primary_key():
    content = CONTACT_JSON.read_text(encoding="utf-8")
    assert "primary_key" not in content


def test_contact_json_pas_de_auto_increment():
    content = CONTACT_JSON.read_text(encoding="utf-8")
    assert "auto_increment" not in content


def test_contact_json_pas_id_dans_fields():
    data = json.loads(CONTACT_JSON.read_text(encoding="utf-8"))
    field_names = [f["name"] for f in data.get("fields", [])]
    assert "id" not in field_names


def test_contact_json_name_contact():
    data = json.loads(CONTACT_JSON.read_text(encoding="utf-8"))
    assert data.get("name") == "Contact"


def test_contact_json_valide_json_schema():
    """Le fichier doit être validé sans erreur par entity:validate (via jsonschema)."""
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema non disponible")

    from forge_cli.entities.entity_validate import collect_entity_validation_results

    entities_root = CONTACT_JSON.parent.parent.parent.parent.parent / "mvc" / "entities"
    if not entities_root.exists():
        entities_root = STARTER_DIR.parent.parent.parent.parent / "mvc" / "entities"

    tmpdir = Path(pytest.importorskip("tempfile").mkdtemp())
    entity_dir = tmpdir / "contact"
    entity_dir.mkdir()
    import shutil
    shutil.copy(CONTACT_JSON, entity_dir / "contact.json")

    results = collect_entity_validation_results(tmpdir)
    assert results is not None
    errors = [e for e in results.get("errors", []) if "contact" in e.get("file", "").lower()]
    assert not errors, f"entity:validate errors : {errors}"


# ── Validation projet temporaire ──────────────────────────────────────────────


class TestContactSimpleBuild:
    @pytest.fixture(autouse=True)
    def _build(self, starter_project):
        self.root = starter_project
        meta = resolve("1")
        build(meta, force=False)

    def test_entity_json_existe(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact.json").exists()

    def test_entity_json_canonique(self):
        path = self.root / "mvc" / "entities" / "contact" / "contact.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Contact"

    def test_entity_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact.sql").exists()

    def test_entity_base_genere(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact_base.py").exists()

    def test_entity_validate_sans_erreur(self):
        """entity:validate doit passer sans erreur sur le projet généré."""
        try:
            import jsonschema  # noqa: F401
        except ImportError:
            pytest.skip("jsonschema non disponible")

        from forge_cli.entities.entity_validate import collect_entity_validation_results

        entities_root = self.root / "mvc" / "entities"
        results = collect_entity_validation_results(entities_root)
        assert results is not None
        assert not results.get("errors"), f"entity:validate errors : {results['errors']}"
