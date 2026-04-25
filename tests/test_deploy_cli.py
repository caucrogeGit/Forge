"""Tests pour les commandes forge deploy:init et forge deploy:check."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from forge_cli.deploy import (
    _check_results,
    _nginx_conf,
    _systemd_service,
    cmd_deploy_check,
    cmd_deploy_init,
)


# ── deploy:init ───────────────────────────────────────────────────────────────

def test_deploy_init_cree_les_fichiers(tmp_path):
    cmd_deploy_init(tmp_path)

    assert (tmp_path / "deploy" / "nginx" / "forge-app.conf").exists()
    assert (tmp_path / "deploy" / "systemd" / "forge-app.service").exists()
    assert (tmp_path / "deploy" / "README_DEPLOY.md").exists()


def test_deploy_init_ne_pas_ecraser(tmp_path, capsys):
    cmd_deploy_init(tmp_path)
    conf = tmp_path / "deploy" / "nginx" / "forge-app.conf"
    conf.write_text("MODIFIÉ", encoding="utf-8")

    capsys.readouterr()  # vider la sortie du premier appel
    cmd_deploy_init(tmp_path)

    assert conf.read_text(encoding="utf-8") == "MODIFIÉ"
    output, _ = capsys.readouterr()
    assert "PRÉSERVÉ" in output


def test_deploy_init_idempotent_pas_erreur(tmp_path):
    cmd_deploy_init(tmp_path)
    cmd_deploy_init(tmp_path)  # ne doit pas lever


def test_nginx_contient_adresse(tmp_path):
    cmd_deploy_init(tmp_path)
    conf = (tmp_path / "deploy" / "nginx" / "forge-app.conf").read_text(encoding="utf-8")
    assert "proxy_pass         http://127.0.0.1:8000;" in conf
    assert "Nginx termine HTTPS" in conf


def test_nginx_contient_client_max_body_size(tmp_path):
    cmd_deploy_init(tmp_path)
    conf = (tmp_path / "deploy" / "nginx" / "forge-app.conf").read_text(encoding="utf-8")
    assert "client_max_body_size" in conf


def test_nginx_conf_headers_proxy(tmp_path):
    cmd_deploy_init(tmp_path)
    conf = (tmp_path / "deploy" / "nginx" / "forge-app.conf").read_text(encoding="utf-8")
    assert "X-Real-IP" in conf
    assert "X-Forwarded-For" in conf
    assert "X-Forwarded-Proto" in conf


def test_systemd_contient_working_directory_et_exec_start(tmp_path):
    cmd_deploy_init(tmp_path)
    service = (tmp_path / "deploy" / "systemd" / "forge-app.service").read_text(encoding="utf-8")
    assert "WorkingDirectory=" in service
    assert "ExecStart=" in service


def test_systemd_contient_restart_always(tmp_path):
    cmd_deploy_init(tmp_path)
    service = (tmp_path / "deploy" / "systemd" / "forge-app.service").read_text(encoding="utf-8")
    assert "Restart=always" in service


def test_systemd_contient_environment_file(tmp_path):
    cmd_deploy_init(tmp_path)
    service = (tmp_path / "deploy" / "systemd" / "forge-app.service").read_text(encoding="utf-8")
    assert "EnvironmentFile=" in service
    assert "env/prod" in service


def test_systemd_lance_app_en_mode_prod(tmp_path):
    cmd_deploy_init(tmp_path)
    service = (tmp_path / "deploy" / "systemd" / "forge-app.service").read_text(encoding="utf-8")
    assert "app.py --env prod" in service


def test_systemd_working_directory_pointe_vers_root(tmp_path):
    cmd_deploy_init(tmp_path)
    service = (tmp_path / "deploy" / "systemd" / "forge-app.service").read_text(encoding="utf-8")
    assert f"WorkingDirectory={tmp_path}" in service


# ── deploy:check ──────────────────────────────────────────────────────────────

def test_deploy_check_ne_plante_pas_si_elements_manquent(tmp_path, capsys):
    try:
        cmd_deploy_check(tmp_path)
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "forge deploy:check" in output


def test_deploy_check_affiche_warn_pour_env_prod_absent(tmp_path, capsys):
    try:
        cmd_deploy_check(tmp_path)
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "[WARN]" in output


def test_deploy_check_ok_avec_env_prod_complet(tmp_path, capsys):
    env_dir = tmp_path / "env"
    env_dir.mkdir()
    (env_dir / "prod").write_text(
        "DB_APP_HOST=localhost\nDB_NAME=forge_db\nDB_APP_LOGIN=forge\n",
        encoding="utf-8",
    )
    try:
        cmd_deploy_check(tmp_path)
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "[OK]" in output


def test_deploy_check_erreur_variables_db_manquantes(tmp_path):
    env_dir = tmp_path / "env"
    env_dir.mkdir()
    (env_dir / "prod").write_text("DB_NAME=forge_db\n", encoding="utf-8")

    results = _check_results(tmp_path)
    db_result = next((r for r in results if r.label == "Variables DB"), None)
    assert db_result is not None
    assert db_result.status == "error"


def test_deploy_check_signale_cwd_non_forge(tmp_path):
    results = _check_results(tmp_path)
    project_result = next((r for r in results if r.label == "Projet Forge"), None)
    assert project_result is not None
    assert project_result.status == "warn"


def test_deploy_check_detecte_projet_forge(tmp_path):
    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "config.py").write_text("", encoding="utf-8")
    (tmp_path / "mvc").mkdir()
    (tmp_path / "mvc" / "routes.py").write_text("", encoding="utf-8")
    (tmp_path / "env").mkdir()
    (tmp_path / "env" / "example").write_text("", encoding="utf-8")

    results = _check_results(tmp_path)
    project_result = next((r for r in results if r.label == "Projet Forge"), None)
    assert project_result is not None
    assert project_result.status == "ok"


def test_deploy_check_detecte_venv(tmp_path):
    (tmp_path / ".venv").mkdir()
    results = _check_results(tmp_path)
    venv_result = next((r for r in results if r.label == "Environnement virtuel"), None)
    assert venv_result is not None
    assert venv_result.status == "ok"


def test_deploy_check_warn_upload_root_absent(tmp_path):
    env_dir = tmp_path / "env"
    env_dir.mkdir()
    (env_dir / "prod").write_text(
        "DB_APP_HOST=localhost\nDB_NAME=forge_db\nDB_APP_LOGIN=forge\n",
        encoding="utf-8",
    )

    results = _check_results(tmp_path)
    upload_result = next((r for r in results if r.label == "Variable UPLOAD_ROOT"), None)
    assert upload_result is not None
    assert upload_result.status == "warn"


def test_deploy_check_warn_si_nginx_http_et_app_ssl_force(tmp_path):
    cmd_deploy_init(tmp_path)
    env_dir = tmp_path / "env"
    env_dir.mkdir()
    (env_dir / "prod").write_text(
        "DB_APP_HOST=localhost\nDB_NAME=forge_db\nDB_APP_LOGIN=forge\n"
        "UPLOAD_ROOT=storage/uploads\nAPP_SSL_ENABLED=true\n",
        encoding="utf-8",
    )

    results = _check_results(tmp_path)
    protocol_result = next((r for r in results if r.label == "HTTP/HTTPS local"), None)
    assert protocol_result is not None
    assert protocol_result.status == "warn"


def test_deploy_check_deploy_files_warn_si_absent(tmp_path):
    results = _check_results(tmp_path)
    deploy_warns = [r for r in results if "deploy/" in r.label and r.status == "warn"]
    assert len(deploy_warns) == 3


def test_deploy_check_deploy_files_ok_apres_init(tmp_path):
    cmd_deploy_init(tmp_path)
    results = _check_results(tmp_path)
    deploy_oks = [r for r in results if "deploy/" in r.label and r.status == "ok"]
    assert len(deploy_oks) == 3


# ── Entrypoint Forge ──────────────────────────────────────────────────────────

def test_entrypoint_deploy_init_accessible(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["forge", "deploy:init"])
    import forge
    forge.main()
    output, _ = capsys.readouterr()
    assert "forge-app.conf" in output


def test_entrypoint_deploy_check_accessible(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["forge", "deploy:check"])
    import forge
    try:
        forge.main()
    except SystemExit:
        pass
    output, _ = capsys.readouterr()
    assert "forge deploy:check" in output
