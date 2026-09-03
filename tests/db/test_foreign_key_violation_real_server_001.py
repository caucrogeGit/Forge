"""`DB-ERROR-MESSAGES-HOMOGENES-001` — la clé étrangère, sur serveurs réels.

Le doublon, la table absente, l'indisponibilité et le droit refusé étaient
qualifiés. **Pas la clé étrangère**, qui est pourtant l'erreur d'écriture la
plus courante après le doublon : supprimer une ligne encore référencée, ou
poser une référence qui n'existe pas.

L'exception du pilote remontait donc telle quelle, ce que l'ADR-054 refuse
précisément : une application ne doit jamais avoir à attraper
`mariadb.IntegrityError` sous peine de n'être portable nulle part.

Aucun signal n'est portable, et c'est la raison d'être de ce test : les quatre
sont vérifiés contre un serveur réel, jamais contre une exception fabriquée à
la main, qui prouverait seulement que le code fait ce qu'on croit.
"""
from __future__ import annotations

from typing import Any

import pytest

from core.database.errors import ForeignKeyViolationError
from core.database.qualify import qualify

pytestmark = pytest.mark.db


def _db() -> Any:
    """Accès base du backend monté par la fixture.

    `real_backend_db` rend le **nom** du backend et monte Forge dessus ; l'accès
    passe donc par `core.database.db`, comme dans une application.
    """
    from core.database import db

    return db


def _prepare(db: Any, prefixe: str) -> "tuple[str, str]":
    parent, enfant = f"{prefixe}_parent", f"{prefixe}_enfant"
    for table in (enfant, parent):
        try:
            db.execute(f"DROP TABLE {table}", ())
        except Exception:
            pass
    db.execute(f"CREATE TABLE {parent} (id INT NOT NULL PRIMARY KEY)", ())
    db.execute(
        f"CREATE TABLE {enfant} ("
        f"id INT NOT NULL PRIMARY KEY, "
        f"parent_id INT NOT NULL, "
        f"CONSTRAINT fk_{prefixe} FOREIGN KEY (parent_id) REFERENCES {parent} (id))",
        (),
    )
    db.execute(f"INSERT INTO {parent} (id) VALUES (1)", ())
    db.execute(f"INSERT INTO {enfant} (id, parent_id) VALUES (1, 1)", ())
    return parent, enfant


def _nettoyer(db: Any, parent: str, enfant: str) -> None:
    for table in (enfant, parent):
        try:
            db.execute(f"DROP TABLE {table}", ())
        except Exception:
            pass


class TestSurServeurReel:

    def test_une_suppression_referencee_est_qualifiee(self, real_backend_db: Any) -> None:
        """Supprimer une catégorie que des articles désignent encore."""
        parent, enfant = _prepare(_db(), "fkv_del")
        try:
            with pytest.raises(Exception) as leve:
                _db().execute(f"DELETE FROM {parent} WHERE id = 1", ())
            assert isinstance(qualify(leve.value), ForeignKeyViolationError), (
                f"non qualifiée : {type(leve.value).__name__} — {leve.value}"
            )
        finally:
            _nettoyer(_db(), parent, enfant)

    def test_une_reference_inexistante_est_qualifiee(self, real_backend_db: Any) -> None:
        """Poser `categorie_id = 42` quand aucune catégorie ne porte cet identifiant."""
        parent, enfant = _prepare(_db(), "fkv_ins")
        try:
            with pytest.raises(Exception) as leve:
                _db().execute(
                    f"INSERT INTO {enfant} (id, parent_id) VALUES (2, 999)", ()
                )
            assert isinstance(qualify(leve.value), ForeignKeyViolationError), (
                f"non qualifiée : {type(leve.value).__name__} — {leve.value}"
            )
        finally:
            _nettoyer(_db(), parent, enfant)

    def test_un_doublon_ne_devient_pas_une_cle_etrangere(
        self, real_backend_db: Any
    ) -> None:
        """Les deux signaux ne se recouvrent sur aucun backend.

        Une erreur mal nommée envoie chercher au mauvais endroit, et c'est la
        seule chose qu'une qualification puisse rendre pire qu'une absence de
        qualification.
        """
        from core.database.errors import UniqueViolationError

        parent, enfant = _prepare(_db(), "fkv_dup")
        try:
            with pytest.raises(Exception) as leve:
                _db().execute(f"INSERT INTO {parent} (id) VALUES (1)", ())
            assert isinstance(qualify(leve.value), UniqueViolationError)
        finally:
            _nettoyer(_db(), parent, enfant)


class TestSqlite:
    """SQLite ne passe pas par `real_backend_db`, n'ayant pas de serveur.

    Le couvrir importe pourtant : c'est le seul des quatre où le signal est le
    **message**, faute de code d'erreur, et donc le plus fragile.
    """

    def test_les_deux_situations_sont_qualifiees(self, tmp_path: Any) -> None:
        import sqlite3

        from forge_mvc_sqlite.backend import SQLiteBackend  # type: ignore[import-not-found]

        chemin = tmp_path / "fk.sqlite3"
        con = sqlite3.connect(chemin)
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
        con.execute(
            "CREATE TABLE enfant (id INTEGER PRIMARY KEY, parent_id INTEGER "
            "NOT NULL REFERENCES parent(id))"
        )
        con.execute("INSERT INTO parent (id) VALUES (1)")
        con.execute("INSERT INTO enfant (id, parent_id) VALUES (1, 1)")

        backend = SQLiteBackend.__new__(SQLiteBackend)

        with pytest.raises(sqlite3.IntegrityError) as suppression:
            con.execute("DELETE FROM parent WHERE id = 1")
        assert backend.is_foreign_key_violation(suppression.value)

        with pytest.raises(sqlite3.IntegrityError) as insertion:
            con.execute("INSERT INTO enfant (id, parent_id) VALUES (2, 999)")
        assert backend.is_foreign_key_violation(insertion.value)

        with pytest.raises(sqlite3.IntegrityError) as doublon:
            con.execute("INSERT INTO parent (id) VALUES (1)")
        assert not backend.is_foreign_key_violation(doublon.value), (
            "un doublon ne doit pas passer pour une clé étrangère"
        )
        con.close()

    def test_la_casse_du_message_ne_compte_pas(self) -> None:
        """La bibliothèque a changé la casse de ce message entre deux versions."""
        from forge_mvc_sqlite.backend import SQLiteBackend  # type: ignore[import-not-found]

        backend = SQLiteBackend.__new__(SQLiteBackend)

        assert backend.is_foreign_key_violation(Exception("FOREIGN KEY constraint failed"))
        assert backend.is_foreign_key_violation(Exception("foreign key constraint failed"))
