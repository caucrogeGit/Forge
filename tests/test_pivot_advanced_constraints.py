"""Tests — PIVOT-ADVANCED-006 : contraintes pivot advanced.

Couvre PivotFieldConstraint, PivotConstraintError, required, nullable,
unique_pair et les méthodes *_by_id avec id_field.
"""
from __future__ import annotations

import sqlite3

import pytest

pytest.importorskip("forge_mvc_pivot")
from forge_mvc_pivot import (
    PivotAdvancedService,
    PivotConstraintError,
    PivotFieldConstraint,
    PivotRow,
)


# ── Fixture SQLite in-memory ──────────────────────────────────────────────────

@pytest.fixture()
def db():
    """Callables SQLite in-memory avec table article_tag."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE article_tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            position INTEGER,
            note TEXT,
            UNIQUE(article_id, tag_id)
        )
    """)
    conn.commit()

    def fetch_one(sql, params):
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetch_all(sql, params):
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def execute(sql, params):
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount

    def insert_fn(sql, params):
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid

    yield {
        "fetch_one": fetch_one,
        "fetch_all": fetch_all,
        "execute": execute,
        "insert_fn": insert_fn,
    }
    conn.close()


def _svc(db, *, pivot_fields=None, pivot_constraints=None, unique_pair=False, id_field=None):
    return PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_fields=pivot_fields,
        pivot_constraints=pivot_constraints,
        unique_pair=unique_pair,
        id_field=id_field,
        fetch_one=db["fetch_one"],
        fetch_all=db["fetch_all"],
        execute=db["execute"],
        insert_fn=db["insert_fn"],
    )


# ── PivotFieldConstraint ──────────────────────────────────────────────────────

def test_pivot_field_constraint_defaults():
    c = PivotFieldConstraint("position")
    assert c.name == "position"
    assert c.required is False
    assert c.nullable is True


def test_pivot_field_constraint_tous_attributs():
    c = PivotFieldConstraint("position", required=True, nullable=False)
    assert c.required is True
    assert c.nullable is False


# ── PivotConstraintError ──────────────────────────────────────────────────────

def test_pivot_constraint_error_est_subclass_value_error():
    err = PivotConstraintError("test")
    assert isinstance(err, ValueError)


def test_pivot_constraint_error_message():
    err = PivotConstraintError("champ requis absent")
    assert "requis absent" in str(err)


# ── Backward compatibility pivot_fields ──────────────────────────────────────

def test_backward_compat_pivot_fields_accepte(db):
    svc = _svc(db, pivot_fields=["position", "note"])
    rid = svc.attach(1, 10, {"position": 1, "note": "ok"})
    assert rid > 0


def test_backward_compat_none_autorise_sans_constraint(db):
    """pivot_fields sans contraintes : None est accepté (pas de vérification)."""
    svc = _svc(db, pivot_fields=["position", "note"])
    svc.attach(1, 10, {"position": None, "note": "ok"})
    row = svc.get(1, 10)
    assert row is not None


# ── Contrainte required ───────────────────────────────────────────────────────

def test_attach_leve_si_required_absent(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", required=True),
        PivotFieldConstraint("note"),
    ])
    with pytest.raises(PivotConstraintError, match="requis absent"):
        svc.attach(1, 10, {"note": "ok"})


def test_attach_accepte_si_required_present(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", required=True),
        PivotFieldConstraint("note"),
    ])
    rid = svc.attach(1, 10, {"position": 1, "note": "ok"})
    assert rid > 0


def test_attach_required_nullable_true_accepte_none(db):
    """required=True, nullable=True : champ présent avec None — accepté."""
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("note", required=True, nullable=True),
    ])
    rid = svc.attach(1, 10, {"note": None})
    assert rid > 0


def test_update_ne_verifie_pas_required(db):
    """required n'est pas vérifié lors d'un update (mise à jour partielle autorisée)."""
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", required=True),
        PivotFieldConstraint("note"),
    ])
    svc.attach(1, 10, {"position": 1, "note": "initial"})
    svc.update(1, 10, {"note": "mis à jour"})
    row = svc.get(1, 10)
    assert row.pivot_data.get("note") == "mis à jour"


# ── Contrainte nullable ───────────────────────────────────────────────────────

def test_attach_leve_si_nullable_false_et_none(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", nullable=False),
        PivotFieldConstraint("note"),
    ])
    with pytest.raises(PivotConstraintError, match="non nullable"):
        svc.attach(1, 10, {"position": None, "note": "ok"})


def test_attach_accepte_si_nullable_false_avec_valeur(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", nullable=False),
        PivotFieldConstraint("note"),
    ])
    rid = svc.attach(1, 10, {"position": 1, "note": "ok"})
    assert rid > 0


def test_attach_nullable_false_absent_du_pivot_data_autorise(db):
    """nullable=False sans required=True : champ absent de pivot_data n'est pas vérifié."""
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", nullable=False),
        PivotFieldConstraint("note"),
    ])
    rid = svc.attach(1, 10, {"note": "ok"})
    assert rid > 0


def test_update_leve_si_nullable_false_et_none(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", nullable=False),
        PivotFieldConstraint("note"),
    ])
    svc.attach(1, 10, {"position": 1})
    with pytest.raises(PivotConstraintError, match="non nullable"):
        svc.update(1, 10, {"position": None})


def test_update_accepte_nullable_true_avec_none(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position"),
        PivotFieldConstraint("note", nullable=True),
    ])
    svc.attach(1, 10, {"position": 1, "note": "avant"})
    svc.update(1, 10, {"note": None})
    row = svc.get(1, 10)
    assert row is not None


# ── required + nullable=False combinés ───────────────────────────────────────

def test_attach_required_et_nullable_false_avec_none_leve_erreur(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", required=True, nullable=False),
    ])
    with pytest.raises(PivotConstraintError):
        svc.attach(1, 10, {"position": None})


def test_attach_required_et_nullable_false_avec_valeur_accepte(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", required=True, nullable=False),
    ])
    rid = svc.attach(1, 10, {"position": 42})
    assert rid > 0


# ── Contrainte unique_pair ────────────────────────────────────────────────────

def test_unique_pair_bloque_doublon(db):
    svc = _svc(db, pivot_fields=["position", "note"], unique_pair=True)
    svc.attach(1, 10, {"position": 1})
    with pytest.raises(PivotConstraintError, match="déjà existante"):
        svc.attach(1, 10, {"position": 2})


def test_unique_pair_accepte_paires_differentes(db):
    svc = _svc(db, pivot_fields=["position"], unique_pair=True)
    svc.attach(1, 10, {"position": 1})
    svc.attach(1, 20, {"position": 2})
    rows = svc.list_for_source(1)
    assert len(rows) == 2


def test_unique_pair_accepte_meme_target_source_differente(db):
    svc = _svc(db, pivot_fields=["position"], unique_pair=True)
    svc.attach(1, 10, {"position": 1})
    svc.attach(2, 10, {"position": 1})
    assert svc.get(1, 10) is not None
    assert svc.get(2, 10) is not None


def test_sans_unique_pair_pas_de_verification_applicative(db):
    """Sans unique_pair=True, le service ne vérifie pas — c'est la DB qui lève."""
    svc = _svc(db, pivot_fields=["position"], unique_pair=False)
    svc.attach(1, 10, {"position": 1})
    with pytest.raises(Exception):
        svc.attach(1, 10, {"position": 2})


# ── id_field et méthodes *_by_id ──────────────────────────────────────────────

def test_get_by_id_retourne_la_ligne(db):
    svc = _svc(db, pivot_fields=["position", "note"], id_field="id")
    svc.attach(1, 10, {"position": 1, "note": "test"})
    row = svc.get(1, 10)
    pivot_id = row.pivot_data.get("id")
    assert pivot_id is not None

    found = svc.get_by_id(pivot_id)
    assert found is not None
    assert isinstance(found, PivotRow)
    assert found.pivot_data.get("note") == "test"


