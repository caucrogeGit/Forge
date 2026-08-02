"""FIXTURES-REFERENCE-DIALECT-001, pendant sur serveurs réels.

Le garde unitaire compare des chaînes ; seul un serveur dit si elles sont du SQL
valide. C'est précisément ce qui manquait : le fichier produit par
`fixtures:generate` n'était jamais soumis à SQL Server, et son `LIMIT 1` y était
refusé (`[42000] Incorrect syntax near '1'`).

Chaque backend joue ici la sous-requête que son dialecte rend, contre son
serveur, sur une table réelle, et par le chemin de requêtes de Forge.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.db

TABLE = "forge_srq_users"


def _eprouver() -> None:
    """Crée la table, joue la sous-requête du dialecte actif, nettoie."""
    import core.database.db as db
    from core.database.backend import get_backend

    dialecte = get_backend().dialect
    identite = dialecte.auto_increment_primary_key_ddl("Id", "INT")
    db.execute(f"CREATE TABLE {TABLE} ({identite}, Email VARCHAR(80) NULL)")
    try:
        sous_requete = dialecte.single_row_subquery(
            "Id", TABLE, "Email = 'a@b.c'")
        db.fetch_all(f"SELECT {sous_requete} AS trouve")
    finally:
        db.execute(f"DROP TABLE {TABLE}")


def test_mariadb_accepte_la_sous_requete(real_db) -> None:  # type: ignore[no-untyped-def]
    _eprouver()


@pytest.mark.db_pg
def test_postgresql_accepte_la_sous_requete(real_pg_db) -> None:  # type: ignore[no-untyped-def]
    _eprouver()


@pytest.mark.db_mssql
def test_sql_server_accepte_la_sous_requete(real_mssql_db) -> None:  # type: ignore[no-untyped-def]
    """Le cas mesuré : c'est ce serveur qui refusait la forme précédente."""
    _eprouver()
