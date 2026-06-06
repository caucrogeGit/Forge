"""Tests des commandes CLI mail — sans fork du processus, sans config.py réel."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import core.forge as forge
pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail.cli import (
    _check_enabled,
    _check_from_address,
    _check_smtp_config,
    _check_storage_mail,
    _check_templates_dir,
    _check_transport,
    cmd_mail_doctor,
    cmd_mail_init,
    cmd_mail_render,
    cmd_mail_test,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def restore_forge():
    snapshot = dict(forge._cfg)
    yield
    forge._cfg.clear()
    forge._cfg.update(snapshot)


@pytest.fixture()
def no_env(monkeypatch):
    """Neutralise _load_env_and_configure_forge — forge est configuré par le test."""
    monkeypatch.setattr("forge_mvc_mail.cli._load_env_and_configure_forge", lambda root: None)


def _forge_mail(tmp_path: Path, *, transport: str = "fake", enabled: bool = True) -> None:
    forge.configure(
        mail_enabled=enabled,
        mail_transport=transport,
        mail_from="from@x.test",
        mail_host="smtp.x.test",
        mail_port=587,
        mail_username="",
        mail_password="",
        mail_use_tls=False,
        mail_use_ssl=False,
        mail_timeout=10,
        mail_log_dir=str(tmp_path / "mail"),
        mail_templates_dir=str(tmp_path / "templates"),
    )


def _make_templates(tmp_path: Path, name: str = "bienvenue") -> Path:
    tpl = tmp_path / "templates"
    tpl.mkdir(exist_ok=True)
    (tpl / f"{name}_subject.txt").write_text("Bonjour {{ prenom }}", encoding="utf-8")
    (tpl / f"{name}_text.txt").write_text("Corps {{ prenom }}", encoding="utf-8")
    return tpl


# ── mail:init ─────────────────────────────────────────────────────────────────

def test_init_cree_dossier_templates(tmp_path):
    cmd_mail_init([], root=tmp_path)
    assert (tmp_path / "mvc" / "mail" / "templates").is_dir()


def test_init_cree_dossier_storage(tmp_path):
    cmd_mail_init([], root=tmp_path)
    assert (tmp_path / "storage" / "mail").is_dir()


def test_init_cree_gitkeep(tmp_path):
    cmd_mail_init([], root=tmp_path)
    assert (tmp_path / "storage" / "mail" / ".gitkeep").exists()


def test_init_cree_templates_exemples(tmp_path):
    cmd_mail_init([], root=tmp_path)
    tpl = tmp_path / "mvc" / "mail" / "templates"
    assert (tpl / "test_subject.txt").exists()
    assert (tpl / "test_text.txt").exists()
    assert (tpl / "test_html.html").exists()


def test_init_cree_sample_json(tmp_path):
    cmd_mail_init([], root=tmp_path)
    ctx = json.loads((tmp_path / "sample.json").read_text(encoding="utf-8"))
    assert "date" in ctx
    assert "transport" in ctx


def test_init_ne_pas_ecraser_templates(tmp_path, capsys):
    cmd_mail_init([], root=tmp_path)
    subj = tmp_path / "mvc" / "mail" / "templates" / "test_subject.txt"
    subj.write_text("MODIFIÉ", encoding="utf-8")

    capsys.readouterr()
    cmd_mail_init([], root=tmp_path)

    assert subj.read_text(encoding="utf-8") == "MODIFIÉ"
    out, _ = capsys.readouterr()
    assert "PRÉSERVÉ" in out


def test_init_ne_pas_ecraser_sample_json(tmp_path, capsys):
    cmd_mail_init([], root=tmp_path)
    (tmp_path / "sample.json").write_text('{"x": 1}', encoding="utf-8")

    capsys.readouterr()
    cmd_mail_init([], root=tmp_path)

    out, _ = capsys.readouterr()
    assert "PRÉSERVÉ" in out


def test_init_idempotent(tmp_path):
    cmd_mail_init([], root=tmp_path)
    cmd_mail_init([], root=tmp_path)
    assert (tmp_path / "mvc" / "mail" / "templates").is_dir()


def test_init_affiche_ok_et_cree(tmp_path, capsys):
    cmd_mail_init([], root=tmp_path)
    out, _ = capsys.readouterr()
    assert "OK" in out


# ── mail:test ─────────────────────────────────────────────────────────────────

def test_test_sans_to_leve_system_exit(no_env, restore_forge, tmp_path):
    with pytest.raises(SystemExit):
        cmd_mail_test([], root=tmp_path)


def test_test_to_sans_valeur_leve_system_exit(no_env, restore_forge, tmp_path):
    with pytest.raises(SystemExit):
        cmd_mail_test(["--to"], root=tmp_path)


def test_test_null_transport_affiche_warn(no_env, restore_forge, tmp_path, capsys):
    _forge_mail(tmp_path, transport="null", enabled=False)
    cmd_mail_test(["--to", "x@x.test"], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "WARN" in stdout


def test_test_fake_transport_affiche_ok(no_env, restore_forge, tmp_path, capsys):
    _forge_mail(tmp_path, transport="fake", enabled=True)
    cmd_mail_test(["--to", "x@x.test"], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "OK" in stdout


def test_test_affiche_nom_transport(no_env, restore_forge, tmp_path, capsys):
    _forge_mail(tmp_path, transport="fake", enabled=True)
    cmd_mail_test(["--to", "x@x.test"], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "FakeTransport" in stdout


def test_test_log_transport_cree_fichier(no_env, restore_forge, tmp_path, capsys):
    log_dir = tmp_path / "mail"
    _forge_mail(tmp_path, transport="log", enabled=True)
    forge.configure(mail_log_dir=str(log_dir))
    cmd_mail_test(["--to", "x@x.test"], root=tmp_path)
    assert len(list(log_dir.glob("*.eml"))) == 1


def test_test_mail_enabled_false_affiche_warn_pas_erreur(no_env, restore_forge, tmp_path, capsys):
    _forge_mail(tmp_path, transport="smtp", enabled=False)
    cmd_mail_test(["--to", "x@x.test"], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "WARN" in stdout


# ── mail:render ───────────────────────────────────────────────────────────────

def test_render_sans_args_leve_system_exit(no_env, restore_forge, tmp_path):
    with pytest.raises(SystemExit):
        cmd_mail_render([], root=tmp_path)


def test_render_affiche_subject_interpole(no_env, restore_forge, tmp_path, capsys):
    tpl = _make_templates(tmp_path)
    _forge_mail(tmp_path)
    forge.configure(mail_templates_dir=str(tpl))
    cmd_mail_render(["bienvenue"], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "Sujet" in stdout


def test_render_context_json_interpole(no_env, restore_forge, tmp_path, capsys):
    tpl = _make_templates(tmp_path)
    _forge_mail(tmp_path)
    forge.configure(mail_templates_dir=str(tpl))
    ctx = tmp_path / "ctx.json"
    ctx.write_text('{"prenom": "Alice"}', encoding="utf-8")
    cmd_mail_render(["bienvenue", "--context", str(ctx)], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "Alice" in stdout


def test_render_context_fichier_manquant_leve_system_exit(no_env, restore_forge, tmp_path):
    _forge_mail(tmp_path)
    with pytest.raises(SystemExit):
        cmd_mail_render(
            ["bienvenue", "--context", str(tmp_path / "inexistant.json")],
            root=tmp_path,
        )


def test_render_context_json_invalide_leve_system_exit(no_env, restore_forge, tmp_path):
    _forge_mail(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text("{ pas du json", encoding="utf-8")
    with pytest.raises(SystemExit):
        cmd_mail_render(["bienvenue", "--context", str(bad)], root=tmp_path)


def test_render_template_manquant_leve_system_exit(no_env, restore_forge, tmp_path):
    tpl = tmp_path / "templates"
    tpl.mkdir()
    _forge_mail(tmp_path)
    forge.configure(mail_templates_dir=str(tpl))
    with pytest.raises(SystemExit):
        cmd_mail_render(["fantome"], root=tmp_path)


def test_render_sans_html_naffiche_pas_balise_html(no_env, restore_forge, tmp_path, capsys):
    tpl = _make_templates(tmp_path)
    _forge_mail(tmp_path)
    forge.configure(mail_templates_dir=str(tpl))
    cmd_mail_render(["bienvenue"], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "[HTML]" not in stdout


def test_render_avec_html_affiche_section_html(no_env, restore_forge, tmp_path, capsys):
    tpl = _make_templates(tmp_path)
    (tpl / "bienvenue_html.html").write_text("<p>{{ prenom }}</p>", encoding="utf-8")
    _forge_mail(tmp_path)
    forge.configure(mail_templates_dir=str(tpl))
    cmd_mail_render(["bienvenue"], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "[HTML]" in stdout


# ── mail:doctor — checks unitaires ───────────────────────────────────────────

def test_check_enabled_true():
    r = _check_enabled(True, "log")
    assert r.status == "ok"


def test_check_enabled_false_warn():
    r = _check_enabled(False, "null")
    assert r.status == "warn"
    assert "false" in r.detail


def test_check_transport_valide():
    for name in ("null", "fake", "console", "log", "smtp"):
        assert _check_transport(name).status == "ok"


def test_check_transport_invalide_fail():
    r = _check_transport("pigeon")
    assert r.status == "fail"
    assert "pigeon" in r.detail


def test_check_templates_dir_present(tmp_path):
    d = tmp_path / "mvc" / "mail" / "templates"
    d.mkdir(parents=True)
    (d / "t_subject.txt").write_text("S")
    r = _check_templates_dir(tmp_path)
    assert r.status == "ok"
    assert "1 fichier" in r.detail


def test_check_templates_dir_absent(tmp_path):
    r = _check_templates_dir(tmp_path)
    assert r.status == "warn"


def test_check_storage_mail_cree_si_absent(tmp_path):
    r = _check_storage_mail(tmp_path)
    assert r.status == "ok"
    assert (tmp_path / "storage" / "mail").is_dir()


def test_check_storage_mail_existant_ok(tmp_path):
    (tmp_path / "storage" / "mail").mkdir(parents=True)
    r = _check_storage_mail(tmp_path)
    assert r.status == "ok"


def test_check_from_address_non_vide():
    assert _check_from_address("exp@x.test").status == "ok"


def test_check_from_address_vide_warn():
    r = _check_from_address("")
    assert r.status == "warn"


def test_check_smtp_config_host_present():
    results = _check_smtp_config("smtp.x.test", 587)
    statuses = {r.label: r.status for r in results}
    assert statuses["MAIL_HOST"] == "ok"
    assert statuses["MAIL_PORT"] == "ok"


def test_check_smtp_config_host_absent():
    results = _check_smtp_config("", 587)
    statuses = {r.label: r.status for r in results}
    assert statuses["MAIL_HOST"] == "fail"


# ── mail:doctor — intégration ─────────────────────────────────────────────────

def test_doctor_passe_avec_config_valide(no_env, restore_forge, tmp_path, capsys):
    (tmp_path / "mvc" / "mail" / "templates").mkdir(parents=True)
    _forge_mail(tmp_path, transport="log", enabled=True)
    cmd_mail_doctor([], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "mail:doctor" in stdout
    assert "0 erreur" in stdout


def test_doctor_fail_si_transport_invalide(no_env, restore_forge, tmp_path):
    _forge_mail(tmp_path, transport="pigeon", enabled=True)
    with pytest.raises(SystemExit):
        cmd_mail_doctor([], root=tmp_path)


def test_doctor_affiche_warn_mail_disabled(no_env, restore_forge, tmp_path, capsys):
    _forge_mail(tmp_path, transport="log", enabled=False)
    cmd_mail_doctor([], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "WARN" in stdout


def test_doctor_smtp_verifie_host(no_env, restore_forge, tmp_path, capsys):
    _forge_mail(tmp_path, transport="smtp", enabled=True)
    forge.configure(mail_host="")
    with pytest.raises(SystemExit):
        cmd_mail_doctor([], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "MAIL_HOST" in stdout


def test_doctor_smtp_ok_si_host_present(no_env, restore_forge, tmp_path, capsys):
    (tmp_path / "mvc" / "mail" / "templates").mkdir(parents=True)
    _forge_mail(tmp_path, transport="smtp", enabled=True)
    forge.configure(mail_host="smtp.x.test", mail_from="from@x.test")
    cmd_mail_doctor([], root=tmp_path)
    stdout, _ = capsys.readouterr()
    assert "MAIL_HOST" in stdout
    assert "MAIL_PORT" in stdout
