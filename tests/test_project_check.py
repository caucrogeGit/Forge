"""Tests unitaires pour cli.project_check — forge project:check."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.doctor import CheckResult
from cli.project_check import (
    check_project_config,
    check_project_entities,
    check_project_migrations,
    check_project_modules,
    check_project_routes,
    check_project_structure,
    check_project_templates,
    has_failures,
    run_project_check,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _minimal_project(root: Path) -> None:
    """Crée la structure minimale d'un projet Forge valide."""
    _write(root / "app.py",    "# app")
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


# ── check_project_structure ───────────────────────────────────────────────────

def test_check_project_structure_ok(tmp_path):
    _minimal_project(tmp_path)
    r = check_project_structure(tmp_path)
    assert r.status == "ok"


def test_check_project_structure_manque_app_py(tmp_path):
    _minimal_project(tmp_path)
    (tmp_path / "app.py").unlink()
    r = check_project_structure(tmp_path)
    assert r.status == "fail"
    assert "app.py" in r.detail


def test_check_project_structure_manque_config_py(tmp_path):
    _minimal_project(tmp_path)
    (tmp_path / "config.py").unlink()
    r = check_project_structure(tmp_path)
    assert r.status == "fail"
    assert "config.py" in r.detail


def test_check_project_structure_manque_mvc(tmp_path):
    _write(tmp_path / "app.py", "")
    _write(tmp_path / "config.py", "")
    r = check_project_structure(tmp_path)
    assert r.status == "fail"
    assert "mvc/" in r.detail


def test_check_project_structure_manque_routes(tmp_path):
    _minimal_project(tmp_path)
    (tmp_path / "mvc" / "routes.py").unlink()
    r = check_project_structure(tmp_path)
    assert r.status == "fail"
    assert "mvc/routes.py" in r.detail


def test_check_project_structure_hors_projet(tmp_path):
    """Un répertoire vide n'est pas un projet Forge."""
    r = check_project_structure(tmp_path)
    assert r.status == "fail"


# ── check_project_config ──────────────────────────────────────────────────────

def test_check_project_config_ok(tmp_path):
    _minimal_project(tmp_path)
    r = check_project_config(tmp_path)
    assert r.status == "ok"


def test_check_project_config_sans_example(tmp_path):
    r = check_project_config(tmp_path)
    assert r.status == "fail"
    assert "env/example" in r.detail


def test_check_project_config_sans_dev(tmp_path):
    _write(tmp_path / "env" / "example", "APP_NAME=Test\n")
    r = check_project_config(tmp_path)
    assert r.status == "warn"
    assert "env/dev" in r.detail


# ── check_project_entities ────────────────────────────────────────────────────

def test_check_project_entities_pas_de_dossier(tmp_path):
    r = check_project_entities(tmp_path)
    assert r.status == "fail"
    assert "mvc/entities/" in r.detail


def test_check_project_entities_nu_sans_relations(tmp_path):
    """Projet nu (ADR-024) : mvc/entities/ existe, aucune entité, pas de
    relations.json. Ce n'est pas une erreur, relations.json naît avec
    make:entity / make:relation."""
    (tmp_path / "mvc" / "entities").mkdir(parents=True)
    r = check_project_entities(tmp_path)
    assert r.status == "ok"
    assert "aucune" in r.detail


def test_check_project_entities_pas_de_relations_avec_entite(tmp_path):
    """En présence d'une entité, relations.json devient obligatoire."""
    d = tmp_path / "mvc" / "entities"
    (d / "contact").mkdir(parents=True)
    r = check_project_entities(tmp_path)
    assert r.status == "fail"
    assert "relations.json" in r.detail


def test_check_project_entities_relations_invalide(tmp_path):
    d = tmp_path / "mvc" / "entities"
    (d / "contact").mkdir(parents=True)
    _write(d / "relations.json", "not json")
    r = check_project_entities(tmp_path)
    assert r.status == "fail"
    assert "relations.json" in r.detail


def test_check_project_entities_vide(tmp_path):
    d = tmp_path / "mvc" / "entities"
    d.mkdir(parents=True)
    _write(d / "relations.json", json.dumps({"schema_version": "1.0", "relations": []}))
    r = check_project_entities(tmp_path)
    assert r.status == "ok"
    assert "aucune" in r.detail


def test_check_project_entities_json_absent(tmp_path):
    d = tmp_path / "mvc" / "entities"
    (d / "contact").mkdir(parents=True)
    _write(d / "relations.json", json.dumps({"schema_version": "1.0", "relations": []}))
    r = check_project_entities(tmp_path)
    assert r.status == "fail"
    assert "contact.json" in r.detail


def test_check_project_entities_json_invalide(tmp_path):
    d = tmp_path / "mvc" / "entities"
    (d / "contact").mkdir(parents=True)
    _write(d / "relations.json", json.dumps({"schema_version": "1.0", "relations": []}))
    _write(d / "contact" / "contact.json", "not json")
    r = check_project_entities(tmp_path)
    assert r.status == "fail"
    assert "contact.json" in r.detail


