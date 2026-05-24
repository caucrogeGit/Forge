"""Garde-fou CLI-HELP-FLAGS-ENTITY-MODEL-CRUD-001.

Vérifie que les 5 commandes du cycle entité / modèle / CRUD ont une
aide enrichie cohérente et n'exécutent pas leur logique métier avec
--help / -h :

    entity:validate
    build:model
    check:model
    make:crud
    make:pivot-crud

L'interception centrale (CLI-HELP-FLAGS-DISPATCHER-001) reste responsable
du fait que -h/--help ne lance rien. Ce test garantit que :
1. l'aide est utile et propre à chaque commande ;
2. les commandes qui ÉCRIVENT des fichiers (build:model, make:crud,
   make:pivot-crud) signalent clairement ce risque.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


ENTITY_MODEL_CRUD_COMMANDS = [
    "entity:validate",
    "build:model",
    "check:model",
    "make:crud",
    "make:pivot-crud",
]

# Commandes qui écrivent réellement des fichiers.
WRITING_COMMANDS = [
    "build:model",
    "make:crud",
    "make:pivot-crud",
]


# Mot-clé propre à chaque commande (au moins un doit apparaître dans l'aide).
COMMAND_KEYWORDS = {
    "entity:validate": ["entité", "validation", "entites"],
    "build:model":     ["modèle", "_base.py", "modeles"],
    "check:model":     ["contrôle", "cohérence", "controle"],
    "make:crud":       ["crud"],
    "make:pivot-crud": ["pivot", "many-to-many", "many_to_many"],
}


# Marqueurs spécifiques aux SORTIES réelles des commandes. Choisis pour
# ne pas coïncider avec le vocabulaire normal de description : on tolère
# « génère », « créé », « fichier », « modèle », « CRUD » comme termes
# de doc et on cible les marqueurs uniques d'exécution (tags, en-têtes
# de rapport, lignes de résumé).
SIDE_EFFECT_MARKERS = [
    "[OK]",
    "[ERREUR]",
    "[INFO]",
    "[PRÉSERVÉ]",
    "[ÉCRIT]",
    "[CRÉÉ]",
    "[DRY-RUN]",
    "Modele valide —",
    "Aucun fichier modifié.",
    "Aucun fichier créé.",
    "Fichiers qui seraient générés :",
    "régénéré(s),",
    "préservé(s).",
]


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


class TestEntityModelCrudExitZero:
    """`--help` et `-h` retournent 0 pour chaque commande."""

    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0. "
            f"stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0. "
            f"stderr={result.stderr!r}"
        )


class TestEntityModelCrudHelpStructure:
    """Chaque aide contient les sections attendues."""

    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_has_usage_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Usage:" in out, f"{command} : section Usage: manquante."
        assert f"forge {command}" in out, (
            f"{command} : l'aide doit citer `forge {command}`."
        )

    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_has_description_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Description:" in out, (
            f"{command} : section Description: manquante."
        )

    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_has_options_section(self, command: str):
        out = _run_forge(command, "--help").stdout
        assert "Options:" in out, (
            f"{command} : section Options: manquante."
        )
        assert "--help" in out, (
            f"{command} : le flag --help doit être documenté."
        )

    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_mentions_no_execution(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        assert "sans exécuter" in out, (
            f"{command} : l'aide doit rappeler que --help n'exécute rien."
        )


class TestEntityModelCrudHelpHasKeyword:
    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_mentions_command_specific_keyword(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        keywords = [k.lower() for k in COMMAND_KEYWORDS[command]]
        found = [k for k in keywords if k in out]
        assert found, (
            f"{command} : aucun mot-clé attendu trouvé ({keywords}) "
            f"dans l'aide."
        )


class TestWritingCommandsAdvertiseFileWrite:
    """Les 3 commandes qui écrivent doivent l'indiquer dans leur aide."""

    @pytest.mark.parametrize("command", WRITING_COMMANDS)
    def test_help_mentions_write_or_regenerate(self, command: str):
        out = _run_forge(command, "--help").stdout.lower()
        write_markers = [
            "écrit", "régénère", "régénéré", "génère",
            "write-if-new", "écrase", "écraser",
            "peut être modifié",
        ]
        found = [m for m in write_markers if m in out]
        assert found, (
            f"{command} --help doit signaler qu'elle peut écrire des "
            f"fichiers (chercher un de : {write_markers}). Sortie : "
            f"{out[:300]!r}"
        )


class TestEntityModelCrudNoSideEffects:
    """L'enrichissement n'a pas réintroduit d'effet de bord."""

    @pytest.mark.parametrize("command", ENTITY_MODEL_CRUD_COMMANDS)
    def test_no_execution_marker_in_output(self, command: str):
        result = _run_forge(command, "--help")
        combined = result.stdout + result.stderr
        offenders = [m for m in SIDE_EFFECT_MARKERS if m in combined]
        assert not offenders, (
            f"{command} : marqueurs d'exécution trouvés ({offenders}). "
            f"Sortie : {combined!r}"
        )
