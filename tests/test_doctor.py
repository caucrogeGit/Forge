"""Tests unitaires pour cli.project.doctor."""

import json
import sys
import types
from pathlib import Path


from cli.project.doctor import (
    CheckResult,
    _detect_mfa_indicators,
    check_db,
    check_env,
    check_i18n,
    check_mfa_dependency,
    check_migrations,
    check_model_entities,
    check_modules,
    check_node,
    check_python,
    check_ssl,
    check_mvc_structure,
    check_templates,
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
           "DB_NAME=forge_db\nDB_HOST=localhost\nDB_PORT=3306\n"
           "DB_APP_LOGIN=forge\nDB_APP_PWD=\n"
           "DB_ADMIN_LOGIN=root\nDB_ADMIN_PWD=\n"
           "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n")
    _write(tmp_path / "env" / "dev", "DB_NAME=forge_db\n")


def _minimal_config(tmp_path: Path, **extra) -> types.SimpleNamespace:
    cfg = types.SimpleNamespace(
        SSL_CERTFILE="cert.pem",
        SSL_KEYFILE="key.pem",
        DB_HOST="localhost",
        DB_PORT=3306,
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
        "schema_version": "1.0",
        "name": folder.capitalize(),
        "table": folder,
        "fields": [{"name": "nom", "type": "string", "max_length": 100}],
    }), encoding="utf-8")


def _write_relations(entities_root: Path) -> None:
    (entities_root / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": []}), encoding="utf-8"
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
    assert "3.12" in r.detail


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


def test_check_env_ok_sans_bloc_bdd(tmp_path):
    # ADR-060 : l'env neutre du squelette (aucune variable DB_*) doit passer.
    # Régression : check_env exigeait DB_NAME/DB_APP_*/DB_ADMIN_* et échouait.
    env = ("APP_NAME=Demo\nAPP_ROUTES_MODULE=mvc.routes\n"
           "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n")
    _write(tmp_path / "env" / "example", env)
    _write(tmp_path / "env" / "dev", env)
    r = check_env(tmp_path)
    assert r.status == "ok", r.detail


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
        json.dumps({"schema_version": "1.0", "relations": []}), encoding="utf-8"
    )
    r = check_mvc_structure(tmp_path)
    assert r.status == "ok"


def test_check_mvc_structure_ok_sans_relations_json(tmp_path):
    """Le squelette nu (ADR-024) n'a pas relations.json : ne doit pas FAIL.

    relations.json naît avec make:entity / make:relation ; son absence à la
    création du projet ne doit pas être signalée comme une erreur de structure.
    """
    mvc = tmp_path / "mvc"
    (mvc / "entities").mkdir(parents=True)
    (mvc / "views").mkdir()
    (mvc / "controllers").mkdir()
    (mvc / "routes.py").write_text("", encoding="utf-8")
    assert not (mvc / "entities" / "relations.json").exists()
    r = check_mvc_structure(tmp_path)
    assert r.status == "ok"


def test_check_mvc_structure_sans_views_et_controllers(tmp_path):
    """mvc/views/ et mvc/controllers/ sont requis."""
    mvc = tmp_path / "mvc"
    (mvc / "entities").mkdir(parents=True)
    (mvc / "routes.py").write_text("", encoding="utf-8")
    (mvc / "entities" / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": []}), encoding="utf-8"
    )
    r = check_mvc_structure(tmp_path)
    assert r.status == "fail"
    assert "mvc/views/" in r.detail or "mvc/controllers/" in r.detail


# ── check_model_entities ──────────────────────────────────────────────────────

def test_check_model_entities_no_dir(tmp_path):
    r = check_model_entities(tmp_path)
    assert r.status == "skip"


def test_check_model_entities_vide(tmp_path):
    # Projet vierge (ADR-024) : aucune entité est l'état nominal, pas une anomalie.
    # SKIP plutôt que WARN (FIX-DOCTOR-ENTITIES-SKELETON-001).
    (tmp_path / "mvc" / "entities").mkdir(parents=True)
    r = check_model_entities(tmp_path)
    assert r.status == "skip"
    assert "entité" in r.detail.lower()
    assert "make:entity" in r.detail


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


def _fake_backend(name="sqlite", conn_error=None):
    """Backend factice pour check_db (ADR-054/060) : agnostique, sans mariadb."""
    def get_connection():
        if conn_error is not None:
            raise conn_error
        return object()
    return types.SimpleNamespace(
        name=name,
        get_connection=get_connection,
        close_connection=lambda c: None,
    )


def _patch_backend(monkeypatch, resolver):
    import core.database.backend as backend_mod
    monkeypatch.setattr(backend_mod, "reset_backend", lambda: None)
    monkeypatch.setattr(backend_mod, "get_backend", resolver)


