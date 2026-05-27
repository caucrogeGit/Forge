"""
Tests E2E-STARTER-001 — Génération des starters Forge et contrôle DX.

Stratégie :
  - forge_cli.entities.db_apply.apply_model_sql est mockée (retourne [])
    pour éviter toute dépendance à MariaDB réelle.
  - Chaque test utilise un projet temporaire isolé.
  - Les builds sont rapides (< 0.05 s), fixtures function-scoped acceptables.

Starters testés :
  1  contact-simple    — CRUD simple, une entité
  3  carnet-contacts   — Application, plusieurs entités, relations
  Cas invalide         — starter introuvable
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.starters import cmd_starter_build, cmd_starter_list
from forge_cli.starters._exceptions import StarterBuildError
from forge_cli.starters.builder import build
from forge_cli.starters.registry import StarterNotFound, all_starters, resolve
from forge_cli.project_audit import run_project_audit
from forge_cli.project_check import run_project_check

_FORGE_VERSION = "2.2.0"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scaffold_minimal_project(root: Path) -> None:
    _write(root / "app.py",    "# app")
    _write(root / "config.py", "APP_NAME = 'TestStarter'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=TestStarter\nAPP_ROUTES_MODULE=mvc.routes\n"
        "DB_NAME=test_starter_db\nDB_APP_HOST=localhost\nDB_APP_PORT=3306\n"
        "DB_APP_LOGIN=test_app\nDB_APP_PWD=\n"
        "DB_ADMIN_HOST=localhost\nDB_ADMIN_PORT=3306\n"
        "DB_ADMIN_LOGIN=root\nDB_ADMIN_PWD=\n"
        "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n",
    )
    _write(root / "env" / "dev", "DB_NAME=test_starter_db\n")
    (root / "mvc" / "controllers").mkdir(parents=True)
    (root / "mvc" / "views").mkdir(parents=True)
    (root / "mvc" / "entities").mkdir(parents=True)
    _write(
        root / "mvc" / "routes.py",
        "from core.http.router import Router\nrouter = Router()\n",
    )


@pytest.fixture()
def starter_project(tmp_path, monkeypatch):
    """Projet minimal + db_apply mockée + chdir."""
    root = tmp_path / "StarterTest"
    root.mkdir()
    _scaffold_minimal_project(root)
    monkeypatch.setattr("forge_cli.entities.db_apply.apply_model_sql", lambda _root: [])
    monkeypatch.chdir(root)
    return root


def _build_starter(identifier: str) -> None:
    """Lance build() sur le starter résolu (cwd déjà positionné)."""
    meta = resolve(identifier)
    build(meta, force=False)


# ── Métadonnées des starters ──────────────────────────────────────────────────

class TestStarterRegistry:
    def test_huit_starters_disponibles(self):
        assert len(all_starters()) == 8

    def test_numeros_1_a_8(self):
        assert [s["number"] for s in all_starters()] == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_tous_available(self):
        assert all(s["status"] == "available" for s in all_starters())

    def test_starter_1_est_crud(self):
        assert resolve("1").get("kind", "crud") == "crud"

    def test_starter_3_est_application(self):
        assert resolve("3")["kind"] == "application"

    def test_starter_inconnu_leve_exception(self):
        with pytest.raises(StarterNotFound):
            resolve("99")


# ── starter:list ──────────────────────────────────────────────────────────────

class TestStarterList:
    def test_affiche_les_5_starters(self, capsys):
        cmd_starter_list()
        out = capsys.readouterr().out
        assert "1" in out
        assert "5" in out

    def test_affiche_noms(self, capsys):
        cmd_starter_list()
        out = capsys.readouterr().out
        assert "Contacts" in out
        assert "Carnet de contacts" in out

    def test_affiche_disponible(self, capsys):
        cmd_starter_list()
        out = capsys.readouterr().out
        assert "disponible" in out

    def test_starter_inconnu_exit_1(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            cmd_starter_build(["99"])
        assert exc_info.value.code == 1


# ── Starter 1 — contact-simple (CRUD) ────────────────────────────────────────

class TestStarter1Crud:
    @pytest.fixture(autouse=True)
    def _build(self, starter_project):
        self.root = starter_project
        _build_starter("1")

    def test_entity_dir_exists(self):
        assert (self.root / "mvc" / "entities" / "contact").is_dir()

    def test_entity_json_valid(self):
        path = self.root / "mvc" / "entities" / "contact" / "contact.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("name") == "Contact"
        assert data.get("schema_version") == "1.0"

    def test_entity_sql_exists(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact.sql").exists()

    def test_controller_exists(self):
        assert (self.root / "mvc" / "controllers" / "contact_controller.py").exists()

    def test_model_exists(self):
        assert (self.root / "mvc" / "models" / "contact_model.py").exists()

    def test_form_exists(self):
        assert (self.root / "mvc" / "forms" / "contact_form.py").exists()

    def test_views_exist(self):
        views = self.root / "mvc" / "views" / "contact"
        assert (views / "index.html").exists()
        assert (views / "show.html").exists()
        assert (views / "form.html").exists()

    def test_routes_injected(self):
        routes = (self.root / "mvc" / "routes.py").read_text(encoding="utf-8")
        assert "/contacts" in routes

    def test_project_check_no_failures(self):
        results = run_project_check(self.root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:check FAIL : {[r.detail for r in failures]}"

    def test_project_audit_no_failures(self):
        results = run_project_audit(self.root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:audit FAIL : {[r.detail for r in failures]}"


# ── Starter 3 — carnet-contacts (application, plusieurs entités) ──────────────

class TestStarter3Application:
    @pytest.fixture(autouse=True)
    def _build(self, starter_project):
        self.root = starter_project
        _build_starter("3")

    def test_entity_ville_dir_exists(self):
        assert (self.root / "mvc" / "entities" / "ville").is_dir()

    def test_entity_contact_dir_exists(self):
        assert (self.root / "mvc" / "entities" / "contact").is_dir()

    def test_entity_ville_json_valid(self):
        path = self.root / "mvc" / "entities" / "ville" / "ville.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("name") == "Ville"
        assert data.get("schema_version") == "1.0"

    def test_entity_contact_json_valid(self):
        path = self.root / "mvc" / "entities" / "contact" / "contact.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("name") == "Contact"
        assert data.get("schema_version") == "1.0"

    def test_relations_json_exists(self):
        assert (self.root / "mvc" / "entities" / "relations.json").exists()

    def test_relations_json_valid(self):
        path = self.root / "mvc" / "entities" / "relations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "relations" in data

    def test_ville_sql_exists(self):
        assert (self.root / "mvc" / "entities" / "ville" / "ville.sql").exists()

    def test_contact_sql_exists(self):
        assert (self.root / "mvc" / "entities" / "contact" / "contact.sql").exists()

    def test_controller_ville_exists(self):
        assert (self.root / "mvc" / "controllers" / "ville_controller.py").exists()

    def test_controller_contact_exists(self):
        assert (self.root / "mvc" / "controllers" / "contact_controller.py").exists()

    def test_model_ville_exists(self):
        assert (self.root / "mvc" / "models" / "ville_model.py").exists()

    def test_model_contact_exists(self):
        assert (self.root / "mvc" / "models" / "contact_model.py").exists()

    def test_views_contact_exist(self):
        views = self.root / "mvc" / "views" / "contact"
        assert (views / "index.html").exists()
        assert (views / "form.html").exists()
        assert (views / "show.html").exists()

    def test_views_ville_exist(self):
        assert (self.root / "mvc" / "views" / "ville" / "index.html").exists()

    def test_layout_exists(self):
        assert (self.root / "mvc" / "views" / "layouts" / "app.html").exists()

    def test_routes_injected(self):
        routes = (self.root / "mvc" / "routes.py").read_text(encoding="utf-8")
        assert "/villes" in routes or "/contacts" in routes

    def test_project_check_no_failures(self):
        results = run_project_check(self.root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:check FAIL : {[r.detail for r in failures]}"

    def test_project_audit_no_failures(self):
        results = run_project_audit(self.root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:audit FAIL : {[r.detail for r in failures]}"


# ── Cas invalide ──────────────────────────────────────────────────────────────

class TestStarterInvalid:
    def test_build_inconnu_exit_1(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            cmd_starter_build(["99"])
        assert exc_info.value.code == 1

    def test_build_inconnu_message_lisible(self, capsys):
        with pytest.raises(SystemExit):
            cmd_starter_build(["starter-inconnu"])
        out = capsys.readouterr().out
        assert out.strip() != ""

    def test_build_sans_projet_exit_1(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("forge_cli.entities.db_apply.apply_model_sql", lambda _: [])
        with pytest.raises((SystemExit, StarterBuildError)):
            meta = resolve("1")
            build(meta)

    def test_resolve_invalide_leve_starter_not_found(self):
        with pytest.raises(StarterNotFound):
            resolve("inconnu-xyz")
