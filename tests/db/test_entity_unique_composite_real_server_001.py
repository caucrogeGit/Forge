"""ENTITIES-UNIQUE-COMPOSITE-001 — la contrainte refuse vraiment un doublon.

Le SQL rendu était jusqu'ici comparé à des chaînes attendues. Une contrainte
peut être exactement celle qu'on voulait écrire et ne rien contraindre : seul
le serveur dit si un doublon passe.

Ce test crée la table depuis un contrat et tente le doublon, sur les trois
serveurs.

Marqué `db` : sauté sans serveur, requis en CI via FORGE_REQUIRE_DB=1.
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_entities")


def _sql(table: str, indexes: "list[dict[str, object]]") -> str:
    from forge_mvc_entities.make_entity import build_entity_sql

    return build_entity_sql({
        "entity": "Inscription",
        "table": table,
        "fields": [
            {"name": "id", "column": "Id", "sql_type": "INTEGER", "python_type": "int",
             "nullable": False, "primary_key": True, "auto_increment": True},
            {"name": "eleve_id", "column": "EleveId", "sql_type": "INTEGER",
             "python_type": "int", "nullable": False, "primary_key": False,
             "auto_increment": False},
            {"name": "session_id", "column": "SessionId", "sql_type": "INTEGER",
             "python_type": "int", "nullable": False, "primary_key": False,
             "auto_increment": False},
        ],
        "indexes": indexes,
    })


def _executer(sql: str) -> None:
    from core.database.sql_script import split_sql_statements

    for instruction in split_sql_statements(sql):
        if instruction.strip():
            db.execute(instruction)


def test_la_contrainte_composite_refuse_un_doublon(real_backend_db: str) -> None:
    nom = f"forge_it_uq_{uuid.uuid4().hex[:12]}"
    try:
        _executer(_sql(nom, [
            {"name": f"{nom}_uq", "columns": ["EleveId", "SessionId"], "unique": True}
        ]))

        db.execute(f"INSERT INTO {nom} (EleveId, SessionId) VALUES (?, ?)", [1, 10])

        # Le couple existe déjà : le serveur doit refuser.
        with pytest.raises(Exception):
            db.execute(f"INSERT INTO {nom} (EleveId, SessionId) VALUES (?, ?)", [1, 10])
    finally:
        db.execute(f"DROP TABLE IF EXISTS {nom}")


def test_la_contrainte_laisse_passer_un_couple_different(real_backend_db: str) -> None:
    """Une contrainte qui refuserait tout serait aussi fausse qu'une absente."""
    nom = f"forge_it_uq_{uuid.uuid4().hex[:12]}"
    try:
        _executer(_sql(nom, [
            {"name": f"{nom}_uq", "columns": ["EleveId", "SessionId"], "unique": True}
        ]))

        db.execute(f"INSERT INTO {nom} (EleveId, SessionId) VALUES (?, ?)", [1, 10])
        # Même élève, autre session : permis, c'est le sens du composite.
        db.execute(f"INSERT INTO {nom} (EleveId, SessionId) VALUES (?, ?)", [1, 11])
        # Autre élève, même session : permis aussi.
        db.execute(f"INSERT INTO {nom} (EleveId, SessionId) VALUES (?, ?)", [2, 10])

        ligne = db.fetch_one(f"SELECT COUNT(*) AS n FROM {nom}", [])
        assert ligne is not None
        assert int(ligne["n"]) == 3
    finally:
        db.execute(f"DROP TABLE IF EXISTS {nom}")


def test_un_index_simple_s_execute(real_backend_db: str) -> None:
    """Un index non unique ne doit rien contraindre, et surtout s'exécuter."""
    nom = f"forge_it_idx_{uuid.uuid4().hex[:12]}"
    try:
        _executer(_sql(nom, [
            {"name": f"{nom}_idx", "columns": ["EleveId"], "unique": False}
        ]))

        db.execute(f"INSERT INTO {nom} (EleveId, SessionId) VALUES (?, ?)", [1, 10])
        db.execute(f"INSERT INTO {nom} (EleveId, SessionId) VALUES (?, ?)", [1, 10])

        ligne = db.fetch_one(f"SELECT COUNT(*) AS n FROM {nom}", [])
        assert ligne is not None
        assert int(ligne["n"]) == 2
    finally:
        db.execute(f"DROP TABLE IF EXISTS {nom}")
