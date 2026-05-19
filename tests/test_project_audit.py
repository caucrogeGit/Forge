"""Tests unitaires pour forge_cli.project_audit — forge project:audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.project_audit import (
    AuditResult,
    audit_project_config,
    audit_project_docs,
    audit_project_entities,
    audit_project_migrations,
    audit_project_modules,
    audit_project_routes,
    audit_project_structure,
    audit_project_templates,
    audit_project_tests,
    has_failures,
    run_project_audit,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _minimal_project(root: Path) -> None:
    """Projet Forge minimal valide pour l'audit."""
    _write(root / "app.py", "# app")
    _write(root / "config.py", "APP_NAME = 'Test'\n")
    _write(root / "env" / "example",
           "APP_NAME=Test\nAPP_ROUTES_MODULE=mvc.routes\n"
           "DB_NAME=test\nDB_APP_HOST=localhost\nDB_APP_PORT=3306\n"
           "DB_APP_LOGIN=u\nDB_APP_PWD=\n"
           "DB_ADMIN_HOST=localhost\nDB_ADMIN_PORT=3306\n"
           "DB_ADMIN_LOGIN=root\nDB_ADMIN_PWD=\n"
           "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n")
    _write(root / "env" / "dev", "DB_NAME=test\n")
    mvc = root / "mvc"
    (mvc / "controllers").mkdir(parents=True)
    (mvc / "views").mkdir(parents=True)
    (mvc / "entities").mkdir(parents=True)
    _write(mvc / "routes.py", "from core.http.router import Router\nrouter = Router()\n")
    _write(mvc / "entities" / "relations.json",
           json.dumps({"schema_version": "1.0", "relations": []}))
    _write(mvc / "views" / "base.html", "<html></html>")


def _add_entity(root: Path, name: str, with_sql: bool = True, with_base: bool = True) -> None:
    """Ajoute une entité complète au projet."""
    entity_dir = root / "mvc" / "entities" / name
    entity_dir.mkdir(parents=True, exist_ok=True)
    entity_data = {
        "entity": name.capitalize(), "table": name.lower(),
        "primary_key": {"name": "id", "sql": "Id", "python_type": "int",
                        "sql_type": "INT", "auto_increment": True},
        "fields": [],
    }
    _write(entity_dir / f"{name}.json", json.dumps(entity_data))
    if with_sql:
        _write(entity_dir / f"{name}.sql", f"CREATE TABLE {name} (id INT);")
    if with_base:
        _write(entity_dir / f"{name}_base.py", f"class {name.capitalize()}Base: pass")


# ── audit_project_structure ───────────────────────────────────────────────────

def test_audit_structure_ok(tmp_path):
    _minimal_project(tmp_path)
    results = audit_project_structure(tmp_path)
    fails = [r for r in results if r.status == "fail"]
    assert not fails


def test_audit_structure_app_py_absent(tmp_path):
    _minimal_project(tmp_path)
    (tmp_path / "app.py").unlink()
    results = audit_project_structure(tmp_path)
    assert any(r.status == "fail" and "app.py" in r.detail for r in results)


def test_audit_structure_config_py_absent(tmp_path):
    _minimal_project(tmp_path)
    (tmp_path / "config.py").unlink()
    results = audit_project_structure(tmp_path)
    assert any(r.status == "fail" and "config.py" in r.detail for r in results)


def test_audit_structure_mvc_absent(tmp_path):
    _write(tmp_path / "app.py", "")
    _write(tmp_path / "config.py", "")
    results = audit_project_structure(tmp_path)
    assert any(r.status == "fail" and "mvc/" in r.detail for r in results)


def test_audit_structure_dossier_vide(tmp_path):
    _minimal_project(tmp_path)
    # controllers/ vide (pas de fichiers)
    results = audit_project_structure(tmp_path)
    assert any(r.status == "warn" and "vide" in r.detail for r in results)


def test_audit_structure_static_absent_est_info(tmp_path):
    _minimal_project(tmp_path)
    results = audit_project_structure(tmp_path)
    static_results = [r for r in results if "static" in r.detail]
    assert static_results
    assert all(r.status == "info" for r in static_results)


