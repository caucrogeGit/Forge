"""
Tests E2E-CLI-001 — Cycle complet forge new → make:entity → make:crud → project:check → project:audit.

Simule forge new en créant la structure minimale directement (sans réseau, sans venv, sans MariaDB).
Appelle les fonctions CLI internes dans l'ordre habituel du développeur.

Entité : Contact (--no-input → id INT PK AUTO_INCREMENT uniquement).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cli.entities.make_crud import cmd_make_crud_main
from cli.entities.make_entity import main as make_entity_main
from cli.project.project_audit import run_project_audit
from cli.project.project_check import run_project_check

_FORGE_VERSION = "2.2.0"
_ENTITY_NAME   = "Contact"
_ENTITY_SNAKE  = "contact"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scaffold_minimal_project(root: Path) -> None:
    """Crée la structure minimale équivalente à ce que forge new produit."""
    _write(root / "app.py",    "# app")
    _write(root / "config.py", "APP_NAME = 'TestContact'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=TestContact\nAPP_ROUTES_MODULE=mvc.routes\n"
        "DB_NAME=test_contact_db\nDB_HOST=localhost\nDB_PORT=3306\n"
        "DB_APP_LOGIN=test_contact_app\nDB_APP_PWD=\n"
        "DB_ADMIN_LOGIN=root\nDB_ADMIN_PWD=\n"
        "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n",
    )
    _write(root / "env" / "dev", "DB_NAME=test_contact_db\n")
    (root / "mvc" / "controllers").mkdir(parents=True)
    (root / "mvc" / "views").mkdir(parents=True)
    (root / "mvc" / "entities").mkdir(parents=True)
    _write(
        root / "mvc" / "routes" / "__init__.py",
        "from core.http.router import Router\nrouter = Router()\n",
    )


@pytest.fixture(scope="module")
def built_project(tmp_path_factory):
    """
    Construit une fois par module un projet Forge complet :
    scaffold → make:entity Contact --no-input → make:crud Contact.
    """
    root = tmp_path_factory.mktemp("e2e_cli")
    _scaffold_minimal_project(root)

    old_cwd = os.getcwd()
    os.chdir(root)
    try:
        make_entity_main([_ENTITY_NAME, "--no-input"])
        cmd_make_crud_main([_ENTITY_NAME])
    finally:
        os.chdir(old_cwd)

    return root


# ── Structure du projet ───────────────────────────────────────────────────────

class TestProjectStructure:
    def test_app_py_exists(self, built_project):
        assert (built_project / "app.py").exists()

    def test_config_py_exists(self, built_project):
        assert (built_project / "config.py").exists()

    def test_mvc_dir_exists(self, built_project):
        assert (built_project / "mvc").is_dir()

    def test_routes_py_exists(self, built_project):
        assert (built_project / "mvc" / "routes" / "__init__.py").exists()


# ── Entité ────────────────────────────────────────────────────────────────────

class TestEntityCreated:
    @property
    def _dir(self):
        def _get(root: Path) -> Path:
            return root / "mvc" / "entities" / _ENTITY_SNAKE
        return _get

    def test_entity_dir_exists(self, built_project):
        assert self._dir(built_project).is_dir()

    def test_entity_json_exists(self, built_project):
        assert (self._dir(built_project) / f"{_ENTITY_SNAKE}.json").exists()

    def test_entity_json_valid_and_named(self, built_project):
        data = json.loads(
            (self._dir(built_project) / f"{_ENTITY_SNAKE}.json").read_text(encoding="utf-8")
        )
        assert data["name"] == _ENTITY_NAME

    def test_entity_sql_exists(self, built_project):
        assert (self._dir(built_project) / f"{_ENTITY_SNAKE}.sql").exists()

    def test_entity_sql_contains_create_table(self, built_project):
        sql = (self._dir(built_project) / f"{_ENTITY_SNAKE}.sql").read_text(encoding="utf-8")
        assert "CREATE TABLE" in sql

    def test_entity_base_py_exists(self, built_project):
        assert (self._dir(built_project) / f"{_ENTITY_SNAKE}_base.py").exists()

    def test_relations_json_exists(self, built_project):
        assert (built_project / "mvc" / "entities" / "relations.json").exists()


# ── CRUD ──────────────────────────────────────────────────────────────────────

class TestCrudGenerated:
    def test_controller_exists(self, built_project):
        assert (built_project / "mvc" / "controllers" / f"{_ENTITY_SNAKE}_controller.py").exists()

    def test_model_exists(self, built_project):
        assert (built_project / "mvc" / "models" / f"{_ENTITY_SNAKE}_model.py").exists()

    def test_form_exists(self, built_project):
        assert (built_project / "mvc" / "forms" / f"{_ENTITY_SNAKE}_form.py").exists()

    def test_view_index_exists(self, built_project):
        assert (built_project / "mvc" / "views" / _ENTITY_SNAKE / "index.html").exists()

    def test_view_show_exists(self, built_project):
        assert (built_project / "mvc" / "views" / _ENTITY_SNAKE / "show.html").exists()

    def test_view_form_exists(self, built_project):
        assert (built_project / "mvc" / "views" / _ENTITY_SNAKE / "form.html").exists()

    def test_view_table_partial_exists(self, built_project):
        assert (built_project / "mvc" / "views" / _ENTITY_SNAKE / "_table.html").exists()

    def test_view_pagination_partial_exists(self, built_project):
        assert (built_project / "mvc" / "views" / _ENTITY_SNAKE / "_pagination.html").exists()

    def test_layout_app_html_exists(self, built_project):
        assert (built_project / "mvc" / "views" / "layouts" / "app.html").exists()


# ── project:check ─────────────────────────────────────────────────────────────

class TestProjectCheck:
    def test_no_failures(self, built_project):
        results = run_project_check(built_project, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:check FAIL : {[r.detail for r in failures]}"

    def test_returns_results(self, built_project):
        results = run_project_check(built_project, _FORGE_VERSION)
        assert len(results) > 0


# ── project:audit ─────────────────────────────────────────────────────────────

class TestProjectAudit:
    def test_no_failures(self, built_project):
        results = run_project_audit(built_project, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:audit FAIL : {[r.detail for r in failures]}"

    def test_returns_results(self, built_project):
        results = run_project_audit(built_project, _FORGE_VERSION)
        assert len(results) > 0


# ── Isolation ─────────────────────────────────────────────────────────────────

class TestIsolation:
    def test_cwd_restored_after_fixture(self, built_project):
        assert Path.cwd() != built_project

    def test_project_in_temp_dir(self, built_project):
        assert "tmp" in str(built_project).lower() or "temp" in str(built_project).lower()

    def test_two_projects_independent(self, tmp_path_factory):
        root_a = tmp_path_factory.mktemp("e2e_iso_a")
        root_b = tmp_path_factory.mktemp("e2e_iso_b")
        _scaffold_minimal_project(root_a)
        _scaffold_minimal_project(root_b)
        assert root_a != root_b
        assert not (root_a / "mvc").samefile(root_b / "mvc")
