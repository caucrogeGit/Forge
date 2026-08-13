"""Les lectures de stats et d'IoT s'exécutent sur les trois moteurs (STATS-IOT-SELECT-REAL-001).

Le relevé des surfaces publiques a montré que **huit constructeurs de SQL** de
ces deux opt-ins n'étaient jamais exécutés : les tests comparaient la chaîne
produite à une chaîne attendue, sans jamais la soumettre à un moteur.

C'est la signature qui explique la majorité des défauts de ce pré-mortem. Une
requête peut être exactement celle qu'on voulait écrire et rester refusée par
le serveur, ou rendre des clés que l'appelant ne sait pas lire.

Deux propriétés se jouent ici, et aucune n'est visible sur la chaîne :

- la borne dialectale doit s'assembler correctement. T-SQL rend
  `" OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY"`, qui exige un `ORDER BY` **et** un
  paramètre supplémentaire, là où `LIMIT ?` des autres moteurs se contente de
  suivre ;
- les alias non protégés sont repliés en minuscules par PostgreSQL, et
  l'appelant lit alors une clé qui n'existe pas.
"""
from __future__ import annotations

from typing import Any

import pytest

from core.database.timestamps import utc_now
from forge_mvc_testing.real_db import tables_temporaires

pytestmark = pytest.mark.db


# ── forge-mvc-stats ───────────────────────────────────────────────────────────

@pytest.fixture
def stats(real_backend_db: str):
    """Six événements, trois catégories, de quoi faire mentir un GROUP BY."""
    pytest.importorskip("forge_mvc_stats")
    from forge_mvc_stats.tables import STATS_EVENTS, STATS_EVENTS_TABLE

    with tables_temporaires(STATS_EVENTS) as db:
        maintenant = utc_now()
        evenements = [
            ("page.view", "Page vue", "trafic"),
            ("page.view", "Page vue", "trafic"),
            ("page.view", "Page vue", "trafic"),
            ("user.login", "Connexion", "auth"),
            ("user.login", "Connexion", "auth"),
            ("export.csv", "Export CSV", "outil"),
        ]
        for nom, libelle, categorie in evenements:
            db.execute(
                f"INSERT INTO {STATS_EVENTS_TABLE} "
                "(name, label, category, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (nom, libelle, categorie, None, maintenant),
            )
        yield db


def test_l_agregat_par_nom_s_execute_et_compte_juste(stats: Any) -> None:
    """`GROUP BY` avec alias, ordonné sur un alias : trois pièges d'un coup."""
    from forge_mvc_stats.aggregate import get_stats_counts_sql

    sql = get_stats_counts_sql("name")
    lignes = stats.fetch_all(sql, ())

    assert [(l["bucket"], l["total"]) for l in lignes] == [
        ("page.view", 3),
        ("user.login", 2),
        ("export.csv", 1),
    ], "l'agrégat doit trier par total décroissant, puis par bucket croissant"


def test_l_agregat_filtre_par_categorie(stats: Any) -> None:
    """Le filtre optionnel ajoute un `?`, dont l'ordre doit survivre au moteur."""
    from forge_mvc_stats.aggregate import get_stats_counts_sql

    sql = get_stats_counts_sql("name", category="auth")
    lignes = stats.fetch_all(sql, ("auth",))

    assert [(l["bucket"], l["total"]) for l in lignes] == [("user.login", 2)]


def test_la_liste_d_administration_respecte_sa_borne(stats: Any) -> None:
    """LE test de la borne dialectale : T-SQL exige un paramètre de plus.

    Une borne écrite en dur rendait cette lecture inutilisable sur SQL Server.
    Le correctif était posé, mais jamais exécuté : la chaîne était comparée à
    une chaîne, ce qui ne dit rien du nombre de paramètres attendus.
    """
    from forge_mvc_stats.admin import get_stats_events_admin_sql

    sql = get_stats_events_admin_sql(limit=2)
    lignes = stats.fetch_all(sql, (2,))

    assert len(lignes) == 2, (
        f"la borne n'a pas été appliquée : {len(lignes)} lignes rendues au lieu de 2"
    )