# ── audit_project_config ──────────────────────────────────────────────────────

def test_audit_config_ok(tmp_path):
    _minimal_project(tmp_path)
    results = audit_project_config(tmp_path)
    assert any(r.status == "ok" and "env/example" in r.detail for r in results)
    assert any(r.status == "ok" and "env/dev" in r.detail for r in results)


def test_audit_config_example_absent(tmp_path):
    results = audit_project_config(tmp_path)
    assert any(r.status == "fail" and "env/example" in r.detail for r in results)


def test_audit_config_dev_absent(tmp_path):
    _write(tmp_path / "env" / "example",
           "APP_NAME=Test\nAPP_ROUTES_MODULE=mvc.routes\n"
           "DB_NAME=test\nDB_APP_HOST=localhost\n")
    results = audit_project_config(tmp_path)
    assert any(r.status == "warn" and "env/dev" in r.detail for r in results)


# ── audit_project_entities ────────────────────────────────────────────────────

def test_audit_entities_dossier_absent(tmp_path):
    results = audit_project_entities(tmp_path)
    assert any(r.status == "fail" and "mvc/entities/" in r.detail for r in results)


def test_audit_entities_aucune_entite(tmp_path):
    _minimal_project(tmp_path)
    results = audit_project_entities(tmp_path)
    assert any(r.status == "info" and "aucune" in r.detail for r in results)


def test_audit_entities_ok(tmp_path):
    _minimal_project(tmp_path)
    _add_entity(tmp_path, "contact")
    results = audit_project_entities(tmp_path)
    fails = [r for r in results if r.status == "fail"]
    warns = [r for r in results if r.status == "warn"]
    assert not fails
    assert not warns


def test_audit_entities_json_invalide(tmp_path):
    _minimal_project(tmp_path)
    entity_dir = tmp_path / "mvc" / "entities" / "contact"
    entity_dir.mkdir()
    _write(entity_dir / "contact.json", "not json")
    results = audit_project_entities(tmp_path)
    assert any(r.status == "fail" and "contact.json" in r.detail for r in results)


def test_audit_entities_sans_sql(tmp_path):
    _minimal_project(tmp_path)
    _add_entity(tmp_path, "contact", with_sql=False)
    results = audit_project_entities(tmp_path)
    assert any(r.status == "warn" and "SQL" in r.detail for r in results)


def test_audit_entities_sans_base_py(tmp_path):
    _minimal_project(tmp_path)
    _add_entity(tmp_path, "contact", with_base=False)
    results = audit_project_entities(tmp_path)
    assert any(r.status == "warn" and "_base.py" in r.detail for r in results)


def test_audit_entities_relations_invalide(tmp_path):
    (tmp_path / "mvc" / "entities").mkdir(parents=True)
    _write(tmp_path / "mvc" / "entities" / "relations.json", "not json")
    results = audit_project_entities(tmp_path)
    assert any(r.status == "fail" and "relations.json" in r.detail for r in results)


# ── audit_project_routes ──────────────────────────────────────────────────────

def test_audit_routes_ok(tmp_path):
    _write(tmp_path / "mvc" / "routes.py",
           "from core.http.router import Router\nrouter = Router()\n")
    results = audit_project_routes(tmp_path)
    assert any(r.status == "ok" and "syntaxe" in r.detail for r in results)
    assert any(r.status == "ok" and "router" in r.detail for r in results)


def test_audit_routes_absent(tmp_path):
    results = audit_project_routes(tmp_path)
    assert any(r.status == "fail" and "absent" in r.detail for r in results)


def test_audit_routes_vide(tmp_path):
    _write(tmp_path / "mvc" / "routes.py", "   \n")
    results = audit_project_routes(tmp_path)
    assert any(r.status == "warn" and "vide" in r.detail for r in results)


def test_audit_routes_syntax_error(tmp_path):
    _write(tmp_path / "mvc" / "routes.py", "def f(\n")
    results = audit_project_routes(tmp_path)
    assert any(r.status == "fail" and "syntaxe" in r.detail for r in results)