def test_get_by_id_retourne_none_si_absent(db):
    svc = _svc(db, pivot_fields=["position"], id_field="id")
    assert svc.get_by_id(9999) is None


def test_update_by_id_modifie_la_ligne(db):
    svc = _svc(db, pivot_fields=["position", "note"], id_field="id")
    svc.attach(1, 10, {"position": 1, "note": "avant"})
    row = svc.get(1, 10)
    pivot_id = row.pivot_data.get("id")

    svc.update_by_id(pivot_id, {"note": "après"})
    updated = svc.get_by_id(pivot_id)
    assert updated.pivot_data.get("note") == "après"


def test_delete_by_id_supprime_la_ligne(db):
    svc = _svc(db, pivot_fields=["position"], id_field="id")
    svc.attach(1, 10, {"position": 1})
    row = svc.get(1, 10)
    pivot_id = row.pivot_data.get("id")

    svc.delete_by_id(pivot_id)
    assert svc.get_by_id(pivot_id) is None
    assert svc.get(1, 10) is None


def test_update_by_id_retourne_rowcount(db):
    svc = _svc(db, pivot_fields=["position", "note"], id_field="id")
    svc.attach(1, 10, {"position": 1})
    row = svc.get(1, 10)
    pivot_id = row.pivot_data.get("id")
    count = svc.update_by_id(pivot_id, {"note": "x"})
    assert count == 1


def test_delete_by_id_retourne_rowcount(db):
    svc = _svc(db, pivot_fields=["position"], id_field="id")
    svc.attach(1, 10, {"position": 1})
    row = svc.get(1, 10)
    pivot_id = row.pivot_data.get("id")
    count = svc.delete_by_id(pivot_id)
    assert count == 1


def test_update_by_id_vide_retourne_zero(db):
    svc = _svc(db, pivot_fields=["position"], id_field="id")
    svc.attach(1, 10, {"position": 1})
    row = svc.get(1, 10)
    pivot_id = row.pivot_data.get("id")
    count = svc.update_by_id(pivot_id, {})
    assert count == 0


# ── Erreurs quand id_field absent ────────────────────────────────────────────

def test_get_by_id_sans_id_field_leve_value_error(db):
    svc = _svc(db, pivot_fields=["position"])
    with pytest.raises(ValueError, match="id_field"):
        svc.get_by_id(1)


def test_update_by_id_sans_id_field_leve_value_error(db):
    svc = _svc(db, pivot_fields=["position"])
    with pytest.raises(ValueError, match="id_field"):
        svc.update_by_id(1, {"position": 2})


def test_delete_by_id_sans_id_field_leve_value_error(db):
    svc = _svc(db, pivot_fields=["position"])
    with pytest.raises(ValueError, match="id_field"):
        svc.delete_by_id(1)


# ── update_by_id applique contrainte nullable ─────────────────────────────────

def test_update_by_id_leve_constraint_error_si_nullable_false_et_none(db):
    svc = _svc(db, pivot_constraints=[
        PivotFieldConstraint("position", nullable=False),
    ], id_field="id")
    svc.attach(1, 10, {"position": 1})
    row = svc.get(1, 10)
    pivot_id = row.pivot_data.get("id")
    with pytest.raises(PivotConstraintError, match="non nullable"):
        svc.update_by_id(pivot_id, {"position": None})


# ── Exports publics ───────────────────────────────────────────────────────────

def test_exports_publics_006():
    from forge_mvc_pivot import (
        PivotAdvancedService,
        PivotConstraintError,
        PivotFieldConstraint,
        PivotRow,
    )
    assert PivotAdvancedService
    assert PivotConstraintError
    assert PivotFieldConstraint
    assert PivotRow


# ── Neutralité make:crud ──────────────────────────────────────────────────────

def test_pivot_advanced_ne_depend_pas_de_make_crud():
    import inspect
    import forge_mvc_pivot as pivot_advanced
    src = inspect.getsource(pivot_advanced)
    assert "make_crud" not in src
    assert "from forge_cli" not in src
