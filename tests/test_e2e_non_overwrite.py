"""
Tests E2E-NON-OVERWRITE-001 — Préservation du code utilisateur lors des régénérations.

Contrat testé :
  - make:entity (re-run)  → SystemExit(1), aucun fichier touché
  - make:crud (re-run)    → tous les fichiers existants préservés (_write_if_new)
  - sync:entity           → écrase contact.sql et contact_base.py,
                            préserve contact.py (manuel)
  - routes.py, static/, fichiers hors génération → jamais touchés

Comportements ambigus / limites documentés en bas de fichier.
"""
from __future__ import annotations

import contextlib
import os
from pathlib import Path

import pytest

from cli.entities.make_crud import cmd_make_crud_main, make_crud
from cli.entities.make_entity import main as make_entity_main
from cli.entities.model import sync_entity
from cli.project.project_audit import run_project_audit
from cli.project.project_check import run_project_check

_FORGE_VERSION = "2.2.0"
_ENTITY_NAME   = "Contact"
_ENTITY_SNAKE  = "contact"
_ENTITIES_ROOT = Path("mvc") / "entities"   # relatif, utilisé par make_entity_main


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scaffold_minimal_project(root: Path) -> None:
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


@contextlib.contextmanager
def _in_dir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _build_project(tmp_path: Path) -> Path:
    """Scaffold + make:entity Contact --no-input + make:crud Contact."""
    root = tmp_path / "TestContact"
    root.mkdir()
    _scaffold_minimal_project(root)
    with _in_dir(root):
        make_entity_main([_ENTITY_NAME, "--no-input"])
        cmd_make_crud_main([_ENTITY_NAME])
    return root


def _entity_dir(root: Path) -> Path:
    return root / "mvc" / "entities" / _ENTITY_SNAKE


def _rerun_make_entity(root: Path) -> None:
    with _in_dir(root):
        with pytest.raises(SystemExit):
            make_entity_main([_ENTITY_NAME, "--no-input"])


def _rerun_make_crud(root: Path) -> None:
    make_crud(
        _ENTITY_NAME,
        entities_root=root / "mvc" / "entities",
        output_root=root,
    )


# ── Re-run de make:entity ─────────────────────────────────────────────────────

class TestMakeEntityRerun:
    """make:entity sur une entité existante : SystemExit(1), aucun fichier modifié."""

    def test_rerun_exits_when_entity_exists(self, tmp_path):
        root = _build_project(tmp_path)
        with _in_dir(root):
            with pytest.raises(SystemExit) as exc_info:
                make_entity_main([_ENTITY_NAME, "--no-input"])
        assert exc_info.value.code == 1

    def test_rerun_preserves_entity_json(self, tmp_path):
        root = _build_project(tmp_path)
        target = _entity_dir(root) / f"{_ENTITY_SNAKE}.json"
        original = target.read_text(encoding="utf-8")
        _rerun_make_entity(root)
        assert target.read_text(encoding="utf-8") == original

    def test_rerun_preserves_manual_entity_py(self, tmp_path):
        root = _build_project(tmp_path)
        manual = _entity_dir(root) / f"{_ENTITY_SNAKE}.py"
        marker = "# USER CUSTOM CODE - DO NOT REMOVE\n"
        manual.write_text(manual.read_text(encoding="utf-8") + marker, encoding="utf-8")
        _rerun_make_entity(root)
        assert marker in manual.read_text(encoding="utf-8")

    def test_rerun_preserves_base_py(self, tmp_path):
        root = _build_project(tmp_path)
        base = _entity_dir(root) / f"{_ENTITY_SNAKE}_base.py"
        original = base.read_text(encoding="utf-8")
        _rerun_make_entity(root)
        assert base.read_text(encoding="utf-8") == original


# ── sync:entity — régénération du modèle ─────────────────────────────────────

