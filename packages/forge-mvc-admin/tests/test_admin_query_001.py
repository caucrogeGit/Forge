"""Tests de la couche requête de liste (ADMIN-LIST-VIEW-001).

SELECT contraint : identifiants déclarés uniquement, valeurs paramétrées.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin import AdminResource
from forge_mvc_admin.query import (
    build_count_sql,
    build_list_sql,
    count_rows,
    list_rows,
)


def _resource(order_by: str = "") -> AdminResource:
    return AdminResource(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("title", "published_at"),
        form_fields=("title", "body"),
        table="articles",
        order_by=order_by,
    )


def test_build_count_sql():
    assert build_count_sql(_resource()) == "SELECT COUNT(*) AS total FROM articles"


def test_build_list_sql_tri_par_defaut_premier_champ():
    sql = build_list_sql(_resource())
    assert sql == (
        "SELECT title, published_at FROM articles "
        "ORDER BY title ASC LIMIT ? OFFSET ?"
    )


def test_build_list_sql_order_by_explicite():
    sql = build_list_sql(_resource(order_by="published_at"))
    assert "ORDER BY published_at ASC" in sql


def test_list_rows_passe_les_valeurs_en_parametres():
    captured: dict[str, Any] = {}

    def fake_fetch_all(sql: str, params: Any) -> list[dict[str, Any]]:
        captured["sql"] = sql
        captured["params"] = params
        return [{"title": "Bonjour", "published_at": "2026-06-24"}]

    rows = list_rows(_resource(), fake_fetch_all, limit=20, offset=40)
    assert rows == [{"title": "Bonjour", "published_at": "2026-06-24"}]
    assert captured["params"] == (20, 40)
    assert "LIMIT ? OFFSET ?" in captured["sql"]


def test_count_rows_lit_le_total():
    def fake_fetch_one(sql: str, params: Any) -> dict[str, Any] | None:
        return {"total": 7}

    assert count_rows(_resource(), fake_fetch_one) == 7


def test_count_rows_zero_si_aucune_ligne():
    def fake_fetch_one(sql: str, params: Any) -> dict[str, Any] | None:
        return None

    assert count_rows(_resource(), fake_fetch_one) == 0
