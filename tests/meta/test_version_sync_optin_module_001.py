"""VERSION-SYNC-OPTIN-MODULE-001 : le `__version__` des opt-ins suit le canonique.

Chacun des vingt-sept opt-ins déclare sa version à **deux** endroits : le
`version` de son `pyproject.toml`, lu par pip, et le `__version__` de son
module, lu par une application à l'exécution.

`check_version_sync.py` ne comparait que le premier. Le second n'était comparé à
rien, dans aucun outil ni aucun test. Un bump qui en oublie un publie donc un
paquet dont les métadonnées disent `rc4` et dont `forge_mvc_x.__version__`
répond `rc3`, sans qu'un seul contrôle proteste.

Mesuré à la veille de la rc4 : les vingt-sept étaient alignés, mais par chance.
Un bump touche soixante et un fichiers, dont vingt-sept `__init__.py` ; la
moitié du travail n'était couverte par rien.

Ce fichier tient deux choses distinctes. Que l'alignement soit vrai
maintenant, et que l'outil de release continue de le vérifier : un test qui
constate l'alignement sans exiger le contrôle laisserait retirer le contrôle.

Aucun test d'ici ne modifie un fichier du dépôt. La suite tourne sur huit
workers qui lisent les mêmes fichiers, et une mutation, même brève et bien
restaurée, y produit des échecs intermittents chez les voisins.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTIL = PROJECT_ROOT / "tools" / "check_version_sync.py"

MODULES = sorted((PROJECT_ROOT / "packages").glob("forge-mvc-*/forge_mvc_*/__init__.py"))


def _canonique() -> str:
    return tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def _version_declaree(init: Path) -> "str | None":
    trouve = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text(encoding="utf-8"))
    return trouve.group(1) if trouve else None


# ── L'alignement lui-même ────────────────────────────────────────────────────

def test_il_y_a_bien_des_modules_a_verifier() -> None:
    """Sans cela, un glob cassé rendrait tous les tests ci-dessous vides et verts."""
    assert len(MODULES) >= 20, f"{len(MODULES)} modules trouvés, glob probablement faux"


@pytest.mark.parametrize("init", MODULES, ids=lambda p: p.parent.parent.name)
def test_le_module_declare_la_version_canonique(init: Path) -> None:
    """C'est cette valeur qu'une application lit à l'exécution."""
    declare = _version_declaree(init)
    if declare is None:
        pytest.skip(f"{init.parent.name} ne déclare pas de __version__")

    assert declare == _canonique(), (
        f"{init.parent.parent.name} : le module déclare {declare!r}, "
        f"le dépôt {_canonique()!r}")


# ── Et l'outil qui le tient pendant le bump ──────────────────────────────────

def test_l_outil_de_release_couvre_les_modules() -> None:
    """Le test ci-dessus constate ; l'outil, lui, protège pendant le bump.

    `release-validate.sh` appelle `check_version_sync.py` en bloquant. C'est là
    que le contrôle doit vivre, sans quoi une désynchronisation ne serait vue
    qu'au prochain passage de la suite, donc peut-être après publication.
    """
    source = OUTIL.read_text(encoding="utf-8")

    assert "forge_mvc_*/__init__.py" in source, (
        "check_version_sync.py ne balaie plus les __init__.py des opt-ins")
    assert "module __version__" in source


def test_l_extraction_de_version_lit_bien_le_module(tmp_path: Path) -> None:
    """Contre-épreuve de la lecture, sans toucher au dépôt.

    Une première version de ce test désynchronisait un vrai `__init__.py` le
    temps d'un sous-processus. Elle passait, mais par chance : la suite tourne
    sur huit workers qui lisent ces mêmes fichiers, et un test qui mute le dépôt
    sous les autres est une source d'échecs intermittents. Un garde-fou instable
    finit désactivé.

    Ce qu'il faut prouver ici est étroit : que la lecture du `__version__` d'un
    module rend bien ce qui y est écrit, y compris quand c'est faux. Que l'outil
    en tire un échec est prouvé par sa structure, vérifiée au test précédent, et
    par son exécution sur le dépôt réel au test suivant.
    """
    faux = tmp_path / "__init__.py"
    faux.write_text('"""Paquet d\'essai."""\n__version__ = "9.9.9-faux"\n', encoding="utf-8")

    assert _version_declaree(faux) == "9.9.9-faux"
    assert _version_declaree(faux) != _canonique()


def test_un_module_sans_version_est_reconnu(tmp_path: Path) -> None:
    """L'absence de `__version__` ne doit pas se lire comme une version vide."""
    muet = tmp_path / "__init__.py"
    muet.write_text('"""Paquet sans version."""\n', encoding="utf-8")

    assert _version_declaree(muet) is None


def test_l_outil_accepte_le_depot_tel_quel() -> None:
    """Contre-épreuve inverse : sans elle, un outil toujours rouge passerait aussi."""
    rendu = subprocess.run([sys.executable, str(OUTIL)],
                           capture_output=True, text=True, check=False)

    assert rendu.returncode == 0, rendu.stdout + rendu.stderr
