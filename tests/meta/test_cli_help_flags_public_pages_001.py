"""Garde-fou CLI-HELP-FLAGS-PUBLIC-PAGES-001.

Vérifie que les 5 commandes Pages publiques ont une aide enrichie
cohérente et n'exécutent pas leur génération avec --help / -h :

    make:public-page
    make:public-list
    make:public-show
    make:public-form
    make:public-contact

Note de cadrage : le ticket mentionnait `make:public-detail` et
`make:public-nav` ; ces noms n'existent pas dans le code
(cf. forge --help et docs/history/audits/cli-help-flags-audit-001.md).
Les vrais noms sont `make:public-show` et `make:public-contact`.

L'interception centrale (CLI-HELP-FLAGS-DISPATCHER-001) reste responsable
du fait que -h/--help ne lance rien ; ce test garantit que le contenu de
l'aide est utile et propre à chaque commande.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


PUBLIC_COMMANDS = [
    "make:public-page",
    "make:public-list",
    "make:public-show",
    "make:public-form",
    "make:public-contact",
]


# Mot-clé propre à chaque commande (au moins un doit apparaître dans l'aide).
COMMAND_KEYWORDS = {
    "make:public-page":    ["page publique"],
    "make:public-list":    ["liste publique", "list"],
    "make:public-show":    ["fiche publique", "show", "détail", "detail"],
    "make:public-form":    ["formulaire public", "form"],
    "make:public-contact": ["page de contact", "contact"],
}


# Marqueurs spécifiques aux SORTIES réelles des commandes (jamais présents
# dans le texte d'aide). Ne pas bannir les mots normaux de documentation
# comme « génère » ou « créé » qui peuvent apparaître dans les descriptions.
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[PRÉSERVÉ]",
    "Dossier prêt",
    "Aucun écrasement effectué",
    "déjà existante",
    "Route :",
    "Template :",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestPublicCommandsExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande."""

    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestPublicCommandsHelpStructure:
    """Chaque aide contient les sections attendues."""

    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )

    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )


class TestPublicCommandsHelpHasKeyword:
    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide."
        )


class TestPublicCommandsNoSideEffects:
    """L'enrichissement n'a pas réintroduit d'effet de bord."""

    @pytest.mark.parametrize("command", PUBLIC_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )
