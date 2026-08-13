"""Le SQL rendu par `fixtures:generate` s'exécute sur les trois moteurs (FIXTURES-RENDER-EXEC-001).

`fixtures:generate` produit un fichier `.sql` que l'utilisateur charge ensuite.
Ce fichier était vérifié par comparaison de chaînes, jamais soumis à un moteur.
Or un SQL écrit comme **texte** échappe à la couche de requêtes : il ne passe ni
par les paramètres liés, ni par la traduction des marqueurs, ni par rien de ce
qui protège le reste du framework.

C'est précisément ce qui avait laissé passer `LIMIT 1` en dur dans les
sous-requêtes de référence, refusé par SQL Server
(`FIXTURES-REFERENCE-DIALECT-001`). Le correctif est posé ; il n'était toujours
pas exécuté.

Ce fichier ferme la boucle : rendre le fichier, le charger, relire les lignes.
Les littéraux exercés sont ceux qui cassent en pratique, apostrophe comprise,
puisqu'un rendu naïf y ouvre une injection autant qu'une erreur de syntaxe.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from core.database.table_ddl import Column, TableDefinition
from forge_mvc_testing.real_db import tables_temporaires

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_fixtures")

TABLE = TableDefinition(
    name="fixture_sonde",
    columns=[
        Column("Id", "identity"),
        Column("Libelle", "string", length=120),
        Column("Actif", "boolean"),
        Column("Quantite", "integer"),
        Column("Prix", "float"),
        Column("Note", "string", length=200, nullable=True),
        Column("Quand", "datetime"),
    ],
    primary_key=["Id"],
)

#: Les valeurs choisies pour ce qu'elles cassent, pas pour leur banalité.
#: L'apostrophe est la première : un rendu naïf y produit du SQL invalide, et un
#: rendu naïf **échappé à moitié** y produit une injection.
LIGNE = {
    "Libelle": "L'atelier « bois »",
    "Actif": True,
    "Quantite": 42,
    "Prix": 19.99,
    "Note": None,
    "Quand": datetime(2026, 8, 13, 12, 0, 0),
}


@pytest.fixture
def table(real_backend_db: str):
    with tables_temporaires(TABLE) as db:
        yield db


def _dialecte() -> Any:
    from core.database.backend import get_backend

    return get_backend().dialect


def test_le_fichier_rendu_se_charge_et_relit_ses_valeurs(table: Any) -> None:
    """Le chemin complet : rendre le texte, l'exécuter, comparer les valeurs relues."""
    from core.database.sql_script import split_sql_statements
    from forge_mvc_fixtures.cli.generate import render_inserts

    texte = render_inserts("fixture_sonde", [LIGNE], _dialecte())

    for instruction in split_sql_statements(texte):
        table.execute(instruction)

    # Alias entre guillemets : sans eux, PostgreSQL replie les colonnes en
    # minuscules et les clés lues n'existent pas (`CRUD-PG-COLUMN-CASE-001`).
    ligne = table.fetch_one(
        'SELECT Libelle AS "Libelle", Actif AS "Actif", Quantite AS "Quantite", '
        'Prix AS "Prix", Note AS "Note" FROM fixture_sonde',
        (),
    )
    assert ligne is not None
    assert ligne["Libelle"] == "L'atelier « bois »", (
        "l'apostrophe n'a pas survécu au rendu : le littéral est mal échappé"
    )
    assert bool(ligne["Actif"]) is True
    assert int(ligne["Quantite"]) == 42
    assert abs(float(ligne["Prix"]) - 19.99) < 0.001
    assert ligne["Note"] is None, "`None` doit devenir `NULL`, pas la chaîne « None »"


def test_la_sous_requete_de_reference_s_execute(table: Any) -> None:
    """LE cas qui avait cassé SQL Server : la borne de la sous-requête.

    `LIMIT 1` était écrit en dur, et SQL Server refusait le fichier produit.
    Le correctif passe par le dialecte ; ce test l'exécute enfin.
    """
    from core.database.sql_script import split_sql_statements
    from forge_mvc_fixtures.cli.generate import render_inserts
    from forge_mvc_fixtures.factory import FixtureReference

    # Une première ligne, que la référence ira retrouver par son libellé.
    for instruction in split_sql_statements(render_inserts("fixture_sonde", [LIGNE], _dialecte())):
        table.execute(instruction)

    seconde = dict(LIGNE)
    seconde["Libelle"] = "Seconde"
    seconde["Quantite"] = FixtureReference(
        table="fixture_sonde", key_column="Libelle", value="L'atelier « bois »"
    )

    texte = render_inserts("fixture_sonde", [seconde], _dialecte())
    for instruction in split_sql_statements(texte):
        table.execute(instruction)

    ligne = table.fetch_one(
        'SELECT Quantite AS "Quantite" FROM fixture_sonde WHERE Libelle = ?',
        ("Seconde",),
    )
    assert ligne is not None
    assert int(ligne["Quantite"]) == 1, (
        "la sous-requête doit résoudre l'Id de la première ligne, soit 1"
    )


def test_le_rendu_ne_laisse_pas_passer_une_apostrophe_seule() -> None:
    """Contrôle direct du littéral, sans base : une injection est plus qu'une erreur.

    Un rendu qui laisserait l'apostrophe intacte casserait la syntaxe dans le
    meilleur cas, et permettrait d'écrire du SQL arbitraire dans le pire. Le
    fichier engendré est ensuite exécuté tel quel par `fixtures:load`.
    """
    from forge_mvc_fixtures.cli.generate import render_value

    rendu = render_value("'; DROP TABLE fixture_sonde; --", _dialecte())

    # L'apostrophe intérieure doit être doublée : c'est elle, et elle seule, qui
    # empêche la valeur de sortir de sa chaîne pour devenir du code.
    assert rendu.startswith("''" + "'"), (
        f"l'apostrophe de tête n'est pas doublée, la chaîne se referme : {rendu!r}"
    )
    assert rendu.count("'") % 2 == 0, (
        f"littéral déséquilibré, donc échappable : {rendu!r}"
    )

    # Et le tout reste UNE seule instruction : rien n'en sort.
    from core.database.sql_script import split_sql_statements

    assert len(split_sql_statements(f"SELECT {rendu}")) == 1, (
        f"le littéral rendu produit plus d'une instruction : {rendu!r}"
    )