def test_audit_routes_sans_router(tmp_path):
    _write(tmp_path / "mvc" / "routes.py", "x = 1\n")
    results = audit_project_routes(tmp_path)
    assert any(r.status == "warn" and "router" in r.detail for r in results)


# ── audit_project_templates ───────────────────────────────────────────────────

def test_audit_templates_ok(tmp_path):
    views = tmp_path / "mvc" / "views"
    views.mkdir(parents=True)
    _write(views / "base.html", "<html></html>")
    results = audit_project_templates(tmp_path)
    assert any(r.status == "ok" and "template" in r.detail for r in results)


def test_audit_templates_absent(tmp_path):
    results = audit_project_templates(tmp_path)
    assert any(r.status == "fail" and "absent" in r.detail for r in results)


def test_audit_templates_vide(tmp_path):
    (tmp_path / "mvc" / "views").mkdir(parents=True)
    results = audit_project_templates(tmp_path)
    assert any(r.status == "warn" and ".html" in r.detail for r in results)


def test_audit_templates_sans_base_html(tmp_path):
    views = tmp_path / "mvc" / "views"
    views.mkdir(parents=True)
    _write(views / "contact.html", "<div>contact</div>")
    results = audit_project_templates(tmp_path)
    assert any(r.status == "info" and "base.html" in r.detail for r in results)


# ── audit_project_modules ─────────────────────────────────────────────────────

def test_audit_modules_absent(tmp_path):
    results = audit_project_modules(tmp_path)
    assert any(r.status == "info" and "absent" in r.detail for r in results)


def test_audit_modules_json_invalide(tmp_path):
    _write(tmp_path / "forge_modules.json", "not json")
    results = audit_project_modules(tmp_path)
    assert any(r.status == "fail" and "invalide" in r.detail for r in results)


def test_audit_modules_source_absente(tmp_path):
    _write(tmp_path / "forge_modules.json", json.dumps({
        "installed": {"mon_module": {"name": "mon_module", "source": "modules/mon_module"}}
    }))
    results = audit_project_modules(tmp_path)
    assert any(r.status == "fail" and "mon_module" in r.detail for r in results)


def test_audit_modules_ok(tmp_path):
    (tmp_path / "modules" / "mon_module").mkdir(parents=True)
    _write(tmp_path / "forge_modules.json", json.dumps({
        "installed": {"mon_module": {"name": "mon_module", "source": "modules/mon_module"}}
    }))
    results = audit_project_modules(tmp_path)
    assert not any(r.status == "fail" for r in results)


# ── audit_project_migrations ──────────────────────────────────────────────────

def test_audit_migrations_absent(tmp_path):
    results = audit_project_migrations(tmp_path)
    assert any(r.status == "info" and "absent" in r.detail for r in results)