def test_check_db_backend_non_resolu_warn(tmp_path, monkeypatch):
    # Aucun backend (ou plusieurs sans DB_BACKEND) : avertissement, pas blocage.
    _write(tmp_path / "env" / "dev", "")
    def _boom():
        raise RuntimeError("Aucun backend BDD installé")
    _patch_backend(monkeypatch, _boom)
    r = check_db(tmp_path, _minimal_config(tmp_path))
    assert r.status == "warn"
    assert "backend" in r.detail.lower()


def test_check_db_connexion_impossible(tmp_path, monkeypatch):
    _write(tmp_path / "env" / "dev", "")
    _patch_backend(monkeypatch, lambda: _fake_backend(conn_error=RuntimeError("Access denied")))
    r = check_db(tmp_path, _minimal_config(tmp_path))
    assert r.status == "warn"
    assert "impossible" in r.detail


def test_check_db_ok(tmp_path, monkeypatch):
    _write(tmp_path / "env" / "dev", "")
    _patch_backend(monkeypatch, lambda: _fake_backend(name="sqlite"))
    r = check_db(tmp_path, _minimal_config(tmp_path))
    assert r.status == "ok"
    assert "sqlite" in r.detail


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


# ── check_migrations ─────────────────────────────────────────────────────────

def test_check_migrations_dossier_absent(tmp_path):
    r = check_migrations(tmp_path)
    assert r.status == "ok"
    assert "absent" in r.detail


def test_check_migrations_dossier_vide(tmp_path):
    (tmp_path / "mvc" / "migrations").mkdir(parents=True)
    r = check_migrations(tmp_path)
    assert r.status == "ok"
    assert "vide" in r.detail


