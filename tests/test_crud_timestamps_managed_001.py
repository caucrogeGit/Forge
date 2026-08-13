"""Garde-fou CRUD-TIMESTAMPS-MANAGED-001 (F56, ADR-081).

Une entité avec `options.timestamps: true` produit des horodatages
`created_at`/`updated_at` **gérés par le framework** :

- marqués `managed` par le normaliseur canonique ;
- absents du formulaire (classe Form et `form.html`) : l'utilisateur ne les
  saisit pas ;
- posés par le modèle généré à l'INSERT (`created_at` et `updated_at`) et à
  l'UPDATE (`updated_at` seul, `created_at` stable), via
  `utc_now()`, jamais lus depuis `data` ;
- sans `DEFAULT` SQL (Python reste la seule autorité, cohérent sessions-db) ;
- absents de toutes les vues générées (formulaire, liste, fiche détail) : ce
  sont des métadonnées système, consultables en base (ADR-081 révisé, retour
  terrain sur l'UX du CRUD généré).

Ce garde-fou matérialise l'invariant que pyright/ruff ne voient pas : le
contenu réellement généré pour une entité horodatée.
"""
from __future__ import annotations

import pytest

from forge_mvc_entities.canonical_model_normalizer import (
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.crud.form_builder import build_form
from forge_mvc_entities.crud.model_builder import build_model
from forge_mvc_entities.crud.views_builder import build_form_view, build_show_view
from forge_mvc_entities.make_entity import build_entity_sql
from forge_mvc_entities.validation import (
    EntityDefinitionError,
    validate_entity_definition,
)


_CANONICAL = {
    "schema_version": "1.0",
    "name": "Student",
    "table": "student",
    "fields": [{"name": "nom", "type": "string", "required": True}],
    "options": {"timestamps": True},
}


@pytest.fixture()
def definition() -> dict:
    return validate_entity_definition(
        normalize_canonical_entity_for_model_build(dict(_CANONICAL))
    )


def _field(definition: dict, name: str) -> dict:
    return next(f for f in definition["fields"] if f["name"] == name)


# ── Marquage à la normalisation ──────────────────────────────────────────────

def test_normalizer_marks_timestamps_managed(definition):
    assert _field(definition, "created_at")["managed"] == "timestamp_created"
    assert _field(definition, "updated_at")["managed"] == "timestamp_updated"


# ── Absents du formulaire ────────────────────────────────────────────────────

def test_form_class_excludes_timestamps(definition):
    code, _ = build_form(definition)
    assert "created_at" not in code
    assert "updated_at" not in code


def test_form_view_excludes_timestamps(definition):
    html = build_form_view(definition)
    assert "CreatedAt" not in html
    assert "UpdatedAt" not in html
    assert "created_at" not in html


def test_list_view_excludes_timestamps(definition):
    from forge_mvc_entities.crud.views_builder import build_table_partial
    html = build_table_partial(definition)
    assert "CreatedAt" not in html
    assert "UpdatedAt" not in html


def test_show_view_excludes_timestamps(definition):
    html = build_show_view(definition)
    assert "CreatedAt" not in html
    assert "UpdatedAt" not in html


# ── Posés par le modèle ──────────────────────────────────────────────────────

def test_model_inserts_both_timestamps_from_now(definition):
    model = build_model(definition)
    assert "from core.database.timestamps import utc_now" in model
    insert_line = next(l for l in model.splitlines() if l.startswith("INSERT"))
    assert "CreatedAt" in insert_line and "UpdatedAt" in insert_line
    add_body = next(l for l in model.splitlines() if "insert(INSERT" in l)
    # created_at ET updated_at valués par now(), pas par data.
    assert add_body.count("utc_now()") == 2


def test_model_update_touches_only_updated_at(definition):
    model = build_model(definition)
    update_line = next(l for l in model.splitlines() if l.startswith("UPDATE"))
    assert "UpdatedAt = ?" in update_line
    assert "CreatedAt" not in update_line  # création stable à l'édition
    update_body = next(l for l in model.splitlines() if "execute(UPDATE" in l)
    assert update_body.count("utc_now()") == 1


def test_model_does_not_read_timestamps_from_data(definition):
    model = build_model(definition)
    assert 'data["created_at"]' not in model
    assert 'data["updated_at"]' not in model


# ── DDL sans DEFAULT (Python seule autorité, cohérent sessions-db) ───────────

def test_ddl_timestamps_have_no_default(definition):
    sql = build_entity_sql(definition)
    for line in sql.splitlines():
        if "CreatedAt" in line or "UpdatedAt" in line:
            assert "NOT NULL" in line
            assert "DEFAULT" not in line
            assert "CURRENT_TIMESTAMP" not in line


# ── Le marqueur managed est un contrat interne validé ───────────────────────

def test_unknown_managed_value_is_rejected():
    bad = {
        "name": "Student",
        "table": "student",
        "fields": [
            {"name": "nom", "sql_type": "VARCHAR(255)"},
            {"name": "x", "sql_type": "DATETIME", "managed": "bogus"},
        ],
    }
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(bad)
