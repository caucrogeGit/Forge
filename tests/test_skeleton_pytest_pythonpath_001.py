"""SKELETON-PYTEST-PYTHONPATH-001 : un projet neuf échouait à son propre `make check`.

Constaté en jouant les chapitres « Mise en service » des références, dont 22 sur
26 font lancer `make check`. Sur un projet à peine créé par `forge new`, sans
que rien n'y soit fait :

    tests/test_smoke_001.py:12: from mvc.routes import router
    E   ModuleNotFoundError: No module named 'mvc'
    make: *** [Makefile:19: test] Error 2

La cause tient à une différence que rien n'annonçait. `python -m pytest` insère
le répertoire courant dans `sys.path`, le script console `pytest` ne le fait
pas, et c'est ce dernier que le `Makefile` lance. Les tests passaient donc sous
une forme et échouaient sous l'autre, ce qui rendait le défaut difficile à voir
et facile à croire résolu.

`pythonpath = .` dans `pytest.ini` fait tenir les deux formes.

Un garde-fou existait pourtant, `test_skeleton_ci_makefile_001.py`. Il vérifiait
que le `Makefile` **contient** ses cibles :

    assert gate in content, f"make check doit exécuter « {gate} »"

Il lisait le texte, il ne lançait rien. C'est la même leçon que le verdict pytest
lu dans la sortie plutôt que dans le code retour, et elle s'est répétée ici.
Celui-ci **exécute** donc pytest sur un projet reconstitué.

Le projet est reconstitué plutôt que créé par `forge new` : cette commande crée
un venv, installe des dépendances, appelle npm et openssl, soit plusieurs
minutes et le réseau, ce qui n'a pas sa place dans la suite. Seuls comptent ici
le `pytest.ini` livré et un import applicatif.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTEST_INI = PROJECT_ROOT / "skeleton" / "data" / "pytest.ini"


def _projet_reconstitue(racine: Path) -> None:
    """Le strict nécessaire : le `pytest.ini` du squelette, un paquet, un test."""
    (racine / "pytest.ini").write_text(PYTEST_INI.read_text(encoding="utf-8"),
                                       encoding="utf-8")
    mvc = racine / "mvc"
    mvc.mkdir()
    (mvc / "__init__.py").write_text("", encoding="utf-8")
    (mvc / "routes.py").write_text("router = object()\n", encoding="utf-8")
    tests = racine / "tests"
    tests.mkdir()
    (tests / "test_smoke_001.py").write_text(
        "from mvc.routes import router\n\n\n"
        "def test_le_routeur_se_charge():\n    assert router is not None\n",
        encoding="utf-8")


def _lancer(racine: Path, *, module: bool) -> subprocess.CompletedProcess[str]:
    commande = ([sys.executable, "-m", "pytest", "-q"] if module
                else [str(Path(sys.executable).parent / "pytest"), "-q"])
    return subprocess.run(commande, cwd=racine, capture_output=True, text=True)


# ── Le contrat du fichier livré ──────────────────────────────────────────────

def test_le_squelette_declare_la_racine_importable() -> None:
    contenu = PYTEST_INI.read_text(encoding="utf-8")

    assert "pythonpath = ." in contenu


def test_le_motif_est_ecrit_a_cote_de_la_ligne() -> None:
    """Sans le motif, la ligne passera pour superflue au prochain nettoyage."""
    contenu = PYTEST_INI.read_text(encoding="utf-8")

    assert "sys.path" in contenu
    assert "Makefile" in contenu


# ── Le comportement, éprouvé et non lu ───────────────────────────────────────

@pytest.mark.parametrize("module", [True, False],
                         ids=["python -m pytest", "script console pytest"])
def test_les_deux_invocations_trouvent_le_paquet_applicatif(
    module: bool, tmp_path: Path,
) -> None:
    """Le cas mesuré : l'une passait, l'autre non, et le Makefile lançait l'autre."""
    _projet_reconstitue(tmp_path)

    fini = _lancer(tmp_path, module=module)

    assert fini.returncode == 0, (
        f"pytest a refusé un projet neuf :\n{fini.stdout}\n{fini.stderr}")
    assert "ModuleNotFoundError" not in (fini.stdout + fini.stderr)


def test_sans_la_ligne_le_script_console_echoue(tmp_path: Path) -> None:
    """Preuve que le garde éprouve bien quelque chose.

    Un test qui passerait aussi sans le correctif ne garderait rien : celui-ci
    retire la ligne et vérifie que le défaut revient.
    """
    _projet_reconstitue(tmp_path)
    ini = tmp_path / "pytest.ini"
    ini.write_text(
        "\n".join(l for l in ini.read_text(encoding="utf-8").splitlines()
                  if not l.startswith("pythonpath")),
        encoding="utf-8")

    fini = _lancer(tmp_path, module=False)

    assert fini.returncode != 0
    assert "ModuleNotFoundError" in (fini.stdout + fini.stderr)
