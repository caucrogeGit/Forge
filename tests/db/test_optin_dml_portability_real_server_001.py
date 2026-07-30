"""OPTIN-DML-DIALECT-001 : la DML des opt-ins BDD tourne sur les quatre backends.

Un audit précédent avait rendu la **DDL** de ces paquets dialectale
(`OPTIN-DDL-DIALECT-AUDIT-001`), et s'était arrêté là. La **DML**, elle, était
restée en SQL MariaDB. Mesuré avant correctif, tables créées par la voie
dialectale puis opérations réelles :

    PostgreSQL   4 opérations cassées
    SQL Server   5 opérations cassées
    SQLite       5 opérations cassées

Trois constructions en cause, dont aucune n'est portable : `NOW()`, absent de
SQL Server et de SQLite ; `NOW() + INTERVAL ? SECOND` ; `ON DUPLICATE KEY
UPDATE`, propre à MySQL et MariaDB. La doc de `settings` promettait pourtant
les quatre backends.

La cause de l'invisibilité est structurelle : chaque paquet a bien son test
d'intégration, mais tous portent le seul marqueur `db`, donc ne s'exécutent que
contre MariaDB. Ce fichier est le pendant croisé qui manquait, et c'est
lui qui empêche la dérive de revenir.

Le pendant hors base est `tests/test_optin_dml_dialect_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.db

_TABLES = ("jobs", "notifications", "app_settings")


def _jeter(db: Any, backend_name: str) -> None:
    for nom in _TABLES:
        if backend_name == "mssql":
            db.execute(f"IF OBJECT_ID('{nom}') IS NOT NULL DROP TABLE {nom}")
        else:
            db.execute(f"DROP TABLE IF EXISTS {nom}")


@pytest.fixture()
def opt_ins_prets():
    """Crée les tables des trois opt-ins par leur DDL dialectale."""
    from core.database import db
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_jobs import tables as JT
    from forge_mvc_notifications import tables as NT
    from forge_mvc_settings import tables as ST

    backend = get_backend()
    _jeter(db, backend.name)
    for table in (JT.JOBS, NT.NOTIFICATIONS, ST.APP_SETTINGS):
        for sql in render_create_table(table, backend.dialect):
            db.execute(sql)
    yield db
    _jeter(db, backend.name)


def _exercer_les_trois_opt_ins(db: Any) -> None:
    """Les treize opérations du relevé, dans l'ordre d'un usage réel."""
    from forge_mvc_jobs import queue as Q
    from forge_mvc_notifications import store as NS
    from forge_mvc_settings import store as SS

    # jobs : mise en file, comptage, traitement.
    Q.enqueue("courriel", {"a": 1}, queue="q")
    assert Q.pending_count(queue="q") == 1
    traitees: "list[dict[str, Any]]" = []
    assert Q.process_one({"courriel": traitees.append}, queue="q") is True
    assert traitees == [{"a": 1}]
    assert Q.pending_count(queue="q") == 0

    # notifications : envoi, comptage, marquage.
    NS.notify("roger", "bonjour")
    assert NS.unread_count("roger") == 1
    assert NS.mark_all_read("roger") == 1
    assert NS.unread_count("roger") == 0

    # settings : création puis mise à jour de la même clé (upsert).
    SS.set_setting("theme", "clair")
    assert SS.get_setting("theme") == "clair"
    SS.set_setting("theme", "sombre")
    assert SS.get_setting("theme") == "sombre"


def test_mariadb_les_trois_opt_ins_fonctionnent(real_db: None, opt_ins_prets) -> None:
    _exercer_les_trois_opt_ins(opt_ins_prets)


@pytest.mark.db_pg
def test_postgres_les_trois_opt_ins_fonctionnent(
    real_pg_db: None, opt_ins_prets,
) -> None:
    """Cassait sur enqueue, process_one et set_setting."""
    _exercer_les_trois_opt_ins(opt_ins_prets)


@pytest.mark.db_mssql
def test_mssql_les_trois_opt_ins_fonctionnent(
    real_mssql_db: None, opt_ins_prets,
) -> None:
    """Cassait sur enqueue, process_one, mark_all_read et set_setting."""
    _exercer_les_trois_opt_ins(opt_ins_prets)


def test_mariadb_une_tache_reservee_ne_l_est_pas_deux_fois(
    real_db: None, opt_ins_prets,
) -> None:
    """La réservation en deux temps doit rester exclusive.

    `UPDATE ... ORDER BY id LIMIT 1` réservait en une instruction, extension que
    seul MariaDB accepte. Le motif portable choisit d'abord une candidate, puis
    la réserve sous garde `status='pending'` : deux ouvriers qui visent la même
    ligne ne peuvent pas gagner tous les deux.
    """
    from forge_mvc_jobs import queue as Q

    Q.enqueue("courriel", {"n": 1}, queue="solo")
    vues: "list[dict[str, Any]]" = []

    assert Q.process_one({"courriel": vues.append}, queue="solo") is True
    assert Q.process_one({"courriel": vues.append}, queue="solo") is False
    assert len(vues) == 1, "une tâche ne doit être traitée qu'une fois"
