"""Les tests d'intégration de paquet passent par la vraie couche (TEST-PACKAGE-INTEGRATION-REAL-LAYER-001).

Six paquets opt-in avaient chacun écrit son propre adaptateur de connexion, un
petit objet exposant `execute`, `fetch_one` et `fetch_all` par-dessus une
connexion pilote montée à la main. Deux conséquences, aucune voulue.

Ils ne tournaient que sur **MariaDB**, alors que l'ADR-084 donne les quatre
backends au niveau plein. Et ils court-circuitaient la **vraie couche d'accès**
`core.database.db`, donc la qualification d'erreur de Forge : une violation
d'unicité y remontait sous sa forme pilote, jamais sous la forme portable
`UniqueViolationError`. C'est cet écart qui a caché deux défauts du magasin
anti-rejeu MFA pendant tout un cycle, dont un interblocage InnoDB.

La cause était l'absence de fixture partagée, corrigée par
`TESTING-REAL-DB-FIXTURES-001`. Ce garde-fou empêche le contournement de
revenir.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_RACINE = Path(__file__).resolve().parent.parent

#: Les six fichiers concernés, avec le paquet qui les porte.
_FICHIERS_REECRITS = (
    "packages/forge-mvc-audit/tests/test_audit_db_integration_001.py",
    "packages/forge-mvc-jobs/tests/test_jobs_db_integration_001.py",
    "packages/forge-mvc-mfa/tests/test_mfa_replay_db_integration_001.py",
    "packages/forge-mvc-notifications/tests/test_notifications_db_integration_001.py",
    "packages/forge-mvc-settings/tests/test_settings_db_integration_001.py",
    "packages/forge-mvc-stats/tests/test_stats_db_integration_001.py",
)

#: Une classe qui expose `execute` **et** une lecture est un adaptateur de base.
_METHODES_ECRITURE = {"execute", "insert"}
_METHODES_LECTURE = {"fetch_one", "fetch_all"}


#: Signes qu'un fichier vise un **serveur réel**, et non un faux objet en
#: mémoire. Les deux familles comptent : la fixture partagée pour la forme
#: actuelle, l'import d'un pilote pour la forme que ce ticket supprime. Ne
#: retenir que la première laisserait passer exactement les six fichiers
#: d'origine, qui n'employaient aucune fixture.
_SIGNES_SERVEUR_REEL = (
    "real_backend_db", "real_db", "real_pg_db", "real_mssql_db",
    "import mariadb", "import psycopg", "import pyodbc",
)


def _classes_du_fichier(arbre: ast.Module) -> list[tuple[str, set[str]]]:
    classes: list[tuple[str, set[str]]] = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.ClassDef):
            continue
        methodes = {
            membre.name
            for membre in noeud.body
            if isinstance(membre, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        classes.append((noeud.name, methodes))
    return classes


def _lignes_de_docstring(arbre: ast.Module) -> set[int]:
    """Numéros de ligne occupés par une docstring, à ne pas juger comme du SQL."""
    lignes: set[int] = set()
    for noeud in ast.walk(arbre):
        corps = getattr(noeud, "body", None)
        if not isinstance(corps, list) or not corps:
            continue
        premier = corps[0]
        if (
            isinstance(premier, ast.Expr)
            and isinstance(premier.value, ast.Constant)
            and isinstance(premier.value.value, str)
        ):
            fin = premier.end_lineno or premier.lineno
            lignes.update(range(premier.lineno, fin + 1))
    return lignes


def _chaines_sql(arbre: ast.Module) -> list[str]:
    """Chaînes littérales qui ressemblent à du SQL, docstrings exclues.

    Juger le fichier entier revient à juger sa prose : les docstrings de ces
    six fichiers **citent** `NOW()` et `ON DUPLICATE KEY` pour expliquer
    pourquoi ils ne les écrivent plus.
    """
    docstrings = _lignes_de_docstring(arbre)
    mots = ("SELECT", "UPDATE", "INSERT", "DELETE", "VALUES")
    chaines: list[str] = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Constant) or not isinstance(noeud.value, str):
            continue
        if noeud.lineno in docstrings:
            continue
        majuscules = noeud.value.upper()
        if any(mot in majuscules for mot in mots):
            chaines.append(noeud.value)
    return chaines


def test_aucun_test_d_integration_de_paquet_ne_remonte_son_adaptateur() -> None:
    """Écrire son propre `execute`/`fetch_one` revient à tester à côté de Forge.

    Un adaptateur fait main ne traduit pas les marqueurs de paramètre et ne
    qualifie pas les erreurs. Il rend le test vert sur du code que la vraie
    couche ferait échouer, ce qui est pire qu'un test absent.

    Le relevé ne vise que les fichiers qui montent un **serveur réel** : un
    faux objet de base dans un test unitaire est légitime, il ne prétend rien
    prouver sur un moteur. Un fichier compte comme tel s'il demande une
    fixture serveur ou s'il importe un pilote, sans quoi le relevé aurait
    ignoré les six fichiers d'origine, qui ne faisaient que la seconde chose.
    """
    coupables: list[str] = []
    for chemin in _RACINE.glob("packages/*/tests/**/*.py"):
        source = chemin.read_text(encoding="utf-8")
        if not any(signe in source for signe in _SIGNES_SERVEUR_REEL):
            continue
        for nom, methodes in _classes_du_fichier(ast.parse(source)):
            if (methodes & _METHODES_ECRITURE) and (methodes & _METHODES_LECTURE):
                coupables.append(
                    f"{chemin.relative_to(_RACINE)} : la classe {nom} expose "
                    f"{sorted(methodes & (_METHODES_ECRITURE | _METHODES_LECTURE))}, "
                    "donc double core.database.db"
                )
    assert not coupables, "\n".join(coupables)


@pytest.mark.parametrize("relatif", _FICHIERS_REECRITS)
def test_le_fichier_passe_par_la_fixture_des_trois_serveurs(relatif: str) -> None:
    """Chacun des six demande `real_backend_db`, donc s'exécute sur les trois serveurs.

    Sans cela le fichier retomberait sur un seul moteur, et la moitié des
    backends redeviendrait non vérifiée sans que rien ne le signale.
    """
    source = (_RACINE / relatif).read_text(encoding="utf-8")
    assert "real_backend_db" in source, f"{relatif} ne demande pas les trois serveurs"
    assert "tables_temporaires" in source, (
        f"{relatif} ne crée pas ses tables par la DDL dialectale partagée"
    )


@pytest.mark.parametrize("relatif", _FICHIERS_REECRITS)
def test_le_fichier_ne_monte_plus_de_connexion_pilote(relatif: str) -> None:
    """Plus d'`import mariadb` ni de base jetable créée à la main.

    La fixture partagée s'en charge, et elle sait le faire pour les trois
    moteurs.
    """
    source = (_RACINE / relatif).read_text(encoding="utf-8")
    for interdit in ("import mariadb", "CREATE DATABASE", "DROP DATABASE"):
        assert interdit not in source, f"{relatif} contient encore « {interdit} »"


@pytest.mark.parametrize("relatif", _FICHIERS_REECRITS)
def test_le_fichier_n_ecrit_pas_de_sql_non_portable(relatif: str) -> None:
    """`NOW()` et `INTERVAL ? SECOND` cassent sur SQL Server, y compris dans un test.

    Les helpers de `jobs` les employaient : c'est ce qui aurait fait échouer le
    fichier dès son premier passage sur un autre moteur, et donc ce qui aurait
    pu faire renoncer à l'élargissement.
    """
    arbre = ast.parse((_RACINE / relatif).read_text(encoding="utf-8"))
    for sql in _chaines_sql(arbre):
        majuscules = sql.upper()
        for interdit in ("NOW()", "INTERVAL ?", "ON DUPLICATE KEY", "LIMIT"):
            assert interdit not in majuscules, (
                f"{relatif} écrit encore « {interdit} » dans : {sql!r}"
            )
