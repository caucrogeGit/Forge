"""Tests unitaires pour forge_cli.doctor."""

import json
import sys
import types
from pathlib import Path

import pytest

from forge_cli.doctor import (
    CheckResult,
    check_db,
    check_env,
    check_model_entities,
    check_node,
    check_python,
    check_ssl,
    check_mvc_structure,
    has_failures,
    load_project_config,
    run_all,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _full_env(tmp_path: Path) -> None:
    """Écrit un env/example et env/dev complets pour les tests check_env OK."""
    _write(tmp_path / "env" / "example",
           "APP_NAME=Forge\nAPP_ROUTES_MODULE=mvc.routes\n"
           "DB_NAME=forge_db\nDB_APP_HOST=localhost\nDB_APP_PORT=3306\n"
           "DB_APP_LOGIN=forge\nDB_APP_PWD=\n"
           "DB_ADMIN_HOST=localhost\nDB_ADMIN_PORT=3306\n"
           "DB_ADMIN_LOGIN=root\nDB_ADMIN_PWD=\n"
           "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n")
    _write(tmp_path / "env" / "dev", "DB_NAME=forge_db\n")


def _minimal_config(tmp_path: Path, **extra) -> types.SimpleNamespace:
    cfg = types.SimpleNamespace(
        SSL_CERTFILE="cert.pem",
        SSL_KEYFILE="key.pem",
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge",
        DB_APP_PWD="",
        DB_NAME="forge_db",
    )
    for k, v in extra.items():
        setattr(cfg, k, v)
    return cfg


def _write_entity(entities_root: Path, folder: str) -> None:
    d = entities_root / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{folder}.json").write_text(json.dumps({
        "format_version": 1,
        "entity": folder.capitalize(),
        "table": folder,
        "fields": [{"name": "id", "sql_type": "INT",
                    "primary_key": True, "auto_increment": True}],
    }), encoding="utf-8")


def _write_relations(entities_root: Path) -> None:
    (entities_root / "relations.json").write_text(
        json.dumps({"format_version": 1, "relations": []}), encoding="utf-8"
    )


# ── load_project_config ───────────────────────────────────────────────────────

def test_load_project_config_absent(tmp_path):
    assert load_project_config(tmp_path) is None


def test_load_project_config_charge_module(tmp_path):
    _write(tmp_path / "config.py", "APP_NAME = 'TestApp'\nDB_NAME = 'test_db'\n")
    cfg = load_project_config(tmp_path)
    assert cfg is not None
    assert cfg.APP_NAME == "TestApp"
    assert cfg.DB_NAME == "test_db"


def test_load_project_config_pas_de_pollution_sys_modules(tmp_path):
    _write(tmp_path / "config.py", "VALUE = 42\n")
    load_project_config(tmp_path)
    assert "_forge_doctor_config" not in sys.modules


def test_load_project_config_pas_de_pollution_sys_path(tmp_path):
    _write(tmp_path / "config.py", "VALUE = 42\n")
    before = list(sys.path)
    load_project_config(tmp_path)
    assert sys.path == before


# ── check_python ──────────────────────────────────────────────────────────────

def test_check_python_ok(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 12, 0))
    r = check_python()
    assert r.status == "ok"
    assert "3.12.0" in r.detail


def test_check_python_fail(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 10, 4))
    r = check_python()
    assert r.status == "fail"
    assert "3.10.4" in r.detail
    assert "3.11" in r.detail


# ── check_env ─────────────────────────────────────────────────────────────────

def test_check_env_example_absent(tmp_path):
    r = check_env(tmp_path)
    assert r.status == "fail"
    assert "env/example" in r.detail


def test_check_env_dev_absent(tmp_path):
    _write(tmp_path / "env" / "example", "DB_NAME=forge_db\n")
    r = check_env(tmp_path)
    assert r.status == "warn"
    assert "env/dev" in r.detail


def test_check_env_fusion_example_et_dev(tmp_path):
    """Les clés de env/dev écrasent celles de env/example."""
    _full_env(tmp_path)
    _write(tmp_path / "env" / "dev", "DB_NAME=projet_reel\n")
    r = check_env(tmp_path)
    # La vérification interne utilise les valeurs fusionnées ; DB_NAME est présent et non vide
    assert r.status == "ok"


