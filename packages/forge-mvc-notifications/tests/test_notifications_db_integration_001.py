"""Intégration du store de notifications sur les trois serveurs (NOTIFICATIONS-DB-INTEGRATION-001).

Vérifie le contrat SQL réel face au moteur : la DDL dialectale, l'envoi, l'ordre
décroissant, le comptage des non lues et le marquage.

## Ce qui a changé (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`)

Ce fichier montait sa propre connexion MariaDB dans un adaptateur écrit à la
main. Il ne tournait donc que sur MariaDB, et court-circuitait la vraie couche
d'accès `core.database.db`, celle que l'application utilise en production.
Les tests passent désormais par `real_backend_db` : chacun s'exécute trois
fois, une par serveur, à travers la couche réelle.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

pytest.importorskip("forge_mvc_notifications")

from forge_mvc_notifications import (
    get_notifications,
    mark_all_read,
    mark_read,
    notify,
    unread_count,
)

from forge_mvc_testing.real_db import tables_temporaires


@pytest.fixture
def notif_db(real_backend_db: str) -> Iterator[None]:
    """Table des notifications créée par sa DDL dialectale, sur le serveur du cas."""
    from forge_mvc_notifications.tables import NOTIFICATIONS

    with tables_temporaires(NOTIFICATIONS):
        yield


@pytest.mark.usefixtures("notif_db")
def test_notify_then_read_most_recent_first() -> None:
    notify("eleve.42", "Première", data={"k": 1})
    notify("eleve.42", "Seconde")
    notify("autre", "x")
    entries = get_notifications("eleve.42")
    assert [n.message for n in entries] == ["Seconde", "Première"]
    assert entries[1].data == {"k": 1}


@pytest.mark.usefixtures("notif_db")
def test_unread_count_and_mark_read() -> None:
    nid = notify("eleve.42", "m")
    notify("eleve.42", "m2")
    assert unread_count("eleve.42") == 2
    assert mark_read(nid) is True
    assert mark_read(nid) is False  # déjà lue
    assert unread_count("eleve.42") == 1


@pytest.mark.usefixtures("notif_db")
def test_unread_only_filter() -> None:
    a = notify("r", "lu")
    notify("r", "non lu")
    mark_read(a)
    msgs = [n.message for n in get_notifications("r", unread_only=True)]
    assert msgs == ["non lu"]


@pytest.mark.usefixtures("notif_db")
def test_mark_all_read() -> None:
    notify("r", "1")
    notify("r", "2")
    assert mark_all_read("r") == 2
    assert unread_count("r") == 0
