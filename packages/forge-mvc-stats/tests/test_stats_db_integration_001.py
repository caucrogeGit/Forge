"""Intégration de forge-mvc-stats sur les trois serveurs (STATS-RETENTION-001).

Le paquet n'avait aucun test d'intégration : il rendait du SQL que personne
n'exécutait jamais. Rendre un DDL et l'appliquer sont deux choses, et le second
est le seul qui prouve quoi que ce soit à l'exploitant.

Ce fichier applique réellement la migration déclarée par `tables.py`, écrit des
événements, puis vérifie la purge par âge et la liste d'administration.

## Ce qui a changé (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`)

Ce fichier montait sa propre connexion MariaDB dans un adaptateur écrit à la
main. Il ne tournait donc que sur MariaDB, et court-circuitait la vraie couche
d'accès `core.database.db`, celle que l'application utilise en production.
Les tests passent désormais par `real_backend_db` : chacun s'exécute trois
fois, une par serveur, à travers la couche réelle.

La liste d'administration entre dans le relevé au passage. Sa borne était écrite
en `LIMIT ?` en dur, donc rejetée par SQL Server, et rien ici ne l'exerçait
(`ADMIN-JOBS-LIMIT-PORTABLE-001`).
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats.retention import (
    count_stats_events_before,
    cutoff_for_days,
    purge_stats_events_before,
)
from forge_mvc_stats.tracking import track_event

from forge_mvc_testing.real_db import tables_temporaires


@pytest.fixture
def stats_db(real_backend_db: str) -> Iterator[Any]:
    """Table des événements créée par sa DDL dialectale, sur le serveur du cas."""
    from forge_mvc_stats.tables import STATS_EVENTS

    with tables_temporaires(STATS_EVENTS) as db:
        yield db


def _inserer_date(db: Any, nom: str, created_at: str) -> None:
    db.execute(
        "INSERT INTO forge_stats_events (name, label, category, created_at) "
        "VALUES (?, ?, ?, ?)",
        (nom, nom, "general", created_at),
    )


def test_la_migration_declaree_s_applique_vraiment(stats_db: Any) -> None:
    """La fixture a appliqué le DDL : si elle a tenu, la table existe.

    C'est le test qui manquait le plus. Le paquet rendait un DDL que rien
    n'exécutait jamais, donc une erreur de rendu ne se serait vue qu'en
    production, et seulement sur le moteur concerné.
    """
    row = stats_db.fetch_one("SELECT COUNT(*) AS total FROM forge_stats_events", ())

    assert row is not None
    assert row["total"] == 0


def test_un_evenement_suivi_atterrit_dans_la_table(stats_db: Any) -> None:
    track_event(stats_db.execute, "page_vue", label="Page vue")

    row = stats_db.fetch_one("SELECT COUNT(*) AS total FROM forge_stats_events", ())
    assert row is not None
    assert row["total"] == 1


def test_la_liste_d_administration_traverse_le_moteur(stats_db: Any) -> None:
    """La borne de la liste vient du dialecte : `LIMIT ?` en dur cassait SQL Server.

    Le défaut a été trouvé en élargissant le relevé de portabilité DML, et non
    ici : ce fichier n'exerçait pas la liste. Il l'exerce maintenant, sur les
    trois serveurs.
    """
    from forge_mvc_stats.admin import list_stats_events

    for index in range(4):
        track_event(stats_db.execute, f"vue_{index}", label=f"Vue {index}")

    lignes = list_stats_events(stats_db.fetch_all, limit=2)
    assert len(lignes) == 2
    assert lignes[0]["name"] == "vue_3"  # created_at DESC, id DESC
    assert lignes[0]["metadata"] == {}


def test_la_purge_ne_retire_que_les_evenements_anterieurs(stats_db: Any) -> None:
    """LE test du ticket : la borne discrimine, elle ne vide pas la table."""
    _inserer_date(stats_db, "vieux", "2020-01-01 00:00:00")
    _inserer_date(stats_db, "recent", "2026-08-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_stats_events_before(stats_db.fetch_one, borne) == 1
    assert purge_stats_events_before(stats_db.execute, borne) == 1

    restant = stats_db.fetch_one("SELECT name FROM forge_stats_events", ())
    assert restant is not None
    assert restant["name"] == "recent"


def test_le_comptage_ne_supprime_rien(stats_db: Any) -> None:
    _inserer_date(stats_db, "vieux", "2020-01-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_stats_events_before(stats_db.fetch_one, borne) == 1
    assert count_stats_events_before(stats_db.fetch_one, borne) == 1


def test_la_borne_calculee_en_jours_s_applique_reellement(stats_db: Any) -> None:
    """Point de jonction entre le calcul Python et la colonne SQL.

    Un format d'horodatage divergent passerait les tests unitaires et
    n'échouerait qu'ici, et il peut diverger par moteur.
    """
    from datetime import datetime, timedelta, timezone

    maintenant = datetime.now(timezone.utc)
    _inserer_date(
        stats_db, "vieux", (maintenant - timedelta(days=400)).strftime("%Y-%m-%d %H:%M:%S")
    )
    _inserer_date(
        stats_db, "recent", (maintenant - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    )

    assert purge_stats_events_before(stats_db.execute, cutoff_for_days(365)) == 1
    restant = stats_db.fetch_one("SELECT name FROM forge_stats_events", ())
    assert restant is not None
    assert restant["name"] == "recent"
