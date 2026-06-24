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
    build_get_sql,
    build_insert_sql,
    build_list_sql,
    build_update_sql,
    count_rows,
    detail_columns,
    get_row,
    insert_row,
    list_rows,
    update_row,
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


def test_detail_columns_unique_pk_puis_list_puis_form():
    # pk "id" + list (title, published_at) + form (title, body) dédupliqués.
    assert detail_columns(_resource()) == ("id", "title", "published_at", "body")


def test_build_get_sql():
    sql = build_get_sql(_resource())
    assert sql == (
        "SELECT id, title, published_at, body FROM articles "
        "WHERE id = ? LIMIT 1"
    )


def test_get_row_passe_la_cle_en_parametre():
    captured: dict[str, Any] = {}

    def fake_fetch_one(sql: str, params: Any) -> dict[str, Any] | None:
        captured["params"] = params
        return {"id": 5, "title": "Bonjour"}

    row = get_row(_resource(), fake_fetch_one, pk_value="5")
    assert row == {"id": 5, "title": "Bonjour"}
    assert captured["params"] == ("5",)


def test_get_row_none_si_absent():
    def fake_fetch_one(sql: str, params: Any) -> dict[str, Any] | None:
        return None

    assert get_row(_resource(), fake_fetch_one, pk_value="999") is None


def test_build_insert_sql():
    # form_fields = (title, body)
    assert build_insert_sql(_resource()) == "INSERT INTO articles (title, body) VALUES (?, ?)"


def test_insert_row_passe_les_valeurs_et_retourne_lastrowid():
    captured: dict[str, Any] = {}

    def fake_insert(sql: str, params: Any) -> int:
        captured["sql"] = sql
        captured["params"] = params
        return 42

    new_id = insert_row(_resource(), fake_insert, values=("Bonjour", None))
    assert new_id == 42
    assert captured["params"] == ("Bonjour", None)
    assert captured["sql"].startswith("INSERT INTO articles")


def test_build_update_sql():
    sql = build_update_sql(_resource())
    assert sql == "UPDATE articles SET title = ?, body = ? WHERE id = ? LIMIT 1"


def test_update_row_valeurs_puis_cle():
    captured: dict[str, Any] = {}

    def fake_execute(sql: str, params: Any) -> int:
        captured["params"] = params
        return 1

    affected = update_row(_resource(), fake_execute, values=("Bonjour", None), pk_value="5")
    assert affected == 1
    # valeurs des champs d'abord, clé primaire en dernier
    assert captured["params"] == ("Bonjour", None, "5")