def test_check_env_ok(tmp_path):
    _full_env(tmp_path)
    r = check_env(tmp_path)
    assert r.status == "ok"


def test_check_env_accepte_pwd_vide(tmp_path):
    """DB_APP_PWD et DB_ADMIN_PWD peuvent être vides sans déclencher de FAIL."""
    _full_env(tmp_path)
    # Les deux mots de passe sont vides dans _full_env — le check doit passer
    r = check_env(tmp_path)
    assert r.status == "ok"


def test_check_env_cle_manquante(tmp_path):
    _write(tmp_path / "env" / "example", "APP_NAME=Forge\n")
    _write(tmp_path / "env" / "dev", "APP_NAME=Forge\n")
    r = check_env(tmp_path)
    assert r.status in ("fail", "warn")
    # DB_NAME et autres clés critiques sont absentes


# ── check_mvc_structure ───────────────────────────────────────────────────────

def test_check_mvc_structure_absente(tmp_path):
    r = check_mvc_structure(tmp_path)
    assert r.status == "fail"
    assert "mvc/" in r.detail


def test_check_mvc_structure_partielle(tmp_path):
    (tmp_path / "mvc").mkdir()
    r = check_mvc_structure(tmp_path)
    assert r.status == "fail"
    assert "mvc/routes.py" in r.detail


def test_check_mvc_structure_ok(tmp_path):
    mvc = tmp_path / "mvc"
    (mvc / "entities").mkdir(parents=True)
    (mvc / "views").mkdir()
    (mvc / "controllers").mkdir()
    (mvc / "routes.py").write_text("", encoding="utf-8")
    (mvc / "entities" / "relations.json").write_text(
        json.dumps({"format_version": 1, "relations": []}), encoding="utf-8"
    )
    r = check_mvc_structure(tmp_path)
    assert r.status == "ok"


def test_check_mvc_structure_sans_views_et_controllers(tmp_path):
    """mvc/views/ et mvc/controllers/ sont requis."""
    mvc = tmp_path / "mvc"
    (mvc / "entities").mkdir(parents=True)
    (mvc / "routes.py").write_text("", encoding="utf-8")
    (mvc / "entities" / "relations.json").write_text(
        json.dumps({"format_version": 1, "relations": []}), encoding="utf-8"
    )
    r = check_mvc_structure(tmp_path)
    assert r.status == "fail"
    assert "mvc/views/" in r.detail or "mvc/controllers/" in r.detail


# ── check_model_entities ──────────────────────────────────────────────────────

def test_check_model_entities_no_dir(tmp_path):
    r = check_model_entities(tmp_path)
    assert r.status == "skip"


def test_check_model_entities_vide(tmp_path):
    (tmp_path / "mvc" / "entities").mkdir(parents=True)
    r = check_model_entities(tmp_path)
    assert r.status == "warn"
    assert "entité" in r.detail.lower()


def test_check_model_entities_ok(tmp_path):
    entities = tmp_path / "mvc" / "entities"
    entities.mkdir(parents=True)
    _write_entity(entities, "contact")
    _write_relations(entities)
    r = check_model_entities(tmp_path)
    assert r.status == "ok"
    assert "1" in r.detail


def test_check_model_entities_invalide(tmp_path):
    entities = tmp_path / "mvc" / "entities"
    (entities / "contact").mkdir(parents=True)
    (entities / "contact" / "contact.json").write_text(
        '{"entity": "Contact"}', encoding="utf-8"
    )
    _write_relations(entities)
    r = check_model_entities(tmp_path)
    assert r.status == "fail"


# ── check_ssl ─────────────────────────────────────────────────────────────────

def test_check_ssl_config_absente(tmp_path):
    r = check_ssl(tmp_path, None)
    assert r.status == "skip"


def test_check_ssl_absents(tmp_path):
    cfg = _minimal_config(tmp_path)
    r = check_ssl(tmp_path, cfg)
    assert r.status == "warn"
    assert "cert.pem" in r.detail


def test_check_ssl_ok(tmp_path):
    (tmp_path / "cert.pem").write_text("cert", encoding="utf-8")
    (tmp_path / "key.pem").write_text("key",  encoding="utf-8")
    cfg = _minimal_config(tmp_path)
    r = check_ssl(tmp_path, cfg)
    assert r.status == "ok"


