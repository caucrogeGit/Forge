"""Garde-fou CLI-HELP-HIDDEN-COMMANDS-001.

Vérifie que toute commande acceptée par forge.py apparaît dans
forge --help. Empêche les commandes cachées de se ré-accumuler.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"

# Commandes volontairement cachées (whitelist) - vide pour le moment
HIDDEN_WHITELIST: set[str] = set()


def _commands_in_code() -> set[str]:
    text = FORGE_PY.read_text(encoding="utf-8")
    commands = set()
    for m in re.finditer(r'command\s*==\s*["\']([\w:.-]+)["\']', text):
        commands.add(m.group(1))
    for m in re.finditer(r'command\s+in\s+[\(\{]([^)}]+)[\)\}]', text):
        for s in re.findall(r'["\']([\w:.-]+)["\']', m.group(1)):
            commands.add(s)
    # ADR-059 : les commandes opt-in et les commandes du cœur déléguées sont
    # dispatchées via des tables centrales, plus uniquement par le if-chain.
    from forge import CORE_COMMANDS

    from cli.commands.optin_dispatch import OPTIN_COMMANDS

    commands |= set(OPTIN_COMMANDS) | set(CORE_COMMANDS)
    return commands


def _commands_in_help() -> set[str]:
    result = subprocess.run(
        [sys.executable, str(FORGE_PY), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    commands = set()
    for line in result.stdout.split("\n"):
        # Format général "  commande:sub        description"
        # Inclut les chiffres pour i18n, v2 etc.
        m = re.match(r"^  ([a-z][a-z0-9:-]*(?::[a-z0-9-]+)*)", line)
        if m:
            commands.add(m.group(1))
        # Format spécial "  new <NomProjet>"
        m = re.match(r"^  ([a-z]+)\s+<", line)
        if m:
            commands.add(m.group(1))
    return commands


def test_all_code_commands_appear_in_help():
    code = _commands_in_code()
    help_cmds = _commands_in_help()
    missing = (code - help_cmds) - HIDDEN_WHITELIST

    if missing:
        raise AssertionError(
            f"{len(missing)} commande(s) du code absente(s) de --help :\n"
            + "\n".join(f"  - {c}" for c in sorted(missing))
            + "\n\nSoit ajouter dans cli/_support/help.py, soit ajouter à HIDDEN_WHITELIST."
        )


def test_no_help_commands_phantom():
    """Aucune commande dans --help qui ne soit pas acceptée par le code."""
    code = _commands_in_code()
    help_cmds = _commands_in_help()
    phantom = help_cmds - code

    # Méta-commandes qui ne passent pas par le dispatch
    METACOMMANDS = {"help", "--help", "-h", "version", "--version", "forge"}
    phantom -= METACOMMANDS

    if phantom:
        raise AssertionError(
            f"{len(phantom)} commande(s) annoncée(s) dans --help mais "
            f"absente(s) du code :\n"
            + "\n".join(f"  - {c}" for c in sorted(phantom))
        )
