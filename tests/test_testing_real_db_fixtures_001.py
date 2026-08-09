"""Les fixtures serveur réel ont une source unique (TESTING-REAL-DB-FIXTURES-001).

Elles vivaient dans `tests/db/conftest.py`, donc hors de portée des tests des
paquets opt-in, qui sont sous `packages/*/tests/`. Chacun de ces paquets avait
répondu en réécrivant son propre adaptateur de connexion à la main. Deux façons
officielles de monter une base de test contredisaient le principe 11, et la
seconde court-circuitait la vraie couche d'accès `core.database.db`, donc la
qualification d'erreur de Forge.

Ce garde-fou fige le déplacement vers `forge-mvc-testing` (ADR-041) et empêche
qu'une définition concurrente réapparaisse.

Les deux propriétés qui comptent sont vérifiées **par collecte réelle**, dans un
pytest lancé en sous-processus sur un fichier sonde écrit hors du dépôt : que
les fixtures soient visibles depuis n'importe où, et que chaque marqueur
sélectionne le serveur attendu. Les introspecter aurait voulu dire lire un
attribut privé de pytest, qui a déjà changé de nom d'une version à l'autre.
"""
from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from pathlib import Path

import pytest

from forge_mvc_testing import real_db

pytestmark = pytest.mark.meta

_RACINE = Path(__file__).resolve().parent.parent
_CONFTEST_DB = _RACINE / "tests" / "db" / "conftest.py"

_SONDE = '''
import pytest

# Les trois fixtures directes ne portent **pas** de marqueur : c'est le fichier
# qui déclare le sien, comme tout fichier d'intégration. Seule `real_backend_db`
# marque ses cas elle-même, par ses paramètres.
pytestmark = pytest.mark.db


def test_les_trois_directes(real_db, real_pg_db, real_mssql_db):
    pass


def test_la_parametree(real_backend_db):
    pass
'''

#: Fixtures serveur réel qui n'apportent aucun marqueur au test qui les demande.
_FIXTURES_DIRECTES = {"real_db", "real_pg_db", "real_mssql_db"}
_MARQUEURS_BASE = {"db", "db_pg", "db_mssql"}


def _collecter(chemin_sonde: Path, *arguments: str) -> str:
    """Collecte la sonde dans un pytest séparé et retourne sa sortie."""
    resultat = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "-c", "pytest.ini", "--rootdir=.",
            "-q", "--collect-only", "-p", "no:randomly",
            str(chemin_sonde), *arguments,
        ],
        cwd=_RACINE,
        capture_output=True,
        text=True,
    )
    return resultat.stdout + resultat.stderr


@pytest.fixture
def sonde(tmp_path: Path) -> Path:
    """Fichier de test hors du dépôt, donc sans conftest local pour l'aider."""
    chemin = tmp_path / "test_sonde_real_db.py"
    chemin.write_text(_SONDE, encoding="utf-8")
    return chemin


def test_les_quatre_fixtures_sont_visibles_hors_du_depot(sonde: Path) -> None:
    """Un test posé n'importe où trouve les quatre fixtures.

    C'est la propriété qui manquait : sous `tests/db/conftest.py`, elles
    n'existaient que pour ce dossier, et les tests des paquets opt-in devaient
    se débrouiller autrement.
    """
    sortie = _collecter(sonde)
    assert "fixture 'real_db' not found" not in sortie
    assert "error" not in sortie.lower(), sortie
    assert "4 tests collected" in sortie, sortie


@pytest.mark.parametrize(
    ("marqueur", "cas_attendu"),
    [
        ("db_pg", "test_la_parametree[postgres]"),
        ("db_mssql", "test_la_parametree[mssql]"),
    ],
)
def test_chaque_marqueur_selectionne_son_serveur(
    sonde: Path, marqueur: str, cas_attendu: str
) -> None:
    """Les jobs `db_pg` et `db_mssql` de la CI ne prennent chacun que leur cas.

    C'est ce qui permet d'écrire un test d'intégration **une fois** et de
    l'exécuter sur les trois serveurs.
    """
    sortie = _collecter(sonde, "-m", marqueur)
    assert cas_attendu in sortie, sortie
    assert "1/4 tests collected" in sortie, sortie


