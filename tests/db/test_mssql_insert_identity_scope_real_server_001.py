"""MSSQL-INSERT-IDENTITY-SCOPE-001, mesure sur serveur réel.

Le défaut ne se voyait que face à un vrai serveur : la ligne était écrite,
seule l'identité manquait. Aucun test hors base ne pouvait le révéler, le
curseur factice répondant à la forme du lot et non à ce que SQL Server en fait.

Les sept formes ci-dessous sont celles du relevé d'origine, dont quatre
rendaient `None`. Le CRUD généré redirige vers `/show/{id}` avec cette valeur.

Le pendant hors base est
`packages/forge-mvc-mssql/tests/test_mssql_insert_identity_scope_001.py`.
"""
from __future__ import annotations

import pytest

# TEST-DB-COLLECT-GUARD-001 : le job MariaDB sélectionne `-m db` mais
# laisse sauter ce qui exige un autre serveur, à condition que le second
# marqueur le dise.
pytestmark = [pytest.mark.db, pytest.mark.db_mssql]

_FORMES = [
    ("nu", "INSERT INTO forge_ident_scope (titre) VALUES (?)", ["nu"]),
    ("précédé d'un commentaire",
     "-- crée la ligne\nINSERT INTO forge_ident_scope (titre) VALUES (?)",
     ["commenté devant"]),
    ("indenté sur plusieurs lignes",
     "\n    INSERT INTO forge_ident_scope (titre)\n    VALUES (?)\n",
     ["multiligne"]),
    ("suivi d'un commentaire",
     "INSERT INTO forge_ident_scope (titre) VALUES (?) -- fin",
     ["commenté derrière"]),
    ("« output » dans un littéral",
     "INSERT INTO forge_ident_scope (titre) VALUES ('output du script')", []),
    ("« output » dans un commentaire",
     "INSERT INTO forge_ident_scope (titre) VALUES (?) /* output attendu */",
     ["commentaire output"]),
    ("terminé par un point-virgule",
     "INSERT INTO forge_ident_scope (titre) VALUES (?);", ["point-virgule"]),
]


@pytest.fixture()
def table_identite(real_mssql_db: None):
    from core.database import db

    db.execute("IF OBJECT_ID('forge_ident_scope') IS NOT NULL DROP TABLE forge_ident_scope")
    db.execute(
        "CREATE TABLE forge_ident_scope ("
        " id BIGINT IDENTITY(1,1) PRIMARY KEY,"
        " [output] NVARCHAR(40) NULL,"
        " titre NVARCHAR(80))"
    )
    yield
    db.execute("DROP TABLE forge_ident_scope")


@pytest.mark.parametrize(("nom", "sql", "params"), _FORMES,
                         ids=[forme[0] for forme in _FORMES])
def test_chaque_forme_d_insert_rend_son_identite(
    table_identite: None, nom: str, sql: str, params: "list[str]",
) -> None:
    from core.database import db

    identifiant = db.insert(sql, params)

    assert identifiant is not None, f"identité perdue sur la forme « {nom} »"
    ligne = db.fetch_one("SELECT id FROM forge_ident_scope WHERE id = ?", [identifiant])
    assert ligne == {"id": identifiant}, "l'identité rendue doit désigner la ligne écrite"


def test_une_colonne_nommee_output_ne_desarme_pas_l_identite(
    table_identite: None,
) -> None:
    """`output` est un mot réservé T-SQL : la colonne existe, entre crochets."""
    from core.database import db

    identifiant = db.insert(
        "INSERT INTO forge_ident_scope ([output], titre) VALUES (?, ?)",
        ["sortie", "avec colonne output"],
    )

    assert identifiant is not None


def test_une_vraie_clause_output_reste_servie_par_son_propre_resultat(
    table_identite: None,
) -> None:
    """Ce statement gère déjà son identité : le lot ne doit pas s'y ajouter."""
    from core.database.backend import get_backend

    backend = get_backend()
    connection = backend.get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO forge_ident_scope (titre) OUTPUT INSERTED.id VALUES (?)",
            ("avec clause output",),
        )
        ligne = cursor.fetchone()
        cursor.close()
        connection.commit()
    finally:
        backend.close_connection(connection)

    assert ligne is not None and ligne["id"] > 0


def test_l_identite_designe_la_derniere_ligne_ecrite(table_identite: None) -> None:
    """Deux insertions successives ne doivent pas rendre la même identité."""
    from core.database import db

    premier = db.insert("INSERT INTO forge_ident_scope (titre) VALUES (?)", ["un"])
    second = db.insert(
        "-- deuxième\nINSERT INTO forge_ident_scope (titre) VALUES (?) -- fin", ["deux"])

    assert premier is not None and second is not None
    assert second > premier
    titre = db.fetch_one("SELECT titre FROM forge_ident_scope WHERE id = ?", [second])
    assert titre == {"titre": "deux"}
