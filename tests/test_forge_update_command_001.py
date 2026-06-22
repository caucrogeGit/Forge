"""Garde-fou FORGE-UPDATE-COMMAND-001.

Contrat public de la commande `forge update` :

- enregistrée dans le dispatcher CLI Forge ;
- aide affichée par `format_command_help("update")` ;
- `--dry-run` n'exécute pas pip et affiche la commande qui serait lancée ;
- `--pre` ajoute `--pre` à la commande pip ;
- la commande utilise `sys.executable` (reste dans le venv courant) ;
- détection pipx : si `sys.executable` est sous `pipx/venvs/`,
  n'appelle pas `subprocess.run` mais affiche `pipx upgrade forge-mvc` ;
- échec pip → exit code propagé non nul ;
- `cli/help.py` mentionne la commande ;
- `HELP_TEXTS_RICH["update"]` existe et couvre les modes/options.

Le test mock `subprocess.run` et `sys.executable` — aucun pip réel
n'est lancé pendant les tests.
"""
from __future__ import annotations

import sys

from cli import update as update_module
from cli.help import _HELP_TEMPLATE as HELP_TEMPLATE
from cli.help_dispatch import HELP_DESCRIPTIONS, HELP_TEXTS_RICH, format_command_help


# ── Aide CLI : le dispatcher reconnaît `update` ───────────────────────────────


def test_update_listed_in_help_template():
    """La ligne courte « forge update » apparaît dans `forge help`."""
    assert "update" in HELP_TEMPLATE
    assert "Met à jour Forge" in HELP_TEMPLATE


def test_help_texts_short_entry():
    assert "update" in HELP_DESCRIPTIONS
    assert "environnement courant" in HELP_DESCRIPTIONS["update"]


def test_help_texts_rich_entry():
    assert "update" in HELP_TEXTS_RICH
    rich = HELP_TEXTS_RICH["update"]
    # Couvre les modes et le cas pipx (parties structurantes du contrat)
    for marker in ("--pre", "--check", "--dry-run", "pipx", "sys.executable"):
        assert marker in rich, f"`{marker}` manquant dans HELP_TEXTS_RICH['update']."


def test_format_command_help_returns_update_text():
    text = format_command_help("update")
    assert text is not None
    assert "forge update" in text


# ── --help / -h dans update.main ──────────────────────────────────────────────


def test_main_help_flag_returns_0_and_prints(capsys):
    rc = update_module.main(["--help"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "forge update" in out


def test_main_short_h_flag_returns_0(capsys):
    rc = update_module.main(["-h"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "forge update" in out


# ── --dry-run : ne lance pas subprocess.run ───────────────────────────────────


def test_dry_run_does_not_call_subprocess(monkeypatch, capsys):
    called = {"n": 0}

    def fake_run(*args, **kwargs):
        called["n"] += 1
        raise AssertionError("subprocess.run ne doit pas être appelé en --dry-run")

    monkeypatch.setattr(update_module.subprocess, "run", fake_run)
    # Force la branche venv (pas pipx)
    monkeypatch.setattr(update_module, "_is_pipx_install", lambda: False)

    rc = update_module.main(["--dry-run"])
    out = capsys.readouterr().out

    assert rc == 0
    assert called["n"] == 0
    assert "[dry-run]" in out
    assert "pip install --upgrade" in out


def test_dry_run_pre_includes_pre_flag(monkeypatch, capsys):
    monkeypatch.setattr(update_module, "_is_pipx_install", lambda: False)
    rc = update_module.main(["--dry-run", "--pre"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "--pre" in out


# ── --pre dans _build_pip_command ─────────────────────────────────────────────


def test_build_pip_command_without_pre():
    cmd = update_module._build_pip_command(pre=False)
    assert cmd[0] == sys.executable
    assert "pip" in cmd and "install" in cmd and "--upgrade" in cmd
    assert "--pre" not in cmd
    assert cmd[-1] == "forge-mvc"


def test_build_pip_command_with_pre():
    cmd = update_module._build_pip_command(pre=True)
    assert "--pre" in cmd
    # --pre doit être avant le nom de package
    assert cmd.index("--pre") < cmd.index("forge-mvc")


# ── Détection pipx ───────────────────────────────────────────────────────────


def test_pipx_detection_true_when_sys_executable_under_pipx_venvs(monkeypatch):
    monkeypatch.setattr(
        update_module.sys, "executable",
        "/home/u/.local/share/pipx/venvs/forge-mvc/bin/python",
    )
    monkeypatch.setattr(update_module.os.path, "realpath", lambda p: p)
    assert update_module._is_pipx_install() is True


def test_pipx_detection_false_for_normal_venv(monkeypatch):
    monkeypatch.setattr(
        update_module.sys, "executable",
        "/home/u/Projets/Forge/.venv/bin/python",
    )
    monkeypatch.setattr(update_module.os.path, "realpath", lambda p: p)
    assert update_module._is_pipx_install() is False


def test_pipx_branch_shows_pipx_upgrade_and_does_not_call_pip(monkeypatch, capsys):
    monkeypatch.setattr(update_module, "_is_pipx_install", lambda: True)

    def fail_run(*a, **kw):
        raise AssertionError("subprocess.run ne doit pas être appelé en pipx")

    monkeypatch.setattr(update_module.subprocess, "run", fail_run)

    rc = update_module.main([])  # mode défaut
    out = capsys.readouterr().out

    # rc non-nul : on n'a PAS mis à jour, juste affiché la marche à suivre
    assert rc != 0
    assert "pipx upgrade forge-mvc" in out


def test_pipx_branch_with_pre_passes_pip_args_pre(monkeypatch, capsys):
    monkeypatch.setattr(update_module, "_is_pipx_install", lambda: True)
    monkeypatch.setattr(
        update_module.subprocess, "run",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("subprocess.run ne doit pas être appelé en pipx")
        ),
    )

    rc = update_module.main(["--pre"])
    out = capsys.readouterr().out

    assert rc != 0
    assert 'pipx upgrade forge-mvc --pip-args="--pre"' in out


# ── Branche venv : pip est lancé via sys.executable, exit code propagé ────────


class _FakeCompleted:
    def __init__(self, returncode: int):
        self.returncode = returncode


def test_venv_branch_calls_subprocess_with_sys_executable(monkeypatch, capsys):
    monkeypatch.setattr(update_module, "_is_pipx_install", lambda: False)

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return _FakeCompleted(0)

    monkeypatch.setattr(update_module.subprocess, "run", fake_run)

    rc = update_module.main([])
    assert rc == 0
    assert captured["cmd"][0] == sys.executable
    assert "forge-mvc" in captured["cmd"]


def test_venv_branch_propagates_pip_failure_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(update_module, "_is_pipx_install", lambda: False)
    monkeypatch.setattr(
        update_module.subprocess, "run",
        lambda *a, **kw: _FakeCompleted(42),
    )

    rc = update_module.main([])
    out = capsys.readouterr().out
    assert rc == 42
    assert "Erreur pip" in out


# ── --check : lecture seule, ne lance pas pip ─────────────────────────────────


def test_check_does_not_call_subprocess(monkeypatch, capsys):
    monkeypatch.setattr(update_module, "_is_pipx_install", lambda: False)
    monkeypatch.setattr(
        update_module.subprocess, "run",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("subprocess.run ne doit pas être appelé en --check")
        ),
    )

    rc = update_module.main(["--check"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Version installée" in out
    assert "pip install --upgrade" in out
