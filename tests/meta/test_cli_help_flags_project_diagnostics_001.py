"""Garde-fou CLI-HELP-FLAGS-PROJECT-DIAGNOSTICS-001.

Vérifie que les 4 commandes de diagnostic projet ont une aide enrichie
cohérente et n'exécutent pas leur logique métier avec --help / -h :

    doctor
    project:check
    project:audit
    routes:list

Ces commandes sont importantes pour la prise en main : elles décrivent
l'état d'un projet Forge sans rien modifier. Le test garantit que :
1. l'aide est utile et propre à chaque commande ;
2. les marqueurs réels de sortie n'apparaissent jamais dans l'aide.

L'interception centrale (CLI-HELP-FLAGS-DISPATCHER-001) reste responsable
du fait que -h/--help ne lance rien.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


PROJECT_DIAG_COMMANDS = [
    "doctor",
    "project:check",
    "project:audit",
    "routes:list",
]


# Mot-clé propre à chaque commande (au moins un doit apparaître dans l'aide).
COMMAND_KEYWORDS = {
    "doctor":        ["diagnostic", "doctor"],
    "project:check": ["cohérence", "check", "conventions"],
    "project:audit": ["audit", "rapport"],
    "routes:list":   ["routes", "liste"],
}


# Marqueurs spécifiques aux SORTIES réelles des commandes. Choisis pour
# ne PAS coïncider avec le vocabulaire normal de description. Le mot
# « routes » (minuscule) reste autorisé dans routes:list. Les noms de
# commandes Forge peuvent apparaître dans l'aide, mais pas leur en-tête
# de rapport (« Forge doctor — », tiret long).
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[WARN]",
    "[FAIL]",
    "[SKIP]",
    "[INFO]",
    "Forge doctor —",
    "Forge project:check —",
    "Forge project:audit —",
    "Tout est conforme.",
    "Projet non conforme.",
    "Projet conforme avec avertissements.",
    "Aucune route déclarée.",
    "avertissement(s),",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestProjectDiagCommandsExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande."""

    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestProjectDiagCommandsHelpStructure:
    """Chaque aide contient les sections attendues."""

    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )

    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )


class TestProjectDiagCommandsHelpHasKeyword:
    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide."
        )


class TestProjectDiagCommandsNoSideEffects:
    """L'enrichissement n'a pas réintroduit d'effet de bord."""

    @pytest.mark.parametrize("command", PROJECT_DIAG_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )


class TestProjectDiagCommandsDistinguishThemselves:
    """Les aides doivent renvoyer entre elles pour clarifier les rôles."""

    def test_doctor_mentions_project_check_or_project_audit(self):
        out = _run_forge("doctor", "--help").stdout.lower()
        assert ("project:check" in out) or ("project:audit" in out), (
            "L'aide de doctor doit renvoyer à project:check ou "
            "project:audit pour clarifier la différence."
        )

    def test_project_check_mentions_doctor_or_project_audit(self):
        out = _run_forge("project:check", "--help").stdout.lower()
        assert ("doctor" in out) or ("project:audit" in out), (
            "L'aide de project:check doit renvoyer à doctor ou "
            "project:audit pour clarifier la différence."
        )

    def test_project_audit_mentions_doctor_or_project_check(self):
        out = _run_forge("project:audit", "--help").stdout.lower()
        assert ("doctor" in out) or ("project:check" in out), (
            "L'aide de project:audit doit renvoyer à doctor ou "
            "project:check pour clarifier la différence."
        )
