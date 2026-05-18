"""Tests — STARTERS-MIGRATE-004 : suivi-comportement-eleves en format canonique.

Vérifie que le starter suivi-comportement-eleves utilise le format JSON canonique
Forge (schema_version: "1.0") et que build:model passe sur un projet temporaire.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.starters.builder import build
from forge_cli.starters.registry import resolve

STARTER_DIR = Path("forge_cli/starters/data/suivi-comportement-eleves")
COURS_JSON        = STARTER_DIR / "entities" / "cours.json"
ELEVE_JSON        = STARTER_DIR / "entities" / "eleve.json"
OBS_JSON          = STARTER_DIR / "entities" / "observation_cours.json"
UTILISATEUR_JSON  = STARTER_DIR / "entities" / "utilisateur.json"
RELATIONS_JSON    = STARTER_DIR / "relations.json"
AUTH_MODEL        = STARTER_DIR / "files" / "mvc" / "models" / "auth_model.py"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture()
def starter_project(tmp_path, monkeypatch):
    """Projet Forge minimal avec db_apply mockée."""
    root = tmp_path / "SuiviTest"
    root.mkdir()
    _write(root / "app.py", "# app")
    _write(root / "config.py", "APP_NAME = 'SuiviTest'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=SuiviTest\nAPP_ROUTES_MODULE=mvc.routes\n"
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


# ── Format canonique — cours.json ─────────────────────────────────────────────


def test_cours_json_existe():
    assert COURS_JSON.exists()


def test_cours_json_schema_version():
    data = json.loads(COURS_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_cours_json_pas_de_format_version():
    assert "format_version" not in COURS_JSON.read_text(encoding="utf-8")


def test_cours_json_pas_de_sql_type():
    assert "sql_type" not in COURS_JSON.read_text(encoding="utf-8")


def test_cours_json_pas_de_primary_key():
    assert "primary_key" not in COURS_JSON.read_text(encoding="utf-8")


def test_cours_json_pas_id_dans_fields():
    data = json.loads(COURS_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


# ── Format canonique — eleve.json ─────────────────────────────────────────────


def test_eleve_json_existe():
    assert ELEVE_JSON.exists()


def test_eleve_json_schema_version():
    data = json.loads(ELEVE_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_eleve_json_pas_de_format_version():
    assert "format_version" not in ELEVE_JSON.read_text(encoding="utf-8")


def test_eleve_json_pas_de_sql_type():
    assert "sql_type" not in ELEVE_JSON.read_text(encoding="utf-8")


def test_eleve_json_pas_de_primary_key():
    assert "primary_key" not in ELEVE_JSON.read_text(encoding="utf-8")


def test_eleve_json_pas_id_dans_fields():
    data = json.loads(ELEVE_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


# ── Format canonique — observation_cours.json ─────────────────────────────────


def test_observation_cours_json_existe():
    assert OBS_JSON.exists()


def test_observation_cours_json_schema_version():
    data = json.loads(OBS_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_observation_cours_json_pas_de_format_version():
    assert "format_version" not in OBS_JSON.read_text(encoding="utf-8")


def test_observation_cours_json_pas_de_sql_type():
    assert "sql_type" not in OBS_JSON.read_text(encoding="utf-8")


def test_observation_cours_json_pas_de_primary_key():
    assert "primary_key" not in OBS_JSON.read_text(encoding="utf-8")


def test_observation_cours_json_pas_id_dans_fields():
    data = json.loads(OBS_JSON.read_text(encoding="utf-8"))
    assert "id" not in [f["name"] for f in data.get("fields", [])]


# ── Format canonique — utilisateur.json ──────────────────────────────────────


def test_utilisateur_json_existe():
    assert UTILISATEUR_JSON.exists()


def test_utilisateur_json_schema_version():
    data = json.loads(UTILISATEUR_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_utilisateur_json_pas_de_format_version():
    assert "format_version" not in UTILISATEUR_JSON.read_text(encoding="utf-8")


def test_utilisateur_json_pas_de_sql_type():
    assert "sql_type" not in UTILISATEUR_JSON.read_text(encoding="utf-8")


def test_utilisateur_json_pas_de_primary_key():
    assert "primary_key" not in UTILISATEUR_JSON.read_text(encoding="utf-8")


def test_utilisateur_json_pas_utilisateur_id_dans_fields():
    data = json.loads(UTILISATEUR_JSON.read_text(encoding="utf-8"))
    field_names = [f["name"] for f in data.get("fields", [])]
    assert "id" not in field_names
    assert "utilisateur_id" not in field_names


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


def test_relations_json_deux_relations():
    data = json.loads(RELATIONS_JSON.read_text(encoding="utf-8"))
    assert len(data.get("relations", [])) == 2


# ── auth_model.py — PK canonique ─────────────────────────────────────────────


def test_auth_model_pas_utilisateur_id():
    content = AUTH_MODEL.read_text(encoding="utf-8")
    assert "UtilisateurId" not in content


def test_auth_model_utilise_id_canonique():
    content = AUTH_MODEL.read_text(encoding="utf-8")
    assert 'row["Id"]' in content


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
        ("cours", COURS_JSON),
        ("eleve", ELEVE_JSON),
        ("observation_cours", OBS_JSON),
        ("utilisateur", UTILISATEUR_JSON),
    ]:
        d = tmpdir / entity_name
        d.mkdir()
        shutil.copy(src, d / f"{entity_name}.json")

    results = collect_entity_validation_results(tmpdir)
    assert results is not None
    assert not results.get("errors"), f"entity:validate errors : {results['errors']}"


# ── Validation projet temporaire ──────────────────────────────────────────────


class TestSuiviComportementElevesBuild:
    @pytest.fixture(autouse=True)
    def _build(self, starter_project):
        self.root = starter_project
        meta = resolve("4")
        build(meta, force=False)

    def test_entity_cours_json_canonique(self):
        path = self.root / "mvc" / "entities" / "cours" / "cours.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Cours"

    def test_entity_eleve_json_canonique(self):
        path = self.root / "mvc" / "entities" / "eleve" / "eleve.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Eleve"

    def test_entity_observation_cours_json_canonique(self):
        path = self.root / "mvc" / "entities" / "observation_cours" / "observation_cours.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "ObservationCours"

    def test_entity_utilisateur_json_canonique(self):
        path = self.root / "mvc" / "entities" / "utilisateur" / "utilisateur.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert data.get("name") == "Utilisateur"

    def test_relations_json_canonique(self):
        path = self.root / "mvc" / "entities" / "relations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1.0"
        assert len(data.get("relations", [])) == 2

    def test_cours_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "cours" / "cours.sql").exists()

    def test_eleve_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "eleve" / "eleve.sql").exists()

    def test_observation_cours_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "observation_cours" / "observation_cours.sql").exists()

    def test_utilisateur_sql_genere(self):
        assert (self.root / "mvc" / "entities" / "utilisateur" / "utilisateur.sql").exists()

    def test_auth_model_copie(self):
        assert (self.root / "mvc" / "models" / "auth_model.py").exists()

    def test_eleve_model_copie(self):
        assert (self.root / "mvc" / "models" / "eleve_model.py").exists()

    def test_cours_model_copie(self):
        assert (self.root / "mvc" / "models" / "cours_model.py").exists()

    def test_observation_cours_model_copie(self):
        assert (self.root / "mvc" / "models" / "observation_cours_model.py").exists()

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
