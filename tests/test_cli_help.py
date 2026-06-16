"""Tests pour l'aide CLI Forge — forge help / forge --help."""

from __future__ import annotations

import sys

import forge
from forge_cli.help import build_help


# ── build_help ────────────────────────────────────────────────────────────────

def test_build_help_contient_version():
    text = build_help("2.2.0")
    assert "2.2.0" in text


def test_build_help_contient_usage():
    text = build_help("2.2.0")
    assert "forge <commande>" in text


def test_build_help_contient_commandes_projet():
    text = build_help("2.2.0")
    assert "new" in text
    assert "doctor" in text
    assert "project:check" in text
    assert "routes:list" in text


def test_build_help_contient_commandes_entites():
    text = build_help("2.2.0")
    assert "make:entity" in text
    assert "make:crud" in text
    assert "sync:entity" in text


def test_build_help_contient_commandes_db():
    text = build_help("2.2.0")
    assert "db:init" in text
    assert "migration:apply" in text


def test_build_help_contient_commandes_modules():
    text = build_help("2.2.0")
    assert "module:list" in text
    assert "module:install" in text


def test_build_help_contient_commandes_auth():
    text = build_help("2.2.0")
    assert "auth:init" in text
    assert "auth:user:create" in text


def test_build_help_contient_commandes_mail():
    text = build_help("2.2.0")
    assert "mail:init" in text
    assert "mail:doctor" in text


def test_build_help_contient_commandes_pages_publiques():
    text = build_help("2.2.0")
    assert "make:public-page" in text
    assert "make:public-contact" in text


def test_build_help_contient_exemples():
    text = build_help("2.2.0")
    assert "Exemples" in text
    assert "forge new" in text


def test_build_help_contient_lien_documentation():
    text = build_help("2.2.0")
    assert "github.com" in text


def test_build_help_doctor_et_project_check_decrits():
    """doctor et project:check doivent avoir des descriptions distinctes."""
    text = build_help("2.2.0")
    assert "doctor" in text
    assert "project:check" in text
    lines = text.splitlines()
    doctor_line = next((l for l in lines if "doctor" in l and "auth" not in l and "mail" not in l), None)
    check_line = next((l for l in lines if "project:check" in l), None)
    assert doctor_line is not None
    assert check_line is not None
    assert doctor_line != check_line


def test_build_help_pas_de_traceback():
    text = build_help("2.2.0")
    assert "Traceback" not in text


# ── dispatch help ─────────────────────────────────────────────────────────────

def test_forge_sans_argument_affiche_aide(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge"])
    forge.main()
    out = capsys.readouterr().out
    assert "doctor" in out
    assert "project:check" in out


def test_forge_help_affiche_aide(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "help"])
    forge.main()
    out = capsys.readouterr().out
    assert "doctor" in out
    assert "make:crud" in out


def test_forge_tiret_tiret_help_affiche_aide(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "--help"])
    forge.main()
    out = capsys.readouterr().out
    assert "doctor" in out
    assert "make:entity" in out


def test_forge_h_affiche_aide(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "-h"])
    forge.main()
    out = capsys.readouterr().out
    assert "doctor" in out


def test_aide_sans_code_erreur(monkeypatch, capsys):
    """forge help doit terminer normalement (pas de SystemExit)."""
    monkeypatch.setattr(sys, "argv", ["forge", "help"])
    forge.main()  # ne doit pas lever


def test_aide_affiche_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "help"])
    forge.main()
    out = capsys.readouterr().out
    assert forge._FORGE_VERSION in out


def test_aide_affiche_commandes_recentes(monkeypatch, capsys):
    """project:check et doctor doivent apparaître dans l'aide."""
    monkeypatch.setattr(sys, "argv", ["forge", "help"])
    forge.main()
    out = capsys.readouterr().out
    assert "project:check" in out
    assert "doctor" in out
    assert "make:public-page" in out
    assert "module:install" in out


def test_aide_affiche_sur_stdout_pas_stderr(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "help"])
    forge.main()
    captured = capsys.readouterr()
    assert len(captured.out) > 100
    assert captured.err == ""
