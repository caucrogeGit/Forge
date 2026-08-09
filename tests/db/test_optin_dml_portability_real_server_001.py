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

## Élargissement (`OPTIN-DML-PORTABILITY-WIDEN-001`)

Ce fichier ne couvrait d'abord que trois paquets, `jobs`, `notifications` et
`settings`, par treize opérations choisies. Le pré-mortem de la rc5 a montré ce
que cette double restriction laissait passer.

`forge-mvc-admin` n'était pas couvert : ses `UPDATE ... LIMIT 1` et
`DELETE ... LIMIT 1`, extensions MySQL, **empêchaient le back-office de modifier
ou de supprimer un enregistrement sur PostgreSQL et sur SQL Server**.

Et pour `jobs`, l'opération fautive n'était pas dans les treize : `get_job`
portait un `LIMIT 1` qui le cassait sur SQL Server.

La leçon est que la couverture doit porter sur la **surface publique** d'un
paquet, pas sur un échantillon d'opérations jugées représentatives. Les paquets
`admin`, `audit`, `stats` et `mfa` sont donc ajoutés, et les opérations de
lecture unitaire avec eux.
"""
from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.db

_TABLES = (
    "jobs", "notifications", "app_settings",
    # OPTIN-DML-PORTABILITY-WIDEN-001 : paquets ajoutés au relevé.
    "audit_log", "forge_stats_events", "mfa_totp_replay",
    # Table applicative de démonstration : `forge-mvc-admin` n'a pas de
    # table à lui, il opère sur celles de l'application.
    "articles_admin",
)


def _jeter(db: Any, backend_name: str) -> None:
    for nom in _TABLES:
        if backend_name == "mssql":
            db.execute(f"IF OBJECT_ID('{nom}') IS NOT NULL DROP TABLE {nom}")
        else:
            db.execute(f"DROP TABLE IF EXISTS {nom}")


@pytest.fixture()
def opt_ins_prets():
    """Crée les tables des opt-ins couverts, par leur DDL dialectale."""
    from core.database import db
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from core.database.table_ddl import Column, TableDefinition
    from forge_mvc_audit import tables as AT
    from forge_mvc_jobs import tables as JT
    from forge_mvc_mfa import tables as MT
    from forge_mvc_notifications import tables as NT
    from forge_mvc_settings import tables as ST
    from forge_mvc_stats import tables as StT

    #: Table applicative servant de cible à `forge-mvc-admin`, décrite par le
    #: socle dialectal pour que le relevé ne dépende d'aucun SQL écrit à la main.
    articles = TableDefinition(
        name="articles_admin",
        columns=[
            Column("id", "identity"),
            Column("titre", "string", length=120),
            Column("resume", "text", nullable=True),
        ],
        primary_key=["id"],
    )

    backend = get_backend()
    _jeter(db, backend.name)
    for table in (
        JT.JOBS, NT.NOTIFICATIONS, ST.APP_SETTINGS,
        AT.AUDIT_LOG, StT.STATS_EVENTS, MT.TOTP_REPLAY, articles,
    ):
        for sql in render_create_table(table, backend.dialect):
            db.execute(sql)
    yield db
    _jeter(db, backend.name)


def _exercer_les_opt_ins(db: Any) -> None:
    """La surface publique des opt-ins couverts, dans l'ordre d'un usage réel.

    Le relevé porte sur ce que chaque paquet **expose**, pas sur un échantillon
    d'opérations jugées représentatives : c'est ce choix-là qui avait laissé
    passer `get_job` et tout `forge-mvc-admin`.
    """
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

    # jobs : lecture unitaire et reprise. `get_job` portait un `LIMIT 1` qui le
    # cassait sur SQL Server, et il n'était dans aucun des treize relevés.
    jid = Q.enqueue("differe", {"x": 1}, queue="q2", max_attempts=3)
    lu = Q.get_job(jid)
    assert lu is not None and lu.status == "pending" and lu.task == "differe"
    assert Q.get_job(10_000_000) is None
    assert Q.reclaim_stale(queue="q2", lease_seconds=900).total == 0

    # audit : écriture, lecture filtrée, comptage et purge par âge.
    from forge_mvc_audit import store as AS

    AS.record_audit("eleve.cree", actor="prof", target_type="eleve", target_id=1)
    assert len(AS.get_audit_log(action="eleve.cree")) == 1
    borne = AS.cutoff_for_days(1)
    assert AS.count_audit_before(borne) == 0
    assert AS.purge_audit_before(borne) == 0

    # stats : suivi, agrégation, liste et purge par âge.
    from forge_mvc_stats import admin as StA
    from forge_mvc_stats import aggregate as StAg
    from forge_mvc_stats import retention as StR
    from forge_mvc_stats import tracking as StTr

    StTr.track_event(db.execute, "page_vue", label="Page vue")
    assert StAg.count_stats_events(db.fetch_all, "name")[0]["total"] == 1
    assert len(StA.list_stats_events(db.fetch_all)) == 1
    borne_st = StR.cutoff_for_days(1)
    assert StR.count_stats_events_before(db.fetch_one, borne_st) == 0
    assert StR.purge_stats_events_before(db.execute, borne_st) == 0

    # mfa : magasin anti-rejeu partagé, `INSERT` puis `UPDATE` gardé.
    from forge_mvc_mfa.replay_store_db import DbTotpReplayStore

    magasin = DbTotpReplayStore()
    assert magasin.check_and_record(1, 1000) is True
    assert magasin.check_and_record(1, 1000) is False
    assert magasin.check_and_record(1, 1001) is True
    assert magasin.is_replay(1, 1000) is True
    assert magasin.purge_old(0.0) == 0

    # admin : les quatre requêtes du back-office, exécutées pour de vrai.
    # `UPDATE ... LIMIT` et `DELETE ... LIMIT` sont des extensions MySQL : le
    # back-office ne savait ni modifier ni supprimer sur PostgreSQL ni sur
    # SQL Server (`ADMIN-JOBS-LIMIT-PORTABLE-001`).
    from forge_mvc_admin.query import (
        build_count_sql, build_delete_sql, build_get_sql,
        build_insert_sql, build_list_sql, build_update_sql, list_params,
    )
    from forge_mvc_admin.resources import AdminResource

    ressource = AdminResource(
        entity="Article", slug="articles", label="Article", plural_label="Articles",
        list_fields=("id", "titre"), form_fields=("titre", "resume"),
        table="articles_admin", pk="id",
    )
    db.execute(build_insert_sql(ressource), ("Titre", "Resume"))
    assert db.fetch_one(build_count_sql(ressource), ())["total"] == 1
    assert len(db.fetch_all(build_list_sql(ressource), list_params(limit=20, offset=0))) == 1
    identifiant = db.fetch_all(build_list_sql(ressource), list_params(limit=20, offset=0))[0]["id"]
    assert db.fetch_all(build_get_sql(ressource), (identifiant,))
    db.execute(build_update_sql(ressource), ("Titre 2", "Resume 2", identifiant))
    db.execute(build_delete_sql(ressource), (identifiant,))
    assert db.fetch_one(build_count_sql(ressource), ())["total"] == 0


def test_mariadb_les_opt_ins_fonctionnent(real_db: None, opt_ins_prets) -> None:
    _exercer_les_opt_ins(opt_ins_prets)


@pytest.mark.db_pg
def test_postgres_les_opt_ins_fonctionnent(
    real_pg_db: None, opt_ins_prets,
) -> None:
    """Cassait sur enqueue, process_one et set_setting."""
    _exercer_les_opt_ins(opt_ins_prets)


@pytest.mark.db_mssql
def test_mssql_les_opt_ins_fonctionnent(
    real_mssql_db: None, opt_ins_prets,
) -> None:
    """Cassait sur enqueue, process_one, mark_all_read et set_setting."""
    _exercer_les_opt_ins(opt_ins_prets)


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
