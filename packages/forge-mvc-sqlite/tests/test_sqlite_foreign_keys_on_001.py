"""SQLITE-FOREIGN-KEYS-ON-001 — SQLite applique enfin les clés étrangères.

SQLite laisse `PRAGMA foreign_keys` à 0 par défaut, par compatibilité
ascendante, et le réglage est propre à la connexion. Forge ne l'armait nulle
part : les contraintes que `make:relation` écrit dans la DDL ne contraignaient
rien. Mesuré avant correctif, sur un vrai fichier :

    enfant orphelin (auteur_id = 999)   accepté
    parent supprimé                     ses enfants restaient, sans cascade

Le sens de la dérive commandait de corriger : SQLite sert en développement, les
SGBD serveur en production. Le défaut ne se voyait donc jamais chez le
développeur, toujours chez l'utilisateur, et sur des données déjà incohérentes.

SQLite étant dans la bibliothèque standard, tout est éprouvé ici de bout en
bout sur un vrai fichier : aucun serveur, donc aucune raison de reléguer ces
preuves derrière le marqueur `db`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.database.errors import ForeignKeyViolationError

pytest.importorskip("forge_mvc_sqlite")

import core.forge as forge  # noqa: E402
from forge_mvc_sqlite.backend import SQLiteBackend  # noqa: E402
from forge_mvc_sqlite.dialect import SQLiteDialect  # noqa: E402

_SCHEMA = (
    "CREATE TABLE auteur (id INTEGER PRIMARY KEY, nom TEXT)",
    "CREATE TABLE livre ("
    " id INTEGER PRIMARY KEY,"
    " titre TEXT,"
    " auteur_id INTEGER NOT NULL,"
    " CONSTRAINT fk_livre_auteur FOREIGN KEY (auteur_id)"
    "   REFERENCES auteur(id) ON DELETE CASCADE)",
)


@pytest.fixture()
def base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Une base de deux tables reliées, servie par le backend SQLite."""
    forge.configure(app_name="forge_sqlite_fk_test")
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("DB_NAME", str(tmp_path / "app.db"))
    from core.database import backend as backend_module
    from core.database import db

    backend_module.reset_backend()
    # SQLITE-RUNTIME-NO-CREATE-001 : seule la porte de provisionnement crée le
    # fichier, comme le ferait `forge db:init`.
    SQLiteBackend().get_admin_connection().close()
    try:
        for statement in _SCHEMA:
            db.execute(statement)
        db.execute("INSERT INTO auteur (id, nom) VALUES (?, ?)", (1, "Hugo"))
        db.execute("INSERT INTO livre (id, titre, auteur_id) VALUES (?, ?, ?)",
                   (1, "Les Misérables", 1))
        yield db
    finally:
        backend_module.reset_backend()


# ── Les contraintes contraignent ─────────────────────────────────────────────

def test_le_pragma_est_arme_sur_toute_connexion_empruntee(base) -> None:
    assert base.fetch_one("PRAGMA foreign_keys") == {"foreign_keys": 1}


def test_un_enfant_orphelin_est_refuse(base) -> None:
    """Le cas mesuré : `auteur_id = 999` entrait sans broncher."""

    # DB-ERROR-MESSAGES-HOMOGENES-001 : la violation est désormais qualifiée.
    # Le test attendait `sqlite3.IntegrityError`, ce que l'ADR-054 refuse :
    # une application qui attrape l'exception d'un pilote n'est portable
    # sur aucun autre backend. L'exception d'origine reste en `__cause__`.
    with pytest.raises(ForeignKeyViolationError, match="FOREIGN KEY"):
        base.insert("INSERT INTO livre (titre, auteur_id) VALUES (?, ?)",
                    ("Fantôme", 999))


def test_la_suppression_du_parent_cascade(base) -> None:
    """`ON DELETE CASCADE` était écrit dans la DDL et ne cascadait pas."""
    base.execute("DELETE FROM auteur WHERE id = ?", (1,))

    assert base.fetch_all("SELECT id FROM livre") == []


def test_la_contrainte_tient_aussi_dans_un_bloc_transaction(base) -> None:
    """L'ordre compte : le pragma est sans effet dans une transaction ouverte.

    Armé à l'emprunt, il survit au désarmement d'autocommit que
    `core.database.transaction` opère juste après. Cette preuve est le pendant
    du commentaire d'ordre laissé dans le backend.
    """

    from core.database.transaction import transaction

    # DB-ERROR-MESSAGES-HOMOGENES-001 : la violation est désormais qualifiée.
    # Le test attendait `sqlite3.IntegrityError`, ce que l'ADR-054 refuse :
    # une application qui attrape l'exception d'un pilote n'est portable
    # sur aucun autre backend. L'exception d'origine reste en `__cause__`.
    with pytest.raises(ForeignKeyViolationError, match="FOREIGN KEY"):
        with transaction() as tx:
            base.insert("INSERT INTO livre (titre, auteur_id) VALUES (?, ?)",
                        ("Fantôme", 999), tx=tx)


def test_chaque_emprunt_repart_arme(base) -> None:
    """Le réglage est propre à la connexion : il doit être posé à chaque fois."""
    for _ in range(3):
        assert base.fetch_one("PRAGMA foreign_keys") == {"foreign_keys": 1}


# ── Le levier de fixtures:load --no-fk-checks ────────────────────────────────

def test_le_levier_du_dialecte_agit_dans_une_transaction(base) -> None:
    """`PRAGMA foreign_keys` n'y agirait pas : c'est tout le sujet du report."""
    from core.database.transaction import transaction

    dialect = SQLiteDialect()
    with transaction() as tx:
        for statement in dialect.foreign_key_checks_ddl(enabled=False):
            base.execute(statement, tx=tx)
        # L'enfant arrive avant son parent : c'est le cycle de dépendances que
        # l'option sert à charger.
        base.execute("INSERT INTO livre (id, titre, auteur_id) VALUES (?, ?, ?)",
                     (2, "Hernani", 7), tx=tx)
        base.execute("INSERT INTO auteur (id, nom) VALUES (?, ?)", (7, "Hugo bis"), tx=tx)
        for statement in dialect.foreign_key_checks_ddl(enabled=True):
            base.execute(statement, tx=tx)

    assert base.fetch_one("SELECT auteur_id FROM livre WHERE id = ?", (2,)) == {
        "auteur_id": 7
    }


def test_le_report_n_est_pas_une_desactivation(base) -> None:
    """Un parent qui n'arrive jamais fait toujours échouer le chargement.

    Différence assumée avec MariaDB, qui désactive vraiment : ce que SQLite
    offre est un report de la vérification au `COMMIT`, pas son abandon.
    """

    from core.database.transaction import transaction

    dialect = SQLiteDialect()
    # DB-ERROR-MESSAGES-HOMOGENES-001 : la violation est désormais qualifiée.
    # Le test attendait `sqlite3.IntegrityError`, ce que l'ADR-054 refuse :
    # une application qui attrape l'exception d'un pilote n'est portable
    # sur aucun autre backend. L'exception d'origine reste en `__cause__`.
    with pytest.raises(ForeignKeyViolationError, match="FOREIGN KEY"):
        with transaction() as tx:
            for statement in dialect.foreign_key_checks_ddl(enabled=False):
                base.execute(statement, tx=tx)
            base.execute("INSERT INTO livre (id, titre, auteur_id) VALUES (?, ?, ?)",
                         (3, "Sans auteur", 404), tx=tx)

    assert base.fetch_all("SELECT id FROM livre WHERE id = ?", (3,)) == []


def test_le_report_ne_fuit_pas_vers_l_emprunt_suivant(base) -> None:
    """Il se remet seul à la fin de la transaction : rien à restaurer."""
    from core.database.transaction import transaction

    dialect = SQLiteDialect()
    with transaction() as tx:
        for statement in dialect.foreign_key_checks_ddl(enabled=False):
            base.execute(statement, tx=tx)

    assert base.fetch_one("PRAGMA defer_foreign_keys") == {"defer_foreign_keys": 0}
    assert base.fetch_one("PRAGMA foreign_keys") == {"foreign_keys": 1}


# ── Le contrat du backend ────────────────────────────────────────────────────

def test_le_backend_arme_meme_hors_facade(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """Un appelant direct de `get_connection()` reçoit la même garantie."""
    forge.configure(app_name="forge_sqlite_fk_test")
    monkeypatch.setenv("DB_NAME", str(tmp_path / "direct.db"))
    backend = SQLiteBackend()
    backend.get_admin_connection().close()
    connection = backend.get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("PRAGMA foreign_keys")
        assert cursor.fetchone() == {"foreign_keys": 1}
        cursor.close()
    finally:
        backend.close_connection(connection)
