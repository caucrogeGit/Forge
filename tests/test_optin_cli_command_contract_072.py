"""Garde-fous ADR-072 — contrat des commandes CLI des opt-ins (retour terrain 016 F39/F40).

Vérifie que `dispatch_optin` :
- intercepte `-h`/`--help` avant tout effet (F40) ;
- amorce la config projet (`load_project_config`) avant le handler quand la
  commande déclare `config: True` (F39), et pas sinon ;
et que `forge-mvc-sessions-db` marque `sessions:gc` (adossé à la base) mais pas
`sessions:init` (copie de fichiers).
"""
from __future__ import annotations

import sys
import types

import pytest

from cli.commands import optin_dispatch


def _install_fake_command(monkeypatch, *, needs_config: bool) -> list[tuple[str, object]]:
    """Injecte une commande opt-in factice et retourne la liste des appels observés."""
    calls: list[tuple[str, object]] = []
    module = types.ModuleType("fake_optin_module_072")

    def main(args: list[str]) -> int:
        calls.append(("handler", list(args)))
        return 0

    module.main = main  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fake_optin_module_072", module)

    cmd = optin_dispatch.OptinCommand(
        module="fake_optin_module_072",
        package="fake-pkg",
        needs_config=needs_config,
    )
    monkeypatch.setattr(optin_dispatch, "_discovered_cache", {"fake:cmd": cmd})
    return calls


def test_help_is_intercepted_without_running_effect(monkeypatch, capsys):
    """F40 : `--help` affiche l'aide et n'exécute jamais le handler."""
    calls = _install_fake_command(monkeypatch, needs_config=False)
    handled = optin_dispatch.dispatch_optin("fake:cmd", ["fake:cmd", "--help"])
    assert handled is True
    assert calls == [], "le handler ne doit pas être appelé sur --help"
    assert "fake:cmd" in capsys.readouterr().out


def test_short_help_flag_also_intercepted(monkeypatch, capsys):
    calls = _install_fake_command(monkeypatch, needs_config=False)
    optin_dispatch.dispatch_optin("fake:cmd", ["fake:cmd", "-h"])
    assert calls == []


def test_config_flag_bootstraps_before_handler(monkeypatch):
    """F39 : `config: True` amorce load_project_config AVANT le handler."""
    calls = _install_fake_command(monkeypatch, needs_config=True)
    import cli.project.project_config as pc

    def fake_load(*_a, **_k):
        calls.append(("config", None))
        return types.ModuleType("cfg")

    monkeypatch.setattr(pc, "load_project_config", fake_load)
    optin_dispatch.dispatch_optin("fake:cmd", ["fake:cmd"])
    assert [c[0] for c in calls] == ["config", "handler"], (
        "la config projet doit être amorcée avant le handler"
    )


def test_no_config_flag_skips_bootstrap(monkeypatch):
    calls = _install_fake_command(monkeypatch, needs_config=False)
    import cli.project.project_config as pc

    monkeypatch.setattr(
        pc, "load_project_config",
        lambda *_a, **_k: calls.append(("config", None)),
    )
    optin_dispatch.dispatch_optin("fake:cmd", ["fake:cmd"])
    assert calls == [("handler", [])], "aucun amorçage config sans le drapeau"


def test_spec_parses_config_flag():
    """La table COMMANDS peut déclarer `config` (défaut False)."""
    pytest.importorskip("forge_mvc_sessions_db")
    cmds = optin_dispatch.all_optin_commands()
    assert cmds["sessions:gc"].needs_config is True
    assert cmds["sessions:init"].needs_config is False


def test_sessions_commands_declare_config_correctly():
    pytest.importorskip("forge_mvc_sessions_db")
    from forge_mvc_sessions_db.commands import COMMANDS

    assert COMMANDS["sessions:gc"].get("config") is True
    assert "config" not in COMMANDS["sessions:init"]


# Audit transverse (retour terrain 016, suite F39) : toute commande d'opt-in qui
# ouvre une connexion BDD inconditionnellement doit déclarer config:True.
_DB_BACKED_COMMANDS = frozenset({
    "sessions:gc",     # DELETE des sessions expirées
    "iot:listen",      # INSERT dans iot_events
    "video:upload",    # INSERT ligne vidéo
    "video:process",   # UPDATE statut/poster/MP4
    "video:cleanup",   # DELETE lignes failed
})

# Commandes qui ne connectent pas (copie de fichiers, diagnostic statique,
# publication MQTT) : elles ne doivent pas forcer la config d'un projet.
_NON_DB_COMMANDS = frozenset({
    "sessions:init", "iot:init", "iot:doctor", "iot:simulate",
    "video:init", "video:doctor", "audio:doctor",
    "images:init", "audit:init", "settings:init", "jobs:init",
    "notifications:init", "admin:init", "admin:doctor",
})


def test_db_backed_optin_commands_declare_config():
    cmds = optin_dispatch.all_optin_commands()
    for name in _DB_BACKED_COMMANDS:
        if name in cmds:  # opt-in installé dans l'environnement de test
            assert cmds[name].needs_config is True, (
                f"{name} ouvre une connexion BDD : doit déclarer config:True (F39)."
            )


def test_non_db_optin_commands_do_not_declare_config():
    cmds = optin_dispatch.all_optin_commands()
    for name in _NON_DB_COMMANDS:
        if name in cmds:
            assert cmds[name].needs_config is False, (
                f"{name} ne connecte pas la BDD : ne doit pas forcer la config projet."
            )