class TestSyncEntity:
    """sync:entity écrase sql + base.py, préserve le manuel."""

    def test_sync_overwrites_sql(self, tmp_path):
        root = _build_project(tmp_path)
        sql = _entity_dir(root) / f"{_ENTITY_SNAKE}.sql"
        sql.write_text("-- CONTENU ANCIEN\n", encoding="utf-8")
        sync_entity(root / "mvc" / "entities", _ENTITY_NAME)
        assert "CREATE TABLE" in sql.read_text(encoding="utf-8")
        assert "CONTENU ANCIEN" not in sql.read_text(encoding="utf-8")

    def test_sync_overwrites_base_py(self, tmp_path):
        root = _build_project(tmp_path)
        base = _entity_dir(root) / f"{_ENTITY_SNAKE}_base.py"
        marker = "# MARQUEUR ANCIENNE VERSION\n"
        base.write_text(marker, encoding="utf-8")
        sync_entity(root / "mvc" / "entities", _ENTITY_NAME)
        assert marker not in base.read_text(encoding="utf-8")
        assert f"class {_ENTITY_NAME}Base" in base.read_text(encoding="utf-8")

    def test_sync_preserves_manual_py(self, tmp_path):
        root = _build_project(tmp_path)
        manual = _entity_dir(root) / f"{_ENTITY_SNAKE}.py"
        marker = "# USER CUSTOM CODE - DO NOT REMOVE\n"
        manual.write_text(manual.read_text(encoding="utf-8") + marker, encoding="utf-8")
        sync_entity(root / "mvc" / "entities", _ENTITY_NAME)
        assert marker in manual.read_text(encoding="utf-8")


# ── Re-run de make:crud ───────────────────────────────────────────────────────

class TestMakeCrudRerun:
    """make:crud sur des fichiers existants : tous préservés (_write_if_new)."""

    def test_controller_with_user_code_preserved(self, tmp_path):
        root = _build_project(tmp_path)
        controller = root / "mvc" / "controllers" / f"{_ENTITY_SNAKE}_controller.py"
        marker = "# USER CUSTOM CONTROLLER CODE - DO NOT REMOVE\n"
        controller.write_text(controller.read_text(encoding="utf-8") + marker, encoding="utf-8")
        _rerun_make_crud(root)
        assert marker in controller.read_text(encoding="utf-8")

    def test_model_with_user_code_preserved(self, tmp_path):
        root = _build_project(tmp_path)
        model = root / "mvc" / "models" / f"{_ENTITY_SNAKE}_model.py"
        marker = "# USER CUSTOM MODEL CODE - DO NOT REMOVE\n"
        model.write_text(model.read_text(encoding="utf-8") + marker, encoding="utf-8")
        _rerun_make_crud(root)
        assert marker in model.read_text(encoding="utf-8")

    def test_view_index_with_user_code_preserved(self, tmp_path):
        root = _build_project(tmp_path)
        view = root / "mvc" / "views" / _ENTITY_SNAKE / "index.html"
        marker = "<!-- USER CUSTOM VIEW - DO NOT REMOVE -->"
        view.write_text(view.read_text(encoding="utf-8") + marker, encoding="utf-8")
        _rerun_make_crud(root)
        assert marker in view.read_text(encoding="utf-8")

    def test_view_form_with_user_code_preserved(self, tmp_path):
        root = _build_project(tmp_path)
        view = root / "mvc" / "views" / _ENTITY_SNAKE / "form.html"
        marker = "<!-- USER CUSTOM TEMPLATE BLOCK - DO NOT REMOVE -->"
        view.write_text(view.read_text(encoding="utf-8") + marker, encoding="utf-8")
        _rerun_make_crud(root)
        assert marker in view.read_text(encoding="utf-8")

# ── Fichiers hors périmètre de génération ─────────────────────────────────────

