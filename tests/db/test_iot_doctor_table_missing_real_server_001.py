"""`iot:doctor` distingue « table absente » d'une panne, sur les trois moteurs (IOT-DOCTOR-MISSING-TABLE-001).

`check_database_table` sépare deux situations que l'exploitant ne traite pas de
la même façon :

- la table manque, la migration n'a pas été appliquée. Le diagnostic doit dire
  `warn` et conseiller `forge iot:init` puis `forge migration:apply` ;
- la base est injoignable. Le diagnostic doit dire `fail`.

Cette distinction repose sur `_is_table_missing_error`, qui ne reconnaissait
que MariaDB : le code d'erreur 1146 et la locution anglaise « doesn't exist ».
Aucun serveur ne l'avait jamais exercée.

Un exploitant PostgreSQL ou SQL Server qui oubliait sa migration recevait donc
un `fail` annonçant une base injoignable, avec un message parlant de MariaDB.
Le diagnostic désignait la mauvaise cause, ce qui est pire qu'un silence : il
envoie chercher ailleurs.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.cli.doctor import check_database_table

pytestmark = pytest.mark.db


@pytest.fixture
def base_sans_table(real_backend_db: str):
    """Une base joignable où `iot_events` n'existe simplement pas.

    C'est l'état exact d'un projet dont la migration n'a pas été appliquée, et
    il n'y a pas d'autre façon honnête de le produire que de ne pas créer la
    table.
    """
    from core.database import db

    try:
        db.execute("DROP TABLE iot_events")
    except Exception:  # noqa: BLE001 — l'absence est précisément ce qu'on veut
        pass
    return db


def test_une_table_absente_est_un_avertissement_pas_une_panne(base_sans_table: Any) -> None:
    """LE test : le diagnostic doit désigner la bonne cause sur les trois moteurs."""
    resultat = check_database_table(
        lambda sql, params: base_sans_table.fetch_one(sql, params)
    )

    assert resultat.status == "warn", (
        f"statut « {resultat.status} » au lieu de « warn » : le diagnostic prend "
        "une migration oubliée pour une base injoignable, et envoie l'exploitant "
        f"chercher la mauvaise cause. Détail rendu : {resultat.detail}"
    )
    assert "migration" in " ".join(resultat.lines).lower(), (
        "le conseil doit nommer la migration à appliquer"
    )


def test_une_base_injoignable_reste_une_panne() -> None:
    """L'autre moitié : sans elle, rendre toujours `warn` passerait le test précédent."""

    def toujours_en_panne(sql: str, params: Any) -> Any:
        raise ConnectionError("connexion refusée par le serveur")

    resultat = check_database_table(toujours_en_panne)

    assert resultat.status == "fail", (
        "une base injoignable doit rester une panne, sinon le diagnostic "
        "conseille d'appliquer une migration qui ne réglera rien"
    )


def test_une_table_presente_est_un_succes(real_backend_db: str) -> None:
    """Le cas nominal, pour que les deux autres ne soient pas lus comme la règle."""
    from forge_mvc_iot.tables import IOT_EVENTS

    from forge_mvc_testing.real_db import tables_temporaires

    with tables_temporaires(IOT_EVENTS) as db:
        resultat = check_database_table(lambda sql, params: db.fetch_one(sql, params))

    assert resultat.status == "ok", f"détail rendu : {resultat.detail}"
