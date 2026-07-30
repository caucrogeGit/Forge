"""RELEASE-VALIDATE-INTERPRETER-001 : la validation doit porter sur le bon Python.

Le script résolvait `python3` depuis le `PATH` et se contentait de vérifier
qu'il existe. Or il en existe un sur toute machine : lancé sans venv actif, il
validait donc l'interpréteur du système, où ni Forge ni l'outillage ne sont
installés.

Mesuré sur une validation réelle de la rc3, deux échecs sur trois étaient des
faux positifs de cette nature, un module d'opt-in et mkdocs déclarés absents
alors qu'ils sont installés dans le venv du projet.

Le sens inverse est plus grave et n'a pas encore été rencontré : un interpréteur
portant une version **ancienne** de Forge donnerait un feu vert sur autre chose
que ce qu'on s'apprête à publier. Une porte de release qui peut se tromper
d'environnement ne garde rien.

Trois contrôles, dans cet ordre.

- La **distribution** `forge-mvc` doit être installée, et non simplement le
  module importable : lancé depuis la racine du dépôt, `python -c` ajoute le
  répertoire courant au chemin, si bien que n'importe quel interpréteur importe
  `core`. Ce piège a été rencontré en écrivant ce garde, dont la première
  version passait pour cette raison.
- Sa version doit être celle du `pyproject.toml`, sinon la validation porte sur
  autre chose que la release.
- L'outillage que le script appelle doit être présent.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = PROJECT_ROOT / "tools" / "release-validate.sh"


@pytest.fixture(scope="module")
def source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_le_script_existe() -> None:
    assert SCRIPT.is_file()


def test_la_distribution_est_verifiee_pas_le_simple_import(source: str) -> None:
    """`import core` réussit depuis la racine avec n'importe quel interpréteur."""
    assert 'importlib.metadata' in source
    assert 'm.version("forge-mvc")' in source


def test_la_version_installee_doit_etre_celle_du_depot(source: str) -> None:
    """Le cas dangereux : un feu vert donné sur une version plus ancienne."""
    assert "_FORGE_REPO_VERSION" in source
    assert "porte forge-mvc" in source


def test_l_outillage_appele_est_verifie(source: str) -> None:
    """Le script lance pytest, mkdocs et ruff : leur absence doit être dite tôt."""
    assert "for _outil in pytest mkdocs ruff" in source


def test_les_messages_disent_quoi_faire(source: str) -> None:
    """Un refus sans remède fait perdre le temps qu'il prétend économiser."""
    assert "source .venv/bin/activate" in source
    assert "PYTHON=.venv/bin/python" in source


def test_le_garde_precede_les_etapes_couteuses(source: str) -> None:
    """Découvrir l'erreur après vingt minutes de tests serait absurde."""
    position_garde = source.index("_FORGE_INSTALLED=")
    for etape in ("--- Exécution des tests", "--- MkDocs"):
        assert position_garde < source.index(etape), (
            f"le garde d'interpréteur passe après « {etape} »"
        )


def test_l_ancien_controle_seul_ne_subsiste_pas(source: str) -> None:
    """`command -v python3` ne prouve rien : il ne doit plus conclure seul."""
    position_command = source.index('command -v "$PYTHON_BIN"')
    position_probe = source.index("_FORGE_INSTALLED=")

    assert position_command < position_probe, (
        "la vérification d'existence doit rester, mais être suivie du contrôle réel"
    )