def test_aucun_cas_ne_fuit_dans_le_job_sans_base(sonde: Path) -> None:
    """`-m "not db"` ne doit rien retenir : les trois cas portent le marqueur `db`.

    Sans cela, le job de CI qui tourne sans aucun serveur tenterait une
    connexion et échouerait, ou pire, passerait sans rien vérifier.
    """
    sortie = _collecter(sonde, "-m", "not db")
    assert "no tests collected" in sortie, sortie


def _marqueurs_du_decorateur(noeud: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    noms: set[str] = set()
    for decorateur in noeud.decorator_list:
        cible = decorateur.func if isinstance(decorateur, ast.Call) else decorateur
        while isinstance(cible, ast.Attribute):
            noms.add(cible.attr)
            cible = cible.value
    return noms


def test_aucun_test_ne_demande_un_serveur_sans_marqueur() -> None:
    """Demander `real_db` sans déclarer `db`, c'est écrire un test qui ne tourne jamais.

    Les trois fixtures directes n'apportent aucun marqueur. Un test qui les
    demande sans en déclarer un est collecté dans le job de CI qui n'a aucun
    serveur, où `FORGE_REQUIRE_DB` n'est pas posé : la fixture le **saute**, en
    silence, et il compte comme vert. C'est la forme la plus discrète du piège
    « un saut n'est pas un succès ».

    `real_backend_db` n'est pas concernée, ses paramètres portent leurs marqueurs.
    """
    coupables: list[str] = []
    fichiers = [*_RACINE.glob("tests/**/*.py"), *_RACINE.glob("packages/*/tests/**/*.py")]
    for chemin in fichiers:
        source = chemin.read_text(encoding="utf-8")
        try:
            arbre = ast.parse(source)
        except SyntaxError:  # pragma: no cover — un fichier cassé échoue ailleurs
            continue
        module_marque = "pytestmark" in source and "mark.db" in source
        for noeud in ast.walk(arbre):
            if not isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not noeud.name.startswith("test_"):
                continue
            demandees = {arg.arg for arg in noeud.args.args} & _FIXTURES_DIRECTES
            if not demandees:
                continue
            if module_marque or (_marqueurs_du_decorateur(noeud) & _MARQUEURS_BASE):
                continue
            coupables.append(
                f"{chemin.relative_to(_RACINE)}:{noeud.lineno} {noeud.name} "
                f"demande {sorted(demandees)} sans marqueur de base"
            )
    assert not coupables, "\n".join(coupables)


def test_le_conftest_db_ne_definit_plus_de_fixture() -> None:
    """`tests/db/conftest.py` réutilise, il ne redéfinit pas.

    Une redéfinition locale masquerait silencieusement celle du plugin : les
    tests de `tests/db/` et ceux des paquets exerceraient alors deux montages
    différents, ce qui est exactement la situation que ce ticket supprime.
    """
    source = _CONFTEST_DB.read_text(encoding="utf-8")
    assert "@pytest.fixture" not in source, (
        "tests/db/conftest.py redéfinit une fixture : la source unique est "
        "forge_mvc_testing.real_db"
    )


def test_chaque_backend_parametre_a_sa_fixture() -> None:
    """La table de correspondance ne peut pas pointer vers une fixture absente."""
    for nom_fixture in real_db._FIXTURE_PAR_BACKEND.values():
        assert hasattr(real_db, nom_fixture), (
            f"_FIXTURE_PAR_BACKEND pointe vers {nom_fixture}, qui n'existe pas"
        )


def test_le_contrat_de_saut_est_conserve() -> None:
    """Sauté en local, en échec sous FORGE_REQUIRE_DB : la couche base n'est jamais verte par défaut."""
    source = inspect.getsource(real_db)
    for garde in ("_REQUIRE_DB", "_REQUIRE_DB_PG", "_REQUIRE_DB_MSSQL"):
        assert f"if {garde}:" in source, f"le garde {garde} a disparu"
    assert source.count("pytest.fail(message") == 3
    assert source.count("pytest.skip(message") == 3
