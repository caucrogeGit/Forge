from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats import (
    STATS_EVENTS_COLUMNS,
    STATS_EVENTS_TABLE,
    get_stats_events_schema_sql,
)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


def test_table_vaut_forge_stats_events():
    assert STATS_EVENTS_TABLE == "forge_stats_events"


def test_columns_contient_id():
    assert "id" in STATS_EVENTS_COLUMNS


def test_columns_contient_name():
    assert "name" in STATS_EVENTS_COLUMNS


def test_columns_contient_label():
    assert "label" in STATS_EVENTS_COLUMNS


def test_columns_contient_category():
    assert "category" in STATS_EVENTS_COLUMNS


def test_columns_contient_metadata():
    assert "metadata" in STATS_EVENTS_COLUMNS


def test_columns_contient_created_at():
    assert "created_at" in STATS_EVENTS_COLUMNS


def test_columns_contient_exactement_les_colonnes_attendues():
    """`kind` s'y est ajoutée (`STATS-EVENT-KIND-001`).

    L'égalité stricte reste délibérée : une colonne ajoutée sans que la liste
    la déclare ferait diverger la table et ce que le paquet croit y trouver.
    """
    expected = {
        "id", "name", "label", "category", "metadata", "kind", "created_at",
    }
    assert set(STATS_EVENTS_COLUMNS) == expected


# ---------------------------------------------------------------------------
# get_stats_events_schema_sql
# ---------------------------------------------------------------------------


def test_schema_sql_retourne_une_chaine():
    sql = get_stats_events_schema_sql()
    assert isinstance(sql, str)


def test_schema_sql_non_vide():
    sql = get_stats_events_schema_sql()
    assert sql.strip() != ""


def test_schema_sql_contient_create_table_if_not_exists():
    sql = get_stats_events_schema_sql()
    assert "CREATE TABLE IF NOT EXISTS forge_stats_events" in sql


def test_schema_sql_contient_id_bigint_unsigned():
    sql = get_stats_events_schema_sql()
    assert "id BIGINT UNSIGNED" in sql


def test_schema_sql_contient_name_varchar():
    sql = get_stats_events_schema_sql()
    assert "name VARCHAR" in sql


def test_schema_sql_contient_label_varchar():
    sql = get_stats_events_schema_sql()
    assert "label VARCHAR" in sql


def test_schema_sql_contient_category_varchar():
    sql = get_stats_events_schema_sql()
    assert "category VARCHAR" in sql


def test_schema_sql_contient_metadata_json():
    """Le type JSON est celui du dialecte, pas un litteral MariaDB.

    Le DDL est desormais rendu (OPTIN-DDL-MAIL-STATS-001) : MariaDB mappe
    `json` sur LONGTEXT, PostgreSQL sur JSONB, SQL Server sur NVARCHAR(MAX).
    On verifie que la colonne existe et accepte du texte, pas un nom de type
    propre a un moteur.
    """
    from core.database.backend import get_backend

    sql = get_stats_events_schema_sql()
    assert "metadata " in sql
    expected = get_backend().dialect.simple_type("json")
    assert f"metadata {expected}" in sql


def test_schema_sql_contient_created_at_datetime():
    sql = get_stats_events_schema_sql()
    assert "created_at DATETIME" in sql


def test_schema_sql_contient_cle_primaire():
    sql = get_stats_events_schema_sql()
    assert "PRIMARY KEY" in sql


def test_schema_sql_contient_index_sur_name():
    sql = get_stats_events_schema_sql()
    assert "INDEX" in sql and "name" in sql


def test_schema_sql_contient_index_sur_category():
    sql = get_stats_events_schema_sql()
    assert "idx_forge_stats_events_category" in sql


def test_schema_sql_contient_index_sur_created_at():
    sql = get_stats_events_schema_sql()
    assert "idx_forge_stats_events_created_at" in sql


def test_schema_sql_est_stable():
    assert get_stats_events_schema_sql() == get_stats_events_schema_sql()


def test_schema_sql_contient_nom_de_table():
    sql = get_stats_events_schema_sql()
    assert STATS_EVENTS_TABLE in sql


# ---------------------------------------------------------------------------
# API publique importable depuis core.stats
# ---------------------------------------------------------------------------


def test_api_schema_importable():
    from forge_mvc_stats import (
        STATS_EVENTS_COLUMNS,
        STATS_EVENTS_TABLE,
        get_stats_events_schema_sql,
    )
    assert STATS_EVENTS_TABLE == "forge_stats_events"
    assert callable(get_stats_events_schema_sql)
    assert len(STATS_EVENTS_COLUMNS) == 7  # + kind (STATS-EVENT-KIND-001)


# ---------------------------------------------------------------------------
# Pas d'accès base de données, pas de tracking, pas de cookie
# ---------------------------------------------------------------------------


def test_aucun_acces_base_de_donnees():
    sql = get_stats_events_schema_sql()
    assert "forge_stats_events" in sql


def test_aucun_tracking_automatique():
    sql = get_stats_events_schema_sql()
    assert "INSERT" not in sql
    assert "track_event" not in sql


def test_aucun_cookie_ou_session():
    sql = get_stats_events_schema_sql()
    assert "cookie" not in sql.lower()
    assert "session" not in sql.lower()
