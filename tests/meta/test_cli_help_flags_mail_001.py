"""Garde-fou CLI-HELP-FLAGS-MAIL-001.

Vérifie que les 4 commandes Mail restantes (mail:init étant déjà
couvert par CLI-HELP-FLAGS-INIT-COMMANDS-001) ont une aide enrichie
cohérente et n'exécutent pas leur logique métier avec --help / -h :

    mail:test
    mail:render
    mail:doctor
    mail:logs

L'interception centrale (CLI-HELP-FLAGS-DISPATCHER-001) reste responsable
du fait que -h/--help ne lance rien ; ce test garantit que le contenu de
l'aide est utile et propre à chaque commande, et qu'aucun marqueur de
sortie réelle n'apparaît dans l'aide.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


MAIL_COMMANDS = [
    "mail:test",
    "mail:render",
    "mail:doctor",
    "mail:logs",
]


# Mot-clé propre à chaque commande (au moins un doit apparaître dans l'aide).
COMMAND_KEYWORDS = {
    "mail:test":   ["test", "mail"],
    "mail:render": ["render", "template", "rendu"],
    "mail:doctor": ["doctor", "diagnostic", "diagnostique", "configuration"],
    "mail:logs":   ["logs", "storage", "mail_log"],
}


# Marqueurs spécifiques aux SORTIES réelles des commandes mail. Choisis
# pour ne PAS coïncider avec le vocabulaire normal de description (ex. on
# bannit « Mail envoyé via » et pas « envoyer un mail » qui apparaît dans
# l'aide de mail:test).
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[PRÉSERVÉ]",
    "[FAIL]",
    "[WARN]",
    "[SKIP]",
    "[INFO]",
    "Mail envoyé via",
    "Mail non envoyé",
    "Aucun enregistrement dans mail_log",
    "Forge mail:doctor",  # en-tête de rapport
    "avertissement(s),",  # ligne de résumé doctor
    "Dossier prêt",
    "[TEXTE]",            # mail:render
    "Échec de l'envoi",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestMailCommandsExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande."""

    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestMailCommandsHelpStructure:
    """Chaque aide contient les sections attendues."""

    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )

    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )


class TestMailCommandsHelpHasKeyword:
    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide."
        )


class TestMailCommandsNoSideEffects:
    """L'enrichissement n'a pas réintroduit d'effet de bord."""

    @pytest.mark.parametrize("command", MAIL_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )


class TestMailTestExplicitsRealSendRisk:
    """mail:test doit clarifier qu'un envoi réel reste possible."""

    def test_help_mentions_envoi_reel_or_smtp(self):
        out = _run_forge("mail:test", "--help").stdout.lower()
        risk_markers = ["envoi réel", "smtp", "mail_enabled"]
        found = [m for m in risk_markers if m in out]
        assert found, (
            "mail:test --help doit clarifier qu'un envoi réel est "
            f"possible (chercher un de : {risk_markers}). Sortie : "
            f"{out!r}"
        )