def test_le_comptage_et_la_purge_de_retention_s_executent(stats: Any) -> None:
    """Compter puis supprimer, les deux moitiés de `stats:gc` (charte §7)."""
    from forge_mvc_stats.retention import (
        get_stats_count_before_sql,
        get_stats_purge_sql,
    )

    # Une borne située dans le futur : tout est antérieur.
    from datetime import timedelta

    borne = (utc_now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    ligne = stats.fetch_one(get_stats_count_before_sql(), (borne,))
    assert ligne is not None
    assert int(ligne["total"]) == 6

    stats.execute(get_stats_purge_sql(), (borne,))

    apres = stats.fetch_one(get_stats_count_before_sql(), (borne,))
    assert apres is not None
    assert int(apres["total"]) == 0, "la purge doit vider ce qu'elle a compté"


# ── forge-mvc-iot ─────────────────────────────────────────────────────────────

@pytest.fixture
def iot(real_backend_db: str):
    """Trois relevés, deux appareils, pour que la restriction ait un effet."""
    pytest.importorskip("forge_mvc_iot")
    from forge_mvc_iot.mqtt.contract import Measurement
    from forge_mvc_iot.storage.events import build_insert_iot_event_sql
    from forge_mvc_iot.tables import IOT_EVENTS

    with tables_temporaires(IOT_EVENTS) as db:
        releves = [
            ("atelier", "sonde-1", 21.5),
            ("atelier", "sonde-1", 22.0),
            ("atelier", "sonde-2", 19.0),
        ]
        for site, appareil, valeur in releves:
            sql, params = build_insert_iot_event_sql(
                Measurement(
                    site=site,
                    device_id=appareil,
                    kind="temperature",
                    value=valeur,
                    unit="C",
                    timestamp="2026-08-13T12:00:00Z",
                    metadata=None,
                )
            )
            db.execute(sql, params)
        yield db


def test_la_lecture_recente_s_execute_avec_sa_borne(iot: Any) -> None:
    """`ORDER BY` suivi de la borne du dialecte, assemblés sans espace manquant.

    Le `f"{_limit_clause()}"` colle la borne à l'`ORDER BY` précédent. Une
    chaîne mal jointe passe inaperçue en comparaison de chaînes et n'échoue
    qu'au moteur.
    """
    from forge_mvc_iot.storage.repository import select_iot_events_recent_sql

    lignes = iot.fetch_all(select_iot_events_recent_sql(), (2,))

    assert len(lignes) == 2
    assert {l["device_id"] for l in lignes} <= {"sonde-1", "sonde-2"}
    # Les colonnes lues doivent porter les noms attendus par l'appelant.
    assert "received_at" in lignes[0]
    assert "value" in lignes[0]


def test_la_lecture_par_appareil_ordonne_ses_parametres(iot: Any) -> None:
    """Deux `?` de filtre **puis** celui de la borne : l'ordre est le piège.

    T-SQL annonce le décalage avant le nombre de lignes, l'inverse de `LIMIT`.
    Un test sur la chaîne ne peut pas voir une inversion de paramètres.
    """
    from forge_mvc_iot.storage.repository import select_iot_events_by_device_sql

    lignes = iot.fetch_all(select_iot_events_by_device_sql(), ("atelier", "sonde-1", 5))

    assert len(lignes) == 2, "seuls les deux relevés de sonde-1 doivent remonter"
    assert {l["device_id"] for l in lignes} == {"sonde-1"}


def test_le_comptage_par_appareil_s_execute(iot: Any) -> None:
    """Constante sans borne, donc sans dialecte, mais jamais exécutée non plus."""
    from forge_mvc_iot.storage.repository import COUNT_IOT_EVENTS_BY_DEVICE_SQL

    ligne = iot.fetch_one(COUNT_IOT_EVENTS_BY_DEVICE_SQL, ("atelier", "sonde-2"))

    assert ligne is not None
    assert int(ligne["n"]) == 1