def test_check_project_entities_ok(tmp_path):
    d = tmp_path / "mvc" / "entities"
    (d / "contact").mkdir(parents=True)
    _write(d / "relations.json", json.dumps({"schema_version": "1.0", "relations": []}))
    _write(d / "contact" / "contact.json",
           json.dumps({"entity": "Contact", "table": "contact",
                       "primary_key": {"name": "id", "sql": "Id", "python_type": "int",
                                       "sql_type": "INT", "auto_increment": True},
                       "fields": []}))
    r = check_project_entities(tmp_path)
    assert r.status == "ok"
    assert "1" in r.detail


# ── check_project_routes ──────────────────────────────────────────────────────

def test_check_project_routes_absent(tmp_path):
    r = check_project_routes(tmp_path)
    assert r.status == "fail"
    assert "absent" in r.detail


def test_check_project_routes_vide(tmp_path):
    _write(tmp_path / "mvc" / "routes.py", "   \n")
    r = check_project_routes(tmp_path)
    assert r.status == "warn"
    assert "vide" in r.detail


def test_check_project_routes_syntax_error(tmp_path):
    _write(tmp_path / "mvc" / "routes.py", "def f(\n")
    r = check_project_routes(tmp_path)
    assert r.status == "fail"
    assert "syntaxe" in r.detail


def test_check_project_routes_ok(tmp_path):
    _write(tmp_path / "mvc" / "routes.py",
           "from core.http.router import Router\nrouter = Router()\n")
    r = check_project_routes(tmp_path)
    assert r.status == "ok"


class TestCheckProjectRoutesRealImport:
    """check_project_routes effectue un vrai import (PROJECT-CHECK-ROUTES-IMPORT-001).

    Avant ce ticket, la vérification ne faisait qu'un ast.parse, ce qui laissait
    passer des erreurs d'import (module manquant, attribut manquant). Ces tests
    vérifient que les nouveaux cas d'erreur sont bien détectés.
    """

    def test_routes_with_unimportable_module_fails(self, tmp_path):
        """Un mvc/routes.py qui importe un module inexistant doit faire échouer le check."""
        _write(tmp_path / "mvc" / "__init__.py", "")
        _write(tmp_path / "mvc" / "routes.py",
               "from un_module_qui_nexiste_pas import quelque_chose\n"
               "router = None\n")

        r = check_project_routes(tmp_path)
        assert r.status == "fail", f"Attendu 'fail', obtenu {r.status!r}"
        assert "impossible d'importer" in r.detail or "no module" in r.detail.lower()

    def test_routes_without_router_attribute_fails(self, tmp_path):
        """Un mvc/routes.py valide syntaxiquement mais sans `router` doit faire échouer."""
        _write(tmp_path / "mvc" / "__init__.py", "")
        _write(tmp_path / "mvc" / "routes.py",
               "from core.http.router import Router\n")

        r = check_project_routes(tmp_path)
        assert r.status == "fail"
        assert "router" in r.detail.lower()

    def test_routes_valid_returns_ok(self, tmp_path):
        """Un mvc/routes.py qui s'importe correctement renvoie OK."""
        _write(tmp_path / "mvc" / "__init__.py", "")
        _write(tmp_path / "mvc" / "routes.py",
               "from core.http.router import Router\n"
               "router = Router()\n")

        r = check_project_routes(tmp_path)
        assert r.status == "ok", f"Attendu 'ok', obtenu {r.status!r} — {r.detail}"

    def test_routes_with_syntax_error_still_caught_first(self, tmp_path):
        """Une SyntaxError doit être détectée avant la tentative d'import."""
        _write(tmp_path / "mvc" / "__init__.py", "")
        _write(tmp_path / "mvc" / "routes.py", "def bad(:\n    pass\n")

        r = check_project_routes(tmp_path)
        assert r.status == "fail"
        assert "syntaxe" in r.detail.lower()


# ── check_project_templates ───────────────────────────────────────────────────

def test_check_project_templates_absent(tmp_path):
    """Contrairement à doctor (skip), project:check retourne fail."""
    r = check_project_templates(tmp_path)
    assert r.status == "fail"
    assert "absent" in r.detail


def test_check_project_templates_vide(tmp_path):
    (tmp_path / "mvc" / "views").mkdir(parents=True)
    r = check_project_templates(tmp_path)
    assert r.status == "warn"
    assert ".html" in r.detail


def test_check_project_templates_ok(tmp_path):
    views = tmp_path / "mvc" / "views"
    views.mkdir(parents=True)
    _write(views / "base.html", "<html></html>")
    r = check_project_templates(tmp_path)
    assert r.status == "ok"
    assert "1" in r.detail


# ── check_project_modules ─────────────────────────────────────────────────────

def test_check_project_modules_absent(tmp_path):
    r = check_project_modules(tmp_path)
    assert r.status == "ok"
    assert "absent" in r.detail


def test_check_project_modules_json_invalide(tmp_path):
    _write(tmp_path / "forge_modules.json", "not json")
    r = check_project_modules(tmp_path)
    assert r.status == "fail"
    assert "invalide" in r.detail


