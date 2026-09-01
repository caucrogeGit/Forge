"""FILES-METADATA-TABLE-001 — le registre s'exécute sur un vrai serveur (ADR-094).

Le SQL du registre était vérifié par comparaison de chaînes, ce qui ne prouve
rien : une requête peut être exactement celle qu'on voulait écrire et rester
refusée par le serveur. Le chantier précédent l'a montré, un `ADD COLUMN`
correct sur trois backends étant une erreur de syntaxe sur le quatrième.

Ce test crée la table, l'alimente et interroge le quota sur les trois serveurs.

Marqué `db` : sauté sans serveur, requis en CI via FORGE_REQUIRE_DB=1.
"""
from __future__ import annotations

import uuid
from dataclasses import replace

import pytest

from core.database import db
from core.database.backend import get_backend
from core.database.table_ddl import render_create_table

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_files")


def _table_isolee(nom: str):
    """Le registre, renommé pour ne pas heurter une vraie table."""
    from forge_mvc_files.tables import FILES

    return replace(
        FILES,
        name=nom,
        indexes=[
            replace(index, name=f"{nom}_idx{numero}")
            for numero, index in enumerate(FILES.indexes)
        ],
    )


class _Adaptateur:
    """Redirige le SQL du registre vers la table isolée du test."""

    def __init__(self, nom: str) -> None:
        self._nom = nom

    def _reecrire(self, sql: str) -> str:
        from forge_mvc_files.tables import FILES_TABLE_NAME

        return sql.replace(FILES_TABLE_NAME, self._nom)

    def execute(self, sql: str, params=()):
        return db.execute(self._reecrire(sql), list(params))

    def fetch_one(self, sql: str, params=()):
        return db.fetch_one(self._reecrire(sql), list(params))

    def fetch_all(self, sql: str, params=()):
        return db.fetch_all(self._reecrire(sql), list(params))


def test_le_registre_s_execute_et_le_quota_se_calcule(real_backend_db: str) -> None:
    from forge_mvc_files.registry import (
        forget_file,
        get_file_record,
        list_all_paths,
        owner_file_count,
        owner_usage_bytes,
        record_file,
    )

    nom = f"forge_it_files_{uuid.uuid4().hex[:12]}"
    adaptateur = _Adaptateur(nom)

    try:
        for instruction in render_create_table(_table_isolee(nom), get_backend().dialect):
            db.execute(instruction)

        record_file("u7/rapport.pdf", "Rapport annuel.pdf", 1024,
                    mime_type="application/pdf", owner_kind="user", owner_id=7,
                    db=adaptateur)
        record_file("u7/facture.pdf", "Facture.pdf", 512,
                    owner_kind="user", owner_id=7, db=adaptateur)
        record_file("libre.pdf", "Sans proprietaire.pdf", 8192, db=adaptateur)

        # Le nom d'origine survit au chemin.
        ligne = get_file_record("u7/rapport.pdf", db=adaptateur)
        assert ligne is not None
        assert ligne["original_name"] == "Rapport annuel.pdf"
        assert int(ligne["size_bytes"]) == 1024

        # Le quota agrège, et ignore ce qui n'appartient à personne.
        assert owner_usage_bytes("user", 7, db=adaptateur) == 1536
        assert owner_file_count("user", 7, db=adaptateur) == 2
        assert owner_usage_bytes("user", 9, db=adaptateur) == 0

        # Le rapprochement avec le disque part de cette liste.
        assert list_all_paths(db=adaptateur) == [
            "libre.pdf", "u7/facture.pdf", "u7/rapport.pdf",
        ]

        assert forget_file("u7/rapport.pdf", db=adaptateur) is True
        assert owner_usage_bytes("user", 7, db=adaptateur) == 512
    finally:
        db.execute(f"DROP TABLE IF EXISTS {nom}")


def test_deux_lignes_pour_un_meme_chemin_sont_refusees(real_backend_db: str) -> None:
    """Sans cette contrainte, un quota compterait deux fois le même fichier."""
    from forge_mvc_files.registry import record_file

    nom = f"forge_it_files_{uuid.uuid4().hex[:12]}"
    adaptateur = _Adaptateur(nom)

    try:
        for instruction in render_create_table(_table_isolee(nom), get_backend().dialect):
            db.execute(instruction)

        record_file("doublon.pdf", "a.pdf", 10, db=adaptateur)
        with pytest.raises(Exception):
            record_file("doublon.pdf", "b.pdf", 20, db=adaptateur)
    finally:
        db.execute(f"DROP TABLE IF EXISTS {nom}")
