"""Le back-office sait créer et modifier une entité à horodatages gérés (ADMIN-MANAGED-TIMESTAMPS-001).

L'ADR-081 a retiré les `DEFAULT CURRENT_TIMESTAMP` des tables d'entités : les
colonnes `created_at` et `updated_at` sont `NOT NULL` **sans défaut**, et c'est
Python qui pose la valeur.

`forge-mvc-admin` ignorait ce mécanisme, sans une seule mention dans tout le
paquet. Deux conséquences, mesurées sur les trois serveurs avant correctif.

**Créer était impossible**, l'insertion ne nommant pas les colonnes :

    mariadb    Field 'CreatedAt' doesn't have a default value
    postgres   NOT NULL violation, colonne « created_at »
    mssql      Cannot insert the value NULL into column 'CreatedAt'

**Modifier passait**, mais laissait `updated_at` figé, ce qui est plus discret
et plus durable : l'horodatage ment alors sur la dernière modification.

Le défaut date de l'ADR-081, le 13 juillet, et traverse les rc4 et rc5. Aucun
test ne l'a vu parce que ceux d'`admin` exercent la **construction** du SQL et
jamais son exécution contre une table à horodatages gérés.

C'est la même forme que les cinq défauts trouvés avant la rc5 : une garantie
vérifiée sur la forme du SQL, jamais sur son effet.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin.query import insert_row, update_row
from forge_mvc_admin.resources import AdminResource

from core.database.table_ddl import Column, TableDefinition
from forge_mvc_testing.real_db import tables_temporaires

#: Entité telle que `make:crud` la produit avec `options.timestamps` : les deux
#: colonnes sont `NOT NULL` et sans défaut, conformément à l'ADR-081.
ARTICLE = TableDefinition(
    name="article_admin_ts",
    columns=[
        Column("id", "identity"),
        Column("titre", "string", length=120),
        Column("created_at", "datetime"),
        Column("updated_at", "datetime"),
    ],
    primary_key=["id"],
)


def _ressource(*, timestamps: bool) -> AdminResource:
    return AdminResource(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("titre",),
        form_fields=("titre",),
        table="article_admin_ts",
        timestamps=timestamps,
    )


@pytest.fixture
def table(real_backend_db: str):
    with tables_temporaires(ARTICLE) as db:
        yield db


def test_creer_un_enregistrement(table: Any) -> None:
    """LE test du ticket : sans lui, le back-office ne sait pas créer."""
    avant = datetime.now(timezone.utc)

    insert_row(
        _ressource(timestamps=True),
        lambda sql, params: table.insert(sql, tuple(params)),
        values=["Mon titre"],
    )

    ligne = table.fetch_one("SELECT titre, created_at, updated_at FROM article_admin_ts", ())
    assert ligne is not None
    assert ligne["titre"] == "Mon titre"
    assert ligne["created_at"] is not None, "created_at n'a pas été posé"
    assert ligne["updated_at"] is not None
    # Posé par Python : la valeur vaut au moins l'instant d'avant l'appel.
    assert str(ligne["created_at"]).startswith(str(avant.year))


def test_modifier_rafraichit_updated_at(table: Any) -> None:
    """La modification passait sans erreur, en laissant l'horodatage mentir."""
    ancien = datetime(2020, 1, 1, tzinfo=timezone.utc)
    table.execute(
        "INSERT INTO article_admin_ts (titre, created_at, updated_at) VALUES (?, ?, ?)",
        ("Ancien", ancien, ancien),
    )
    ligne = table.fetch_one("SELECT id FROM article_admin_ts", ())
    assert ligne is not None
    identifiant = ligne["id"]

    update_row(
        _ressource(timestamps=True),
        lambda sql, params: table.execute(sql, tuple(params)),
        values=["Nouveau"],
        pk_value=identifiant,
    )

    apres = table.fetch_one(
        "SELECT titre, created_at, updated_at FROM article_admin_ts WHERE id = ?",
        (identifiant,),
    )
    assert apres is not None
    assert apres["titre"] == "Nouveau"
    assert str(apres["updated_at"])[:4] != "2020", "updated_at n'a pas été rafraîchi"
    assert str(apres["created_at"])[:4] == "2020", "created_at ne doit jamais être réécrit"


def test_une_ressource_sans_horodatages_est_inchangee(table: Any) -> None:
    """Le comportement d'avant tient pour les tables qui n'en portent pas.

    La déclaration est explicite et vaut `False` par défaut (principe 3) : une
    ressource existante ne change pas de comportement du fait de ce ticket.
    """
    sql_vus: "list[str]" = []

    def insert(sql: str, params: Any) -> int:
        sql_vus.append(sql)
        return 1

    insert_row(_ressource(timestamps=False), insert, values=["Sans horodatage"])

    assert "created_at" not in sql_vus[0]
    assert "updated_at" not in sql_vus[0]
