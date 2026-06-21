"""Garde-fou STATS-AGGREGATION-001 (ADR-037).

L'agrégation par comptage : SQL paramétré, `group_by` en liste blanche stricte
(aucune injection par nom de colonne), cohérence SQL/params, normalisation.
"""

from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats import (
    StatsAggregateError,
    count_stats_events,
    get_stats_counts_sql,
    normalize_stats_count_row,
    prepare_stats_counts_params,
)


def test_sql_groupe_et_compte_par_dimension_autorisee() -> None:
    sql = get_stats_counts_sql("category")
    assert "COUNT(*) AS total" in sql
    assert "GROUP BY category" in sql
    assert "SELECT category AS bucket" in sql


@pytest.mark.parametrize("dimension", ["name", "category"])
def test_dimensions_en_liste_blanche_acceptees(dimension: str) -> None:
    sql = get_stats_counts_sql(dimension)
    assert f"GROUP BY {dimension}" in sql


@pytest.mark.parametrize(
    "mauvais",
    ["created_at", "bucket", "id", "name; DROP TABLE stats_events--", "(SELECT 1)", "", "NAME"],
)
def test_group_by_hors_liste_blanche_rejete(mauvais: str) -> None:
    with pytest.raises(StatsAggregateError):
        get_stats_counts_sql(mauvais)
    with pytest.raises(StatsAggregateError):
        prepare_stats_counts_params(mauvais)


@pytest.mark.parametrize(
    ("name", "category", "since"),
    [
        (None, None, None),
        ("page_view", None, None),
        (None, "navigation", None),
        ("page_view", "navigation", "2026-01-01T00:00:00Z"),
        (None, None, "2026-01-01T00:00:00Z"),
    ],
)
def test_coherence_sql_params(name, category, since) -> None:
    sql = get_stats_counts_sql("name", name=name, category=category, since=since)
    params = prepare_stats_counts_params("name", name=name, category=category, since=since)
    assert sql.count("?") == len(params)


def test_filtre_since_ajoute_borne_temporelle() -> None:
    sql = get_stats_counts_sql("name", since="2026-01-01T00:00:00Z")
    assert "created_at >= ?" in sql


def test_category_vide_rejetee() -> None:
    with pytest.raises(StatsAggregateError):
        prepare_stats_counts_params("name", category="   ")


def test_normalisation_total_en_entier() -> None:
    row = normalize_stats_count_row({"bucket": "navigation", "total": "12"})
    assert row == {"bucket": "navigation", "total": 12}


def test_ligne_incomplete_rejetee() -> None:
    with pytest.raises(StatsAggregateError):
        normalize_stats_count_row({"bucket": "x"})


def test_count_stats_events_via_executeur_injecte() -> None:
    captured: dict[str, object] = {}

    def fake_fetch_all(sql: str, params: tuple) -> list[dict[str, object]]:
        captured["sql"] = sql
        captured["params"] = params
        return [
            {"bucket": "navigation", "total": 7},
            {"bucket": "compte", "total": 3},
        ]

    resultat = count_stats_events(fake_fetch_all, "category", since="2026-01-01T00:00:00Z")

    assert resultat == [
        {"bucket": "navigation", "total": 7},
        {"bucket": "compte", "total": 3},
    ]
    assert "GROUP BY category" in captured["sql"]  # type: ignore[operator]
    assert captured["params"] == ("2026-01-01T00:00:00Z",)
