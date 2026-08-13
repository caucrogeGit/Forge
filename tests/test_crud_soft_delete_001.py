"""Garde-fou CRUD-SOFT-DELETE-001 (ADR-083).

Une entité avec `options.soft_delete: true` obtient une **suppression logique**
réelle, pas seulement une colonne `deleted_at` :

- `deleted_at` est marqué `managed = "soft_delete"` par le normaliseur ;
- absent des vues (formulaire, liste, détail) et de l'INSERT/UPDATE ;
- la suppression est un `UPDATE ... SET deleted_at = now()` (au lieu d'un
  `DELETE`), simple et groupée ;
- toute lecture (liste, count, pagination, par id, par slug) filtre
  `deleted_at IS NULL` ;
- DDL : `deleted_at DATETIME NULL`, sans défaut.

Sans `soft_delete`, la suppression reste physique (non-régression).
"""
from __future__ import annotations

import pytest

from forge_mvc_entities.canonical_model_normalizer import (
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.crud.form_builder import build_form
from forge_mvc_entities.crud.model_builder import build_model
from forge_mvc_entities.crud.views_builder import build_show_view, build_table_partial
from forge_mvc_entities.make_entity import build_entity_sql
from forge_mvc_entities.validation import validate_entity_definition


def _definition(soft_delete: bool) -> dict:
    return validate_entity_definition(
        normalize_canonical_entity_for_model_build(
            {
                "schema_version": "1.0",
                "name": "Article",
                "table": "article",
                "fields": [{"name": "titre", "type": "string", "required": True}],
                "options": {"soft_delete": soft_delete},
            }
        )
    )


@pytest.fixture()
def definition() -> dict:
    return _definition(True)


# ── Marquage ─────────────────────────────────────────────────────────────────

def test_normalizer_marks_deleted_at_soft_delete(definition):
    field = next(f for f in definition["fields"] if f["name"] == "deleted_at")
    assert field["managed"] == "soft_delete"
    assert field["nullable"] is True


# ── Suppression logique dans le modèle ───────────────────────────────────────

def test_delete_is_soft_update(definition):
    model = build_model(definition)
    delete_const = next(l for l in model.splitlines() if l.startswith("DELETE"))
    assert "UPDATE article SET DeletedAt = ?" in delete_const
    assert "DELETE FROM" not in delete_const
    body = next(l for l in model.splitlines() if "execute(DELETE" in l)
    assert "utc_now()" in body


def test_bulk_delete_is_soft_update(definition):
    model = build_model(definition)
    bulk = next(l for l in model.splitlines() if "DeletedAt = ? WHERE Id IN" in l)
    assert "UPDATE article SET DeletedAt = ?" in bulk
    assert "utc_now()" in bulk


# ── Lectures filtrées ────────────────────────────────────────────────────────

def test_reads_filter_deleted_at_is_null(definition):
    model = build_model(definition)
    select_all = next(l for l in model.splitlines() if l.startswith("SELECT_ALL"))
    select_by_id = next(l for l in model.splitlines() if l.startswith("SELECT_BY_ID"))
    assert "WHERE DeletedAt IS NULL" in select_all
    assert "AND DeletedAt IS NULL" in select_by_id
    # count et pagination partent d'une clause de base deleted_at IS NULL
    assert model.count('clauses: list[str] = ["DeletedAt IS NULL"]') == 2


# ── Exclusion de l'écriture applicative et des vues ──────────────────────────

def test_deleted_at_absent_from_insert_update(definition):
    model = build_model(definition)
    insert = next(l for l in model.splitlines() if l.startswith("INSERT"))
    update = next(l for l in model.splitlines() if l.startswith("UPDATE"))
    assert "DeletedAt" not in insert
    assert "DeletedAt" not in update


def test_deleted_at_absent_from_views(definition):
    form_code, _ = build_form(definition)
    assert "deleted_at" not in form_code
    assert "DeletedAt" not in build_table_partial(definition)
    assert "DeletedAt" not in build_show_view(definition)


# ── DDL ──────────────────────────────────────────────────────────────────────

def test_ddl_deleted_at_nullable_sans_defaut(definition):
    sql = build_entity_sql(definition)
    line = next(l for l in sql.splitlines() if "DeletedAt" in l)
    assert "NULL" in line and "NOT NULL" not in line
    assert "DEFAULT" not in line


# ── Non-régression : sans soft_delete, suppression physique ─────────────────

def test_sans_soft_delete_suppression_physique():
    model = build_model(_definition(False))
    delete_const = next(l for l in model.splitlines() if l.startswith("DELETE"))
    assert "DELETE FROM article" in delete_const
    assert "SET DeletedAt" not in model
    select_all = next(l for l in model.splitlines() if l.startswith("SELECT_ALL"))
    assert "IS NULL" not in select_all