def test_check_ssl_chemins_personnalises(tmp_path):
    (tmp_path / "server.crt").write_text("cert", encoding="utf-8")
    (tmp_path / "server.key").write_text("key",  encoding="utf-8")
    cfg = _minimal_config(tmp_path, SSL_CERTFILE="server.crt", SSL_KEYFILE="server.key")
    r = check_ssl(tmp_path, cfg)
    assert r.status == "ok"


# ── check_node ────────────────────────────────────────────────────────────────

def test_check_node_present(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/npm" if cmd == "npm" else None)
    r = check_node()
    assert r.status == "ok"


def test_check_node_absent(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _cmd: None)
    r = check_node()
    assert r.status == "warn"
    assert "npm" in r.detail


# ── check_db ──────────────────────────────────────────────────────────────────

def test_check_db_config_absente(tmp_path):
    r = check_db(tmp_path, None)
    assert r.status == "skip"


def test_check_db_dev_absent(tmp_path):
    _write(tmp_path / "env" / "example", "")
    cfg = _minimal_config(tmp_path)
    r = check_db(tmp_path, cfg)
    assert r.status == "skip"
    assert "env/dev" in r.detail


def test_check_db_mariadb_absent(tmp_path, monkeypatch):
    _write(tmp_path / "env" / "dev", "")
    cfg = _minimal_config(tmp_path)
    monkeypatch.setitem(sys.modules, "mariadb", None)
    r = check_db(tmp_path, cfg)
    assert r.status == "warn"
    assert "mariadb" in r.detail.lower()


def test_check_db_connexion_impossible(tmp_path, monkeypatch):
    _write(tmp_path / "env" / "dev", "")
    cfg = _minimal_config(tmp_path)

    fake_mariadb = types.ModuleType("mariadb")
    fake_mariadb.Error = Exception

    def fake_connect(**_kw):
        raise fake_mariadb.Error("Access denied")

    fake_mariadb.connect = fake_connect
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    r = check_db(tmp_path, cfg)
    assert r.status == "warn"
    assert "impossible" in r.detail


def test_check_db_ok(tmp_path, monkeypatch):
    _write(tmp_path / "env" / "dev", "")
    cfg = _minimal_config(tmp_path)

    fake_conn = types.SimpleNamespace(close=lambda: None)
    fake_mariadb = types.ModuleType("mariadb")
    fake_mariadb.Error = Exception
    fake_mariadb.connect = lambda **_kw: fake_conn
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    r = check_db(tmp_path, cfg)
    assert r.status == "ok"
    assert "forge_db" in r.detail


# ── has_failures & codes de sortie ────────────────────────────────────────────

def test_has_failures_avec_fail():
    results = [CheckResult("ok", "A"), CheckResult("fail", "B"), CheckResult("warn", "C")]
    assert has_failures(results) is True


def test_has_failures_sans_fail():
    results = [CheckResult("ok", "A"), CheckResult("warn", "B"), CheckResult("skip", "C")]
    assert has_failures(results) is False


def test_has_failures_warn_seul_ne_declenche_pas_fail():
    results = [CheckResult("warn", "X"), CheckResult("warn", "Y")]
    assert has_failures(results) is False


def test_code_sortie_0_sans_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 12, 0))
    results = run_all(tmp_path, "main")
    # Sans projet initialisé, on a des FAIL (structure MVC absente etc.)
    # On vérifie simplement la cohérence entre has_failures et les résultats
    assert has_failures(results) == any(r.status == "fail" for r in results)


def test_code_sortie_1_avec_fail():
    results = [CheckResult("ok", "A"), CheckResult("fail", "B")]
    assert has_failures(results) is True


def test_warn_uniquement_code_sortie_0():
    results = [CheckResult("ok", "A"), CheckResult("warn", "B"), CheckResult("skip", "C")]
    assert has_failures(results) is False


def test_forge_doctor_utilise_le_cwd(monkeypatch, tmp_path):
    import forge

    captured = {}

    def fake_run_all(root, version):
        captured["root"] = root
        captured["version"] = version
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("forge_cli.doctor.run_all", fake_run_all)
    monkeypatch.setattr("forge_cli.doctor.print_report", lambda _results, _version: None)
    monkeypatch.setattr("forge_cli.doctor.has_failures", lambda _results: False)

    forge.cmd_doctor()

    assert captured["root"] == tmp_path
    assert captured["version"] == "1.0.1"
