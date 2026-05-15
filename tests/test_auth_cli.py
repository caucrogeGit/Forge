"""Tests des diagnostics CLI Auth/User — AUTH-USER-CLI-001."""

from __future__ import annotations

from pathlib import Path

import pytest

import forge
from forge_cli.auth import (
    AUTH_SQL_FILES,
    build_auth_status,
    cmd_auth_doctor,
    cmd_auth_list_sql,
    cmd_auth_status,
    list_auth_sql_files,
    run_auth_doctor,
)


def _project_files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _write_auth_sql(root: Path) -> None:
    sql_dir = root / "mvc" / "models" / "sql"
    sql_dir.mkdir(parents=True)
    for item in AUTH_SQL_FILES:
        (sql_dir / item.filename).write_text("-- optional auth sql\n", encoding="utf-8")


def test_auth_list_sql_liste_les_sql_connus(tmp_path):
    _write_auth_sql(tmp_path)

    checks = list_auth_sql_files(tmp_path)
    labels = {check.label for check in checks}

    assert "users" in labels
    assert "tokens" in labels
    assert "MFA factors" in labels
    assert "pont Auth/User -> RBAC" in labels
    assert all(check.status == "ok" for check in checks)


def test_auth_list_sql_signale_un_fichier_absent_comme_optionnel(tmp_path):
    checks = list_auth_sql_files(tmp_path)

    assert any(check.status == "warn" for check in checks)
    assert any("optionnel" in check.detail for check in checks)


def test_auth_status_liste_les_briques_attendues(tmp_path):
    checks = build_auth_status(tmp_path)
    labels = {check.label for check in checks}

    assert {
        "users",
        "sessions",
        "tokens",
        "reset password",
        "MFA",
        "user_roles",
        "Jinja helpers",
    }.issubset(labels)


def test_auth_status_ne_demande_pas_de_connexion_db(tmp_path, monkeypatch):
    pytest.importorskip("forge_mvc_rbac")
    pytest.importorskip("forge_mvc_mfa")
    import core.database as database_module

    def fail_db(*args, **kwargs):
        raise AssertionError("auth:status ne doit pas interroger la base")

    monkeypatch.setattr(database_module, "fetch_all", fail_db, raising=False)

    checks = build_auth_status(tmp_path)

    assert checks
    assert all(check.status in {"ok", "warn"} for check in checks)


def test_auth_doctor_verifie_modules_contrats_et_rbac(tmp_path):
    pytest.importorskip("forge_mvc_rbac")
    pytest.importorskip("forge_mvc_mfa")
    _write_auth_sql(tmp_path)

    checks = run_auth_doctor(tmp_path)
    labels = {check.label for check in checks}

    assert "core.auth.user" in labels
    assert "core.auth.user.AuthUser" in labels
    assert "forge_mvc_rbac.make_auth_jinja_context" in labels
    assert "forge_mvc_rbac.make_can" in labels
    assert all(check.status in {"ok", "warn"} for check in checks)


def test_commandes_auth_cli_ne_modifient_pas_le_projet(tmp_path, capsys):
    pytest.importorskip("forge_mvc_rbac")
    pytest.importorskip("forge_mvc_mfa")
    before = _project_files(tmp_path)

    cmd_auth_list_sql([], root=tmp_path)
    cmd_auth_status([], root=tmp_path)
    cmd_auth_doctor([], root=tmp_path)

    capsys.readouterr()
    assert _project_files(tmp_path) == before


def test_auth_list_sql_affiche_un_rapport_lisible(tmp_path, capsys):
    cmd_auth_list_sql([], root=tmp_path)

    stdout = capsys.readouterr().out
    assert "Forge auth:list-sql" in stdout
    assert "users" in stdout
    assert "mvc/models/sql/users.sql" in stdout
    assert "optionnel" in stdout


def test_auth_status_affiche_les_briques_sans_secret(tmp_path, capsys):
    pytest.importorskip("forge_mvc_rbac")
    pytest.importorskip("forge_mvc_mfa")
    cmd_auth_status([], root=tmp_path)

    stdout = capsys.readouterr().out
    assert "Forge auth:status" in stdout
    assert "Jinja helpers" in stdout
    assert "password_hash" not in stdout
    assert "token_hash" not in stdout
    assert "totp_secret" not in stdout
    assert "private_key" not in stdout


def test_auth_doctor_affiche_un_code_de_sortie_ok_sans_db(tmp_path, capsys):
    pytest.importorskip("forge_mvc_rbac")
    pytest.importorskip("forge_mvc_mfa")
    cmd_auth_doctor([], root=tmp_path)

    stdout = capsys.readouterr().out
    assert "Forge auth:doctor" in stdout
    assert "0 erreur(s)" in stdout


def test_auth_doctor_echoue_si_un_contrat_obligatoire_manque(monkeypatch, tmp_path):
    import forge_cli.auth as auth_module

    monkeypatch.setattr(auth_module, "AUTH_CONTRACTS", (("core.auth.user", "MissingContract"),))

    with pytest.raises(SystemExit) as exc_info:
        cmd_auth_doctor([], root=tmp_path)

    assert exc_info.value.code == 1


def test_commandes_refusent_les_arguments_en_trop(tmp_path):
    with pytest.raises(SystemExit):
        cmd_auth_list_sql(["--bad"], root=tmp_path)
    with pytest.raises(SystemExit):
        cmd_auth_status(["--bad"], root=tmp_path)
    with pytest.raises(SystemExit):
        cmd_auth_doctor(["--bad"], root=tmp_path)


def test_dispatch_forge_auth_doctor(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:doctor"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:doctor"]


def test_dispatch_forge_auth_status(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:status"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:status"]


def test_dispatch_forge_auth_list_sql(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:list-sql"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:list-sql"]


def test_auth_cli_ne_contient_pas_de_commandes_admin_completes():
    import forge_cli.auth as auth_module

    forbidden = (
        "auth:user:reset-password",
        "auth:role:assign",
        "auth:mfa:reset",
    )
    source = Path(auth_module.__file__).read_text(encoding="utf-8")

    for command in forbidden:
        assert command not in source
