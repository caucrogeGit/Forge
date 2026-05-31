"""Tests — STARTER-RENAME-FIRST-CRUD-GENERATED-001 : starter canonique.

Vérifie que le starter `first-crud-generated` utilise le format JSON
canonique Forge (schema_version: "1.0") sur une entité **neutre**
`Message`, et que build:model passe sur un projet temporaire. Le starter
est le pendant *généré* de `first-crud` (à la main), sans notion métier.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.starters.builder import build
from forge_cli.starters.registry import resolve

STARTER_DIR = Path("forge_cli/starters/data/first-crud-generated")
MESSAGE_JSON = STARTER_DIR / "message.json"


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture()
def starter_project(tmp_path, monkeypatch):
    """Projet Forge minimal avec db_apply mockée."""
    root = tmp_path / "MessageTest"
    root.mkdir()
    _write(root / "app.py", "# app")
    _write(root / "config.py", "APP_NAME = 'MessageTest'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=MessageTest\nAPP_ROUTES_MODULE=mvc.routes\n"
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


# ── Identité du starter ───────────────────────────────────────────────────────


def test_starter_id_canonique():
    meta = resolve("first-crud-generated")
    assert meta["id"] == "first-crud-generated"


def test_alias_numerique_1_resout_le_meme_starter():
    assert resolve("1")["id"] == "first-crud-generated"


def test_entity_neutre_message():
    assert resolve("first-crud-generated").get("entity") == "Message"


def test_aliases_neutres():
    aliases = resolve("first-crud-generated").get("aliases", [])
    assert "first-crud-generated" in aliases
    assert "first_crud_generated" in aliases
    assert "1" in aliases
    # aucun alias métier hérité de l'ancien starter Contacts.
    assert "contacts" not in aliases
    assert "contact-simple" not in aliases


def test_routes_prefix_messages():
    assert resolve("first-crud-generated").get("routes", {}).get("prefix") == "/messages"


def test_home_route_messages():
    assert resolve("first-crud-generated").get("home_route") == "/messages"


def test_doc_url_pointe_crud_generated():
    doc_url = resolve("first-crud-generated").get("doc_url", "")
    assert "crud/first-crud-generated" in doc_url


# ── Format canonique du fichier source (entité neutre) ────────────────────────


def test_message_json_existe():
    assert MESSAGE_JSON.exists()


def test_message_json_schema_version():
    data = json.loads(MESSAGE_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_message_json_pas_de_format_version():
    data = json.loads(MESSAGE_JSON.read_text(encoding="utf-8"))
    assert "format_version" not in data


def test_message_json_pas_de_sql_type():
    content = MESSAGE_JSON.read_text(encoding="utf-8")
    assert "sql_type" not in content


def test_message_json_pas_de_python_type():
    content = MESSAGE_JSON.read_text(encoding="utf-8")
    assert "python_type" not in content


def test_message_json_pas_de_primary_key():
    content = MESSAGE_JSON.read_text(encoding="utf-8")
    assert "primary_key" not in content


def test_message_json_pas_de_auto_increment():
    content = MESSAGE_JSON.read_text(encoding="utf-8")
    assert "auto_increment" not in content


def test_message_json_pas_id_dans_fields():
    data = json.loads(MESSAGE_JSON.read_text(encoding="utf-8"))
    field_names = [f["name"] for f in data.get("fields", [])]
    assert "id" not in field_names


def test_message_json_name_message():
    data = json.loads(MESSAGE_JSON.read_text(encoding="utf-8"))
    assert data.get("name") == "Message"


def test_message_json_entite_neutre():
    """L'entité ne porte aucun champ métier (nom/email/téléphone…)."""
    data = json.loads(MESSAGE_JSON.read_text(encoding="utf-8"))
    field_names = {f["name"] for f in data.get("fields", [])}
    assert field_names == {"content"}
    for metier in ("nom", "prenom", "email", "telephone"):
        assert metier not in field_names


def test_message_json_valide_json_schema():
    """Le fichier doit être validé sans erreur par entity:validate (via jsonschema)."""
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema non disponible")

    from forge_cli.entities.entity_validate import collect_entity_validation_results

    tmpdir = Path(pytest.importorskip("tempfile").mkdtemp())
    entity_dir = tmpdir / "message"
    entity_dir.mkdir()
    import shutil
    shutil.copy(MESSAGE_JSON, entity_dir / "message.json")

    results = collect_entity_validation_results(tmpdir)
    assert results is not None
    errors = [e for e in results.get("errors", []) if "message" in e.get("file", "").lower()]
    assert not errors, f"entity:validate errors : {errors}"


# ── Validation projet temporaire ──────────────────────────────────────────────


class TestFirstCrudGeneratedBuild:
    @pytest.fixture(autouse=True)
    def _build(self, starter_project):
        self.root = starter_project
        meta = resolve("1")
        build(meta, force=False)

    def test_entity_json_existe(self):
        assert (self.root / "mvc" / "entities" / "message" / "message.json").exists()

    def test_entity_json_canonique(self):
        path = self.root / "mvc" / "entities" / "message" / "message.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Message"

    def test_entity_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "message" / "message.sql").exists()

    def test_entity_base_genere(self):
        assert (self.root / "mvc" / "entities" / "message" / "message_base.py").exists()

    def test_routes_messages_injectees(self):
        routes = (self.root / "mvc" / "routes.py").read_text(encoding="utf-8")
        assert "/messages" in routes

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