def test_check_project_modules_installed_invalide(tmp_path):
    _write(tmp_path / "forge_modules.json", '{"installed": "bad"}')
    r = check_project_modules(tmp_path)
    assert r.status == "fail"
    assert "installed" in r.detail


def test_check_project_modules_source_absente_est_fail(tmp_path):
    """project:check est plus strict que doctor : source absente = FAIL (pas WARN)."""
    _write(tmp_path / "forge_modules.json", json.dumps({
        "installed": {"mon_module": {"name": "mon_module", "source": "modules/mon_module"}}
    }))
    r = check_project_modules(tmp_path)
    assert r.status == "fail"
    assert "mon_module" in r.detail


def test_check_project_modules_ok(tmp_path):
    (tmp_path / "modules" / "mon_module").mkdir(parents=True)
    _write(tmp_path / "forge_modules.json", json.dumps({
        "installed": {"mon_module": {"name": "mon_module", "source": "modules/mon_module"}}
    }))
    r = check_project_modules(tmp_path)
    assert r.status == "ok"


def test_check_project_modules_aucun_installe(tmp_path):
    _write(tmp_path / "forge_modules.json", '{"installed": {}}')
    r = check_project_modules(tmp_path)
    assert r.status == "ok"
    assert "aucun" in r.detail.lower()


# ── check_project_migrations ──────────────────────────────────────────────────

def test_check_project_migrations_absent(tmp_path):
    r = check_project_migrations(tmp_path)
    assert r.status == "ok"
    assert "absent" in r.detail


def test_check_project_migrations_noms_invalides(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    _write(d / "migration_001.sql", "SELECT 1;")
    r = check_project_migrations(tmp_path)
    assert r.status == "warn"
    assert "migration_001.sql" in r.detail


def test_check_project_migrations_fichiers_vides(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    _write(d / "20260101120000_init.sql", "")
    r = check_project_migrations(tmp_path)
    assert r.status == "warn"
    assert "vides" in r.detail


def test_check_project_migrations_ok(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    _write(d / "20260101120000_init.sql", "CREATE TABLE t (id INT);")
    r = check_project_migrations(tmp_path)
    assert r.status == "ok"


# ── run_project_check ─────────────────────────────────────────────────────────

def test_run_project_check_contient_toutes_familles(tmp_path):
    results = run_project_check(tmp_path, "test")
    labels = {r.label for r in results}
    assert "Structure" in labels
    assert "Configuration" in labels
    assert "Entités" in labels
    assert "Routes" in labels
    assert "Templates" in labels
    assert "Modules" in labels
    assert "Migrations" in labels


def test_run_project_check_projet_valide_sans_fail(tmp_path):
    _minimal_project(tmp_path)
    results = run_project_check(tmp_path, "test")
    assert not has_failures(results)


def test_run_project_check_hors_projet_retourne_fail(tmp_path):
    results = run_project_check(tmp_path, "test")
    assert has_failures(results)


def test_run_project_check_ne_modifie_pas_les_fichiers(tmp_path):
    _minimal_project(tmp_path)
    routes = tmp_path / "mvc" / "routes.py"
    before = routes.read_text(encoding="utf-8")
    run_project_check(tmp_path, "test")
    assert routes.read_text(encoding="utf-8") == before


# ── has_failures ──────────────────────────────────────────────────────────────

def test_has_failures_avec_fail():
    assert has_failures([CheckResult("ok", "A"), CheckResult("fail", "B")]) is True


def test_has_failures_sans_fail():
    assert has_failures([CheckResult("ok", "A"), CheckResult("warn", "B")]) is False


def test_has_failures_warn_seul_ne_declenche_pas_fail():
    assert has_failures([CheckResult("warn", "X")]) is False


# ── code de sortie ────────────────────────────────────────────────────────────

def test_code_sortie_0_sans_fail(tmp_path):
    _minimal_project(tmp_path)
    results = run_project_check(tmp_path, "test")
    assert has_failures(results) == any(r.status == "fail" for r in results)


def test_code_sortie_1_avec_fail():
    results = [CheckResult("ok", "A"), CheckResult("fail", "B")]
    assert has_failures(results) is True


# ── cmd_project_check depuis forge.py ─────────────────────────────────────────

def test_cmd_project_check_hors_projet(monkeypatch, tmp_path, capsys):
    """Hors projet Forge, la commande échoue proprement avec un message clair."""
    import forge

    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        forge.cmd_project_check()

    assert exc_info.value.code != 0
    assert "Erreur :" in capsys.readouterr().err


def test_cmd_project_check_utilise_le_cwd(monkeypatch, tmp_path):
    import forge

    captured = {}

    def fake_run(root, version):
        captured["root"] = root
        captured["version"] = version
        return []

    _minimal_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("cli.project_check.run_project_check", fake_run)
    monkeypatch.setattr("cli.project_check.print_check_report", lambda *_: None)
    monkeypatch.setattr("cli.project_check.has_failures", lambda _: False)

    forge.cmd_project_check()

    assert captured["root"] == tmp_path
    assert captured["version"] == forge._FORGE_VERSION
