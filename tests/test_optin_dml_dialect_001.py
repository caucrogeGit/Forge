"""OPTIN-DML-DIALECT-001 : plus aucune construction MariaDB en dur dans la DML.

Le pendant sur serveurs réels est
`tests/db/test_optin_dml_portability_real_server_001.py`, qui exerce les
opérations. Ici on fige le contrat et l'absence, qui se vérifient sans base.

Deux traits seulement rejoignent `Dialect`, et c'est délibéré. L'horodatage
courant et le décalage temporel n'ont aucune écriture commune aux quatre
serveurs. L'upsert et la réservation d'une ligne unique en ont une, bâtie sur
ce que le contrat offre déjà : écrire puis insérer sous garde d'unicité pour le
premier, choisir puis réserver sous garde de statut pour le second. Un noyau
minimal ne gagne pas à porter ce qu'on peut exprimer sans lui (principe 8).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from core.database.backend import Dialect

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGES = PROJECT_ROOT / "packages"

_BACKENDS = [
    ("forge_mvc_mariadb.dialect", "MariaDBDialect"),
    ("forge_mvc_sqlite.dialect", "SQLiteDialect"),
    ("forge_mvc_postgres.dialect", "PostgreSQLDialect"),
    ("forge_mvc_mssql.dialect", "MSSQLDialect"),
]


# ── Le contrat ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("methode", ["now_expression", "interval_seconds_expression"])
def test_le_contrat_porte_le_trait(methode: str) -> None:
    assert hasattr(Dialect, methode)


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_les_quatre_dialectes_repondent(module: str, classe: str) -> None:
    dialecte = getattr(pytest.importorskip(module), classe)()

    assert isinstance(dialecte.now_expression(), str)
    assert isinstance(dialecte.interval_seconds_expression("X"), str)


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_le_decalage_porte_exactement_un_marqueur(module: str, classe: str) -> None:
    """Un marqueur de plus ou de moins décalerait tous les paramètres suivants."""
    dialecte = getattr(pytest.importorskip(module), classe)()

    assert dialecte.interval_seconds_expression("BASE").count("?") == 1


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_le_decalage_reprend_la_base_qu_on_lui_donne(module: str, classe: str) -> None:
    dialecte = getattr(pytest.importorskip(module), classe)()

    assert "BASE" in dialecte.interval_seconds_expression("BASE")


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_l_horodatage_coincide_avec_la_clause_default(module: str, classe: str) -> None:
    """La contrainte qui compte : deux lignes doivent rester comparables.

    Une ligne insérée avec le défaut de la colonne et une ligne insérée avec
    l'expression doivent porter la même horloge. SQL Server pose ses défauts en
    UTC (`SYSUTCDATETIME`), là où son `CURRENT_TIMESTAMP` rend l'heure locale.
    """
    dialecte = getattr(pytest.importorskip(module), classe)()

    defaut = dialecte.timestamp_default_clause(on_update=False)
    assert dialecte.now_expression() in defaut


# ── L'absence, dans les opt-ins ──────────────────────────────────────────────

_NON_PORTABLE = re.compile(
    r"\bNOW\(\)|ON DUPLICATE KEY|INTERVAL \?|ORDER BY \w+ LIMIT \d", re.IGNORECASE
)


def _fichiers_sql_des_optins() -> "list[Path]":
    """Modules des opt-ins applicatifs, hors backends et hors code généré."""
    fichiers: "list[Path]" = []
    for paquet in sorted(PACKAGES.iterdir()):
        if not paquet.is_dir() or paquet.name in {
            "forge-mvc-mariadb", "forge-mvc-postgres",
            "forge-mvc-mssql", "forge-mvc-sqlite",
        }:
            continue
        for module in paquet.rglob("forge_mvc_*/**/*.py"):
            if "build/" in module.as_posix() or "__pycache__" in module.as_posix():
                continue
            fichiers.append(module)
    return fichiers


def test_aucune_construction_mariadb_en_dur_dans_la_dml() -> None:
    """Les chaînes SQL des opt-ins ne doivent nommer aucune forme propriétaire.

    Les commentaires et docstrings y ont droit : ils expliquent justement
    pourquoi la forme est bannie. Seules les chaînes de code comptent.
    """
    fautes: "list[str]" = []
    for module in _fichiers_sql_des_optins():
        for numero, ligne in enumerate(module.read_text(encoding="utf-8").splitlines(), 1):
            nue = ligne.strip()
            if nue.startswith("#") or nue.startswith('"""') or nue.startswith("`"):
                continue
            if '"' not in ligne and "'" not in ligne:
                continue
            if _NON_PORTABLE.search(ligne) and ("SELECT" in ligne.upper()
                                                or "UPDATE" in ligne.upper()
                                                or "INSERT" in ligne.upper()
                                                or "VALUES" in ligne.upper()):
                fautes.append(f"{module.relative_to(PROJECT_ROOT)}:{numero} : {nue[:80]}")

    assert not fautes, (
        "SQL non portable dans un opt-in (OPTIN-DML-DIALECT-001) : passez par "
        "`dialect.now_expression()` / `interval_seconds_expression()`, ou par un "
        "motif portable.\n  " + "\n  ".join(fautes)
    )


def test_l_audit_regarde_bien_quelque_chose() -> None:
    """Un balayage qui ne trouve aucun fichier passerait pour toujours vert."""
    assert len(_fichiers_sql_des_optins()) > 100


def test_sessions_db_reste_le_modele_du_sans_fonction_serveur() -> None:
    """Ce paquet calcule ses horodatages en Python : sa garde ne doit pas bouger.

    C'est l'autre réponse valable, et la meilleure quand l'horloge de référence
    peut être celle de l'application.
    """
    garde = (PACKAGES / "forge-mvc-sessions-db" / "tests" / "test_db_store_001.py")

    assert 'assert "NOW()" not in sql' in garde.read_text(encoding="utf-8")
