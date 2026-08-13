"""Le CRUD engendré rend ses colonnes sous leur casse déclarée (CRUD-PG-COLUMN-CASE-001).

PostgreSQL replie tout identifiant non protégé en minuscules : une colonne
déclarée `Nom` s'y relit `nom`. MariaDB et SQL Server, eux, conservent la casse.

`make:crud` engendrait `SELECT * FROM contact`, sans alias, et les vues qu'il
engendre lisent `{{ contact.Nom }}`, par **nom de colonne**. Sur PostgreSQL, la
clé rendue était donc `nom` et l'attribut `Nom` n'existait pas.

**Jinja ne lève pas sur un attribut absent** : il rend une chaîne vide. Le
tableau s'affichait entièrement vide, lignes et boutons présents, contenu
manquant, sans une ligne de journal. Les liens `/contact/show/{{ contact.Id }}`
pointaient tous vers `/contact/show/`.

Silencieux, sur un backend que l'ADR-084 donne au niveau plein depuis juillet.

Le correctif nomme et alias les colonnes entre guillemets, forme acceptée par
les quatre backends et vérifiée ici. Les vues sont inchangées.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")

from core.database.table_ddl import Column, TableDefinition
from forge_mvc_testing.real_db import tables_temporaires

#: Entité aux colonnes PascalCase, convention répandue et celle de la première
#: application Forge. C'est elle qui révèle le repli de casse.
CONTACT = TableDefinition(
    name="contact_casse",
    columns=[
        Column("Id", "identity"),
        Column("Nom", "string", length=60),
        Column("Email", "string", length=120, nullable=True),
    ],
    primary_key=["Id"],
)

DEFINITION: "dict[str, Any]" = {
    "entity": "Contact",
    "table": "contact_casse",
    "fields": [
        {"name": "id", "column": "Id", "type": "integer",
         "primary_key": True, "auto_increment": True},
        {"name": "nom", "column": "Nom", "type": "string", "length": 60},
        {"name": "email", "column": "Email", "type": "string", "length": 120},
    ],
}


def _select_all() -> str:
    """La requête que `make:crud` engendre, extraite de sa sortie réelle.

    Extraite et non recopiée : un test qui recopie la requête ne vérifie que
    lui-même.
    """
    from forge_mvc_entities.crud.model_builder import build_model

    for ligne in build_model(DEFINITION).splitlines():
        if ligne.startswith("SELECT_ALL"):
            return ligne.split("=", 1)[1].strip().strip('"').replace('\\"', '"')
    raise AssertionError("SELECT_ALL introuvable dans le modèle engendré")


@pytest.fixture
def table(real_backend_db: str):
    with tables_temporaires(CONTACT) as db:
        db.execute(
            "INSERT INTO contact_casse (Nom, Email) VALUES (?, ?)",
            ("Alice", "alice@exemple.fr"),
        )
        yield db


def test_les_colonnes_gardent_leur_casse(table: Any) -> None:
    """LE test du ticket : sans lui, le tableau s'affiche vide sur PostgreSQL."""
    lignes = table.fetch_all(_select_all(), ())

    assert lignes, "aucune ligne rendue"
    ligne = lignes[0]
    assert "Nom" in ligne, (
        f"la colonne déclarée `Nom` se relit sous {sorted(ligne)} : les vues "
        "engendrées lisent `{{ contact.Nom }}` et afficheront une cellule vide"
    )
    assert "Id" in ligne
    assert ligne["Nom"] == "Alice"


def test_la_vue_engendree_lit_bien_ces_cles(table: Any) -> None:
    """Le lien entre la requête et la vue, vérifié plutôt que supposé.

    C'est ce maillon qui rendait le défaut invisible : chacun des deux côtés
    était cohérent avec lui-même.
    """
    from forge_mvc_entities.crud.views_builder import build_table_partial

    vue = build_table_partial(DEFINITION)
    ligne = table.fetch_all(_select_all(), ())[0]

    for colonne in ("Id", "Nom"):
        assert f"contact.{colonne}" in vue, f"la vue ne lit pas {colonne}"
        assert colonne in ligne, (
            f"la vue lit `contact.{colonne}` mais la requête rend "
            f"{sorted(ligne)} : Jinja affichera du vide, sans erreur"
        )


def test_la_projection_est_nommee_et_non_une_etoile() -> None:
    """`SELECT *` ne peut pas préserver la casse, quel que soit le moteur.

    Nommer les colonnes rend au passage le SQL lisible (principe 5).
    """
    requete = _select_all()

    assert "SELECT *" not in requete
    assert 'AS "Nom"' in requete
