"""SESSIONS-DELETE-FOR-USER-001 — l'ajout de colonne s'exécute sur un vrai serveur.

`render_add_column` est né parce que le mécanisme de migration des opt-ins ne
savait rendre que des `CREATE TABLE` : aucun opt-in ne pouvait ajouter une
colonne sans casser les projets déjà provisionnés.

Le rendu était vérifié par comparaison de chaînes, ce qui ne prouve rien : une
instruction peut être exactement celle qu'on voulait écrire et rester refusée
par le serveur. Ce test joue le scénario réel, sur les trois serveurs.

Le scénario est celui d'un projet existant : la table est créée **sans** la
colonne, une ligne y est écrite, puis la migration passe. La ligne d'avant doit
survivre, ce que seule une colonne acceptant `NULL` garantit.

Marqué `db` : sauté sans serveur, requis en CI via FORGE_REQUIRE_DB=1.
"""
from __future__ import annotations

import uuid
from dataclasses import replace

import pytest

from core.database import db
from core.database.backend import get_backend
from core.database.table_ddl import (
    Column,
    Index,
    TableDefinition,
    render_add_column,
    render_create_table,
)

pytestmark = pytest.mark.db


def _table(nom: str) -> TableDefinition:
    """Table à deux colonnes, dont une ajoutée après coup, et son index."""
    return TableDefinition(
        name=nom,
        columns=[
            Column("cle", "char", length=32),
            Column("ajoutee", "string", length=191, nullable=True),
        ],
        primary_key=["cle"],
        indexes=[Index(f"{nom}_idx0", "ajoutee")],
    )


def test_l_ajout_de_colonne_s_execute_et_preserve_les_lignes(
    real_backend_db: str,
) -> None:
    nom = f"forge_it_add_{uuid.uuid4().hex[:12]}"
    cible = _table(nom)
    dialecte = get_backend().dialect

    # Le projet d'avant : la table sans la colonne, ni son index.
    avant = replace(
        cible,
        columns=[c for c in cible.columns if c.name != "ajoutee"],
        indexes=[],
    )

    try:
        for instruction in render_create_table(avant, dialecte):
            db.execute(instruction)

        db.execute(f"INSERT INTO {nom} (cle) VALUES (?)", ["existante"])

        # La migration du ticket.
        for instruction in render_add_column(cible, "ajoutee", dialecte):
            db.execute(instruction)

        # La ligne d'avant a survécu, sans valeur pour la colonne neuve.
        ligne = db.fetch_one(f"SELECT ajoutee FROM {nom} WHERE cle = ?", ["existante"])
        assert ligne is not None, "la ligne écrite avant la migration a disparu"
        assert ligne["ajoutee"] is None, "une colonne ajoutée doit valoir NULL sur l'existant"

        # La colonne est utilisable en écriture comme en lecture.
        db.execute(f"INSERT INTO {nom} (cle, ajoutee) VALUES (?, ?)", ["neuve", "42"])
        ligne = db.fetch_one(f"SELECT ajoutee FROM {nom} WHERE cle = ?", ["neuve"])
        assert ligne is not None
        assert str(ligne["ajoutee"]) == "42"

        # Et filtrable, ce que l'index sert à rendre rapide.
        supprimees = db.execute(f"DELETE FROM {nom} WHERE ajoutee = ?", ["42"])
        assert supprimees == 1
    finally:
        db.execute(f"DROP TABLE IF EXISTS {nom}")


def test_l_index_de_la_colonne_ajoutee_n_est_pas_un_doublon(
    real_backend_db: str,
) -> None:
    """Rejouer l'index après un `CREATE TABLE` qui le portait déjà doit échouer.

    Ce test fige la raison pour laquelle `render_add_column` ne rend que les
    index de la colonne ajoutée. Sur MariaDB, un `CREATE INDEX` en double lève ;
    sur PostgreSQL et SQL Server, il est ignoré en silence, ce qui laissait un
    test passer en ne créant qu'un index sur deux.
    """
    nom = f"forge_it_idx_{uuid.uuid4().hex[:12]}"
    cible = _table(nom)
    dialecte = get_backend().dialect

    try:
        for instruction in render_create_table(cible, dialecte):
            db.execute(instruction)

        instructions = render_add_column(cible, "ajoutee", dialecte)
        index_seuls = [i for i in instructions if i.upper().lstrip().startswith(("CREATE INDEX", "IF NOT EXISTS"))]

        assert index_seuls, "l'ajout doit rendre l'index de la colonne"
        assert len(index_seuls) == 1, (
            f"seul l'index de la colonne ajoutée doit être rendu, obtenu : {index_seuls}"
        )
    finally:
        db.execute(f"DROP TABLE IF EXISTS {nom}")