class TestFilesOutsideGeneration:
    """Routes, static/, fichiers libres : aucune commande Forge ne les touche."""

    def test_routes_py_preserved_after_crud_rerun(self, tmp_path):
        root = _build_project(tmp_path)
        routes = root / "mvc" / "routes" / "__init__.py"
        marker = "# USER CUSTOM ROUTE - DO NOT REMOVE\n"
        routes.write_text(routes.read_text(encoding="utf-8") + marker, encoding="utf-8")
        _rerun_make_crud(root)
        assert marker in routes.read_text(encoding="utf-8")

    def test_static_file_preserved(self, tmp_path):
        root = _build_project(tmp_path)
        css = root / "static" / "custom.css"
        content = "/* USER CUSTOM STATIC FILE - DO NOT REMOVE */\n"
        _write(css, content)
        _rerun_make_crud(root)
        _rerun_make_entity(root)
        assert css.exists()
        assert css.read_text(encoding="utf-8") == content

    def test_out_of_scope_file_preserved(self, tmp_path):
        root = _build_project(tmp_path)
        note = root / "notes-dev.md"
        content = "# Notes développeur\n"
        note.write_text(content, encoding="utf-8")
        _rerun_make_crud(root)
        _rerun_make_entity(root)
        assert note.exists()
        assert note.read_text(encoding="utf-8") == content

    def test_nested_doc_preserved(self, tmp_path):
        root = _build_project(tmp_path)
        doc = root / "docs" / "local-note.md"
        content = "# Note locale\n"
        _write(doc, content)
        _rerun_make_crud(root)
        assert doc.exists()
        assert doc.read_text(encoding="utf-8") == content


# ── project:check + project:audit après régénérations ─────────────────────────

class TestChecksAfterRegen:
    def test_project_check_no_failures_after_crud_rerun(self, tmp_path):
        root = _build_project(tmp_path)
        _rerun_make_crud(root)
        results = run_project_check(root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:check FAIL : {[r.detail for r in failures]}"

    def test_project_audit_no_failures_after_crud_rerun(self, tmp_path):
        root = _build_project(tmp_path)
        _rerun_make_crud(root)
        results = run_project_audit(root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:audit FAIL : {[r.detail for r in failures]}"

    def test_project_check_no_failures_after_sync_entity(self, tmp_path):
        root = _build_project(tmp_path)
        sync_entity(root / "mvc" / "entities", _ENTITY_NAME)
        results = run_project_check(root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:check FAIL après sync:entity : {[r.detail for r in failures]}"

    def test_project_audit_no_failures_after_sync_entity(self, tmp_path):
        root = _build_project(tmp_path)
        sync_entity(root / "mvc" / "entities", _ENTITY_NAME)
        results = run_project_audit(root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:audit FAIL après sync:entity : {[r.detail for r in failures]}"


# ── Comportements ambigus / Limites ───────────────────────────────────────────
#
# COMPORTEMENT DOCUMENTÉ — contact_base.py (mvc/entities/contact/contact_base.py)
#   sync:entity et build:model ÉCRASENT ce fichier sans confirmation.
#   C'est le comportement attendu : il s'agit d'un fichier généré à partir du JSON.
#   Ne pas ajouter de logique métier dans contact_base.py.
#   Utiliser contact.py (préservé) pour les extensions manuelles.
#
# COMPORTEMENT DOCUMENTÉ — contact.sql (mvc/entities/contact/contact.sql)
#   sync:entity et build:model ÉCRASENT ce fichier.
#   C'est le comportement attendu : il est régénéré depuis le JSON d'entité.
#
# LIMITE — make:crud templates CRUD
#   Les vues CRUD (index.html, show.html, form.html…) sont préservées lors d'un
#   re-run de make:crud si elles existent déjà (_write_if_new).
#   Mais elles ne sont PAS régénérées automatiquement quand l'entité change.
#   Si l'entité est modifiée, relancer make:crud ne met PAS à jour les vues.
#   → Il faut supprimer les fichiers manuellement pour forcer la régénération.
#   Cette limite sera adressée dans un ticket dédié (E2E-STARTER-001 ou ultérieur).
