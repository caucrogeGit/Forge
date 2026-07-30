"""TEST-DB-BACKEND-MARKERS-001 : un test qui exige PostgreSQL ou SQL Server le déclare.

`TEST-DB-COLLECT-GUARD-001` refuse qu'un test `db` requis soit sauté quand
`FORGE_REQUIRE_DB*` est posé, sans quoi un job d'intégration resterait vert avec
zéro test exécuté. La convention qui l'accompagne veut qu'un test visant un
autre serveur que MariaDB porte **aussi** son marqueur de backend, faute de quoi
le job MariaDB le compte comme requis et échoue de l'avoir sauté.

Cette convention ne vivait que dans un commentaire de `conftest.py`. Elle a été
oubliée trois fois, et la CI est restée rouge deux jours sans que personne
rattache la cause : le garde ne produit aucune ligne `FAILED`, seulement un
message de fin de session, invisible à qui cherche des tests en échec.

Le lien est mécanique, donc vérifiable : un test qui prend la fixture
`real_pg_db` exige un PostgreSQL, un test qui prend `real_mssql_db` exige un SQL
Server. La correspondance entre la fixture et le marqueur est ce que ce
garde-fou fige, à la place d'une relecture attentive.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_TESTS = PROJECT_ROOT / "tests" / "db"

_FIXTURE_MARQUEUR = {
    "real_pg_db": "db_pg",
    "real_mssql_db": "db_mssql",
}


def _marqueurs_de_module(arbre: ast.Module) -> set[str]:
    """Marqueurs posés par `pytestmark`, forme simple ou liste."""
    trouves: set[str] = set()
    for noeud in arbre.body:
        if not isinstance(noeud, ast.Assign):
            continue
        cibles = [c.id for c in noeud.targets if isinstance(c, ast.Name)]
        if "pytestmark" not in cibles:
            continue
        valeurs = (noeud.value.elts if isinstance(noeud.value, (ast.List, ast.Tuple))
                   else [noeud.value])
        for valeur in valeurs:
            if isinstance(valeur, ast.Attribute):
                trouves.add(valeur.attr)
    return trouves


def _marqueurs_de_test(fonction: ast.FunctionDef) -> set[str]:
    trouves: set[str] = set()
    for decorateur in fonction.decorator_list:
        cible = decorateur.func if isinstance(decorateur, ast.Call) else decorateur
        if isinstance(cible, ast.Attribute):
            trouves.add(cible.attr)
    return trouves


def _fixtures_demandees(fonction: ast.FunctionDef) -> set[str]:
    arguments = fonction.args
    noms = {a.arg for a in arguments.args} | {a.arg for a in arguments.kwonlyargs}
    return noms


def _manquements() -> list[str]:
    """Tests dont la fixture exige un serveur que le marqueur ne déclare pas."""
    fautes: list[str] = []
    for chemin in sorted(DB_TESTS.glob("test_*.py")):
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        du_module = _marqueurs_de_module(arbre)
        # Les fixtures locales relaient la dépendance : une fixture du fichier
        # qui prend `real_pg_db` transmet l'exigence aux tests qui la prennent.
        relais: dict[str, set[str]] = {}
        for noeud in arbre.body:
            if not isinstance(noeud, ast.FunctionDef):
                continue
            exigences = {
                _FIXTURE_MARQUEUR[nom]
                for nom in _fixtures_demandees(noeud) & set(_FIXTURE_MARQUEUR)
            }
            if not noeud.name.startswith("test_"):
                if exigences:
                    relais[noeud.name] = exigences
                continue
        for noeud in arbre.body:
            if not isinstance(noeud, ast.FunctionDef) or not noeud.name.startswith("test_"):
                continue
            demandees = _fixtures_demandees(noeud)
            exigences = {
                _FIXTURE_MARQUEUR[nom] for nom in demandees & set(_FIXTURE_MARQUEUR)
            }
            for nom in demandees & set(relais):
                exigences |= relais[nom]
            portes = du_module | _marqueurs_de_test(noeud)
            for marqueur in sorted(exigences - portes):
                fautes.append(
                    f"{chemin.relative_to(PROJECT_ROOT)}::{noeud.name} "
                    f"exige un serveur mais ne porte pas `{marqueur}`"
                )
    return fautes


def test_chaque_test_declare_le_serveur_qu_il_exige() -> None:
    """Sans le marqueur, le job MariaDB échoue d'avoir sauté ce test."""
    fautes = _manquements()

    assert not fautes, (
        "TEST-DB-COLLECT-GUARD-001 : ajoutez le marqueur de backend "
        "(`pytest.mark.db_pg` ou `pytest.mark.db_mssql`), sinon le job MariaDB "
        "comptera ces tests comme requis et échouera de les avoir sautés.\n  "
        + "\n  ".join(fautes)
    )


def test_le_garde_fou_regarde_bien_quelque_chose() -> None:
    """Un audit qui ne trouve aucun fichier passerait pour toujours vert."""
    assert len(list(DB_TESTS.glob("test_*.py"))) > 10


def test_la_convention_est_ecrite_dans_le_conftest() -> None:
    """Le garde-fou fige la règle, le conftest l'explique."""
    texte = (PROJECT_ROOT / "conftest.py").read_text(encoding="utf-8")

    assert "db_pg" in texte and "db_mssql" in texte