def test_check_migrations_fichiers_valides(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    (d / "20260101120000_create_contact.sql").write_text("CREATE TABLE contact;", encoding="utf-8")
    (d / "20260201093045_add_email.sql").write_text("ALTER TABLE contact ADD email;", encoding="utf-8")
    r = check_migrations(tmp_path)
    assert r.status == "ok"
    assert "2" in r.detail


def test_check_migrations_noms_invalides(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    (d / "migration_001.sql").write_text("SELECT 1;", encoding="utf-8")
    r = check_migrations(tmp_path)
    assert r.status == "warn"
    assert "migration_001.sql" in r.detail


def test_check_migrations_fichiers_vides(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    (d / "20260101120000_init.sql").write_text("", encoding="utf-8")
    r = check_migrations(tmp_path)
    assert r.status == "warn"
    assert "vides" in r.detail


def test_check_migrations_ne_modifie_pas_les_fichiers(tmp_path):
    d = tmp_path / "mvc" / "migrations"
    d.mkdir(parents=True)
    f = d / "20260101120000_init.sql"
    f.write_text("CREATE TABLE t;", encoding="utf-8")
    before = f.read_text(encoding="utf-8")
    check_migrations(tmp_path)
    assert f.read_text(encoding="utf-8") == before


# ── check_i18n ────────────────────────────────────────────────────────────────

def test_check_i18n_absent(tmp_path):
    r = check_i18n(tmp_path)
    assert r.status == "ok"
    assert "absent" in r.detail


def test_check_i18n_dossier_vide(tmp_path):
    (tmp_path / "translations").mkdir()
    r = check_i18n(tmp_path)
    assert r.status == "warn"
    assert ".json" in r.detail


def test_check_i18n_valide(tmp_path):
    d = tmp_path / "translations"
    d.mkdir()
    (d / "fr.json").write_text('{"common.save": "Enregistrer"}', encoding="utf-8")
    r = check_i18n(tmp_path)
    assert r.status == "ok"
    assert "1" in r.detail


def test_check_i18n_json_invalide(tmp_path):
    d = tmp_path / "translations"
    d.mkdir()
    (d / "fr.json").write_text("not json", encoding="utf-8")
    r = check_i18n(tmp_path)
    assert r.status == "warn"
    assert "fr.json" in r.detail


def test_check_i18n_pas_un_dict(tmp_path):
    d = tmp_path / "translations"
    d.mkdir()
    (d / "fr.json").write_text('["a", "b"]', encoding="utf-8")
    r = check_i18n(tmp_path)
    assert r.status == "warn"
    assert "fr.json" in r.detail


def test_check_i18n_ne_modifie_pas_les_fichiers(tmp_path):
    d = tmp_path / "translations"
    d.mkdir()
    f = d / "fr.json"
    f.write_text('{"k": "v"}', encoding="utf-8")
    before = f.read_text(encoding="utf-8")
    check_i18n(tmp_path)
    assert f.read_text(encoding="utf-8") == before


# ── check_templates ───────────────────────────────────────────────────────────

def test_check_templates_dossier_absent(tmp_path):
    r = check_templates(tmp_path)
    assert r.status == "skip"


def test_check_templates_vide(tmp_path):
    (tmp_path / "mvc" / "views").mkdir(parents=True)
    r = check_templates(tmp_path)
    assert r.status == "warn"
    assert ".html" in r.detail


def test_check_templates_ok(tmp_path):
    views = tmp_path / "mvc" / "views"
    views.mkdir(parents=True)
    (views / "base.html").write_text("<html></html>", encoding="utf-8")
    (views / "contact").mkdir()
    (views / "contact" / "list.html").write_text("<ul></ul>", encoding="utf-8")
    r = check_templates(tmp_path)
    assert r.status == "ok"
    assert "2" in r.detail


def test_check_templates_ne_modifie_pas_les_fichiers(tmp_path):
    views = tmp_path / "mvc" / "views"
    views.mkdir(parents=True)
    f = views / "base.html"
    f.write_text("<html></html>", encoding="utf-8")
    before = f.read_text(encoding="utf-8")
    check_templates(tmp_path)
    assert f.read_text(encoding="utf-8") == before


# ── check_modules ─────────────────────────────────────────────────────────────

def test_check_modules_registre_absent(tmp_path):
    r = check_modules(tmp_path)
    assert r.status == "ok"
    assert "absent" in r.detail


def test_check_modules_registre_json_invalide(tmp_path):
    (tmp_path / "forge_modules.json").write_text("not json", encoding="utf-8")
    r = check_modules(tmp_path)
    assert r.status == "fail"
    assert "illisible" in r.detail


def test_check_modules_installed_invalide(tmp_path):
    (tmp_path / "forge_modules.json").write_text(
        '{"installed": "not_a_dict"}', encoding="utf-8"
    )
    r = check_modules(tmp_path)
    assert r.status == "fail"
    assert "installed" in r.detail


def test_check_modules_aucun_installe(tmp_path):
    (tmp_path / "forge_modules.json").write_text(
        '{"installed": {}}', encoding="utf-8"
    )
    r = check_modules(tmp_path)
    assert r.status == "ok"
    assert "aucun" in r.detail.lower()


def test_check_modules_source_absente(tmp_path):
    (tmp_path / "forge_modules.json").write_text(json.dumps({
        "installed": {
            "mon_module": {"name": "mon_module", "source": "modules/mon_module"}
        }
    }), encoding="utf-8")
    r = check_modules(tmp_path)
    assert r.status == "warn"
    assert "mon_module" in r.detail


def test_check_modules_ok(tmp_path):
    (tmp_path / "modules" / "mon_module").mkdir(parents=True)
    (tmp_path / "forge_modules.json").write_text(json.dumps({
        "installed": {
            "mon_module": {"name": "mon_module", "source": "modules/mon_module"}
        }
    }), encoding="utf-8")
    r = check_modules(tmp_path)
    assert r.status == "ok"
    assert "1" in r.detail


def test_check_modules_ne_modifie_pas_les_fichiers(tmp_path):
    f = tmp_path / "forge_modules.json"
    f.write_text('{"installed": {}}', encoding="utf-8")
    before = f.read_text(encoding="utf-8")
    check_modules(tmp_path)
    assert f.read_text(encoding="utf-8") == before


# ── run_all inclut les nouveaux checks ────────────────────────────────────────

def test_run_all_contient_migrations_i18n_templates_modules(tmp_path):
    results = run_all(tmp_path, "test")
    labels = {r.label for r in results}
    assert "Migrations" in labels
    assert "i18n" in labels
    assert "Templates" in labels
    assert "Modules" in labels


def test_forge_doctor_utilise_le_cwd(monkeypatch, tmp_path):
    import forge

    captured = {}

    def fake_run_all(root, version):
        captured["root"] = root
        captured["version"] = version
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("cli.project.doctor.run_all", fake_run_all)
    monkeypatch.setattr("cli.project.doctor.print_report", lambda _results, _version: None)
    monkeypatch.setattr("cli.project.doctor.has_failures", lambda _results: False)

    forge.cmd_doctor()

    assert captured["root"] == tmp_path
    assert captured["version"] == forge._FORGE_VERSION


# ── check_mfa_dependency ──────────────────────────────────────────────────────


def _write_mfa_controller(tmp_path: Path) -> None:
    ctrl = tmp_path / "mvc" / "controllers" / "mfa_challenge_controller.py"
    ctrl.parent.mkdir(parents=True, exist_ok=True)
    ctrl.write_text("# MFA challenge controller\n", encoding="utf-8")


def _write_mfa_route(tmp_path: Path) -> None:
    routes = tmp_path / "mvc" / "routes.py"
    routes.parent.mkdir(parents=True, exist_ok=True)
    routes.write_text('router.get("/login/mfa/", MfaChallengeController, "index")\n',
                      encoding="utf-8")


def _write_mfa_import(tmp_path: Path) -> None:
    ctrl = tmp_path / "mvc" / "controllers" / "auth_controller.py"
    ctrl.parent.mkdir(parents=True, exist_ok=True)
    ctrl.write_text("from forge_mvc_mfa import is_mfa_enabled\n", encoding="utf-8")


class TestDetectMfaIndicators:

    def test_no_mvc_dir_returns_empty(self, tmp_path):
        assert _detect_mfa_indicators(tmp_path) == []

    def test_mfa_controller_detected(self, tmp_path):
        _write_mfa_controller(tmp_path)
        indicators = _detect_mfa_indicators(tmp_path)
        assert any("mfa_challenge_controller" in i for i in indicators)

    def test_mfa_route_detected(self, tmp_path):
        _write_mfa_route(tmp_path)
        indicators = _detect_mfa_indicators(tmp_path)
        assert any("routes.py" in i for i in indicators)

    def test_mfa_import_detected(self, tmp_path):
        _write_mfa_import(tmp_path)
        indicators = _detect_mfa_indicators(tmp_path)
        assert any("forge_mvc_mfa" in i or "import MFA" in i for i in indicators)

    def test_no_mfa_signs_returns_empty(self, tmp_path):
        ctrl = tmp_path / "mvc" / "controllers" / "home_controller.py"
        ctrl.parent.mkdir(parents=True, exist_ok=True)
        ctrl.write_text("class HomeController: pass\n", encoding="utf-8")
        assert _detect_mfa_indicators(tmp_path) == []


class TestCheckMfaDependency:

    def test_skip_when_no_mfa_indicators(self, tmp_path):
        result = check_mfa_dependency(tmp_path)
        assert result.status == "skip"
        assert "aucun indice MFA" in result.detail

    def test_warn_when_mfa_used_but_module_absent(self, tmp_path, monkeypatch):
        _write_mfa_controller(tmp_path)
        monkeypatch.setattr(
            "cli.project.doctor.importlib.util.find_spec",
            lambda name: None,
        )
        result = check_mfa_dependency(tmp_path)
        assert result.status == "warn"
        assert "forge_mvc_mfa" in result.detail
        assert "opt-in" in result.detail or "source-only" in result.detail

    def test_ok_when_mfa_used_and_module_available(self, tmp_path, monkeypatch):
        _write_mfa_controller(tmp_path)
        import types as _types
        fake_spec = _types.SimpleNamespace()
        monkeypatch.setattr(
            "cli.project.doctor.importlib.util.find_spec",
            lambda name: fake_spec if name == "forge_mvc_mfa" else None,
        )
        result = check_mfa_dependency(tmp_path)
        assert result.status == "ok"
        assert "forge_mvc_mfa" in result.detail

    def test_warn_is_non_blocking(self, tmp_path, monkeypatch):
        _write_mfa_controller(tmp_path)
        monkeypatch.setattr(
            "cli.project.doctor.importlib.util.find_spec",
            lambda name: None,
        )
        result = check_mfa_dependency(tmp_path)
        assert result.status == "warn"

    def test_warning_mentions_opt_in_nature(self, tmp_path, monkeypatch):
        _write_mfa_route(tmp_path)
        monkeypatch.setattr(
            "cli.project.doctor.importlib.util.find_spec",
            lambda name: None,
        )
        result = check_mfa_dependency(tmp_path)
        assert "opt-in" in result.detail or "source-only" in result.detail

    def test_no_import_of_forge_mvc_mfa_at_check_time(self, tmp_path, monkeypatch):
        """Le check ne tente pas d'importer forge_mvc_mfa — il utilise find_spec."""
        calls: list[str] = []

        original = __import__

        def guarded_import(name, *args, **kwargs):
            if name == "forge_mvc_mfa":
                calls.append(name)
            return original(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", guarded_import)
        _write_mfa_controller(tmp_path)
        check_mfa_dependency(tmp_path)
        assert "forge_mvc_mfa" not in calls, (
            "check_mfa_dependency ne doit pas importer forge_mvc_mfa"
        )

    def test_no_import_of_pyotp_at_check_time(self, tmp_path, monkeypatch):
        """Le check ne tente pas d'importer pyotp — il utilise find_spec."""
        calls: list[str] = []

        original = __import__

        def guarded_import(name, *args, **kwargs):
            if name == "pyotp":
                calls.append(name)
            return original(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", guarded_import)
        _write_mfa_controller(tmp_path)
        check_mfa_dependency(tmp_path)
        assert "pyotp" not in calls, (
            "check_mfa_dependency ne doit pas importer pyotp"
        )