def test_audit_migrations_noms_invalides(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    _write(d / "migration_001.sql", "SELECT 1;")
    results = audit_project_migrations(tmp_path)
    assert any(r.status == "warn" and "non conforme" in r.detail for r in results)


def test_audit_migrations_fichiers_vides(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    _write(d / "20260101120000_init.sql", "")
    results = audit_project_migrations(tmp_path)
    assert any(r.status == "warn" and "vide" in r.detail for r in results)


def test_audit_migrations_ok(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    _write(d / "20260101120000_init.sql", "CREATE TABLE t (id INT);")
    results = audit_project_migrations(tmp_path)
    assert any(r.status == "ok" and "conforme" in r.detail for r in results)


def test_audit_migrations_timestamps_dupliques(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    _write(d / "20260101120000_init.sql", "SELECT 1;")
    _write(d / "20260101120000_init2.sql", "SELECT 2;")
    results = audit_project_migrations(tmp_path)
    assert any(r.status == "warn" and "dupliqué" in r.detail for r in results)


# ── audit_project_docs ────────────────────────────────────────────────────────

def test_audit_docs_readme_absent(tmp_path):
    results = audit_project_docs(tmp_path)
    assert any(r.status == "info" and "README" in r.detail for r in results)


def test_audit_docs_readme_present(tmp_path):
    _write(tmp_path / "README.md",
           "# Mon Projet\n\nCeci est la documentation du projet Forge de démonstration.\n")
    results = audit_project_docs(tmp_path)
    assert any(r.status == "ok" and "README" in r.detail for r in results)


def test_audit_docs_readme_tres_court(tmp_path):
    _write(tmp_path / "README.md", "# Mon Projet\n")
    results = audit_project_docs(tmp_path)
    assert any(r.status == "warn" and "court" in r.detail for r in results)


# ── audit_project_tests ───────────────────────────────────────────────────────

def test_audit_tests_absent(tmp_path):
    results = audit_project_tests(tmp_path)
    assert any(r.status == "info" and "absent" in r.detail for r in results)


def test_audit_tests_dossier_sans_fichiers(tmp_path):
    (tmp_path / "tests").mkdir()
    results = audit_project_tests(tmp_path)
    assert any(r.status == "warn" for r in results)


def test_audit_tests_present(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    _write(tests / "test_example.py", "def test_ok(): assert True")
    results = audit_project_tests(tmp_path)
    assert any(r.status == "info" and "test_*.py" in r.detail for r in results)


# ── run_project_audit ─────────────────────────────────────────────────────────

def test_run_project_audit_contient_toutes_familles(tmp_path):
    results = run_project_audit(tmp_path, "2.2.0")
    families = {r.family for r in results}
    assert "Structure" in families
    assert "Configuration" in families
    assert "Entités" in families
    assert "Routes" in families
    assert "Templates" in families
    assert "Modules" in families
    assert "Migrations" in families
    assert "Documentation" in families
    assert "Tests" in families


def test_run_project_audit_projet_minimal(tmp_path):
    _minimal_project(tmp_path)
    results = run_project_audit(tmp_path, "2.2.0")
    fails = [r for r in results if r.status == "fail"]
    assert not fails


def test_run_project_audit_ne_modifie_pas_fichiers(tmp_path):
    _minimal_project(tmp_path)
    routes = tmp_path / "mvc" / "routes.py"
    before = routes.read_text(encoding="utf-8")
    run_project_audit(tmp_path, "2.2.0")
    assert routes.read_text(encoding="utf-8") == before


# ── has_failures ──────────────────────────────────────────────────────────────

def test_has_failures_avec_fail():
    results = [AuditResult("ok", "A"), AuditResult("fail", "B", "pb")]
    assert has_failures(results) is True


def test_has_failures_sans_fail():
    results = [AuditResult("ok", "A"), AuditResult("warn", "B", "pb")]
    assert has_failures(results) is False


def test_has_failures_info_nest_pas_fail():
    results = [AuditResult("info", "A", "info")]
    assert has_failures(results) is False


# ── cmd_project_audit depuis forge.py ─────────────────────────────────────────

def test_cmd_project_audit_hors_projet(monkeypatch, tmp_path, capsys):
    import forge
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        forge.cmd_project_audit()
    assert exc_info.value.code != 0
    assert "Erreur :" in capsys.readouterr().err


def test_cmd_project_audit_hors_projet_conseil_forge_new(monkeypatch, tmp_path, capsys):
    import forge
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        forge.cmd_project_audit()
    assert "forge new" in capsys.readouterr().err


def test_cmd_project_audit_utilise_le_cwd(monkeypatch, tmp_path):
    import forge
    captured: dict = {}

    def fake_run(root, version):
        captured["root"] = root
        captured["version"] = version
        return []

    _minimal_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("forge_cli.project_audit.run_project_audit", fake_run)
    monkeypatch.setattr("forge_cli.project_audit.print_audit_report", lambda *_: None)
    monkeypatch.setattr("forge_cli.project_audit.has_failures", lambda _: False)

    forge.cmd_project_audit()

    assert captured["root"] == tmp_path
    assert captured["version"] == forge._FORGE_VERSION
