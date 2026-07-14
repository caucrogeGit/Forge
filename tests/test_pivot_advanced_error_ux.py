"""Tests — PIVOT-ADVANCED-007 : UX erreurs pivot advanced.

Couvre PivotFormError, l'enrichissement de PivotConstraintError (code/field),
le helper pivot_error_to_form_error, et la présence des points d'ancrage UX
dans le contrôleur et le template générés par make:pivot-crud.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

pytest.importorskip("forge_mvc_entities")
from forge_mvc_entities import (
    PivotAdvancedService,
    PivotConstraintError,
    PivotFieldConstraint,
    PivotFormError,
    pivot_error_to_form_error,
)
from forge_mvc_entities.make_pivot_crud import make_pivot_crud


# ── Fixture SQLite in-memory ──────────────────────────────────────────────────

@pytest.fixture()
def db():
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
        "fetch_one": fetch_one, "fetch_all": fetch_all,
        "execute": execute, "insert_fn": insert_fn,
    }
    conn.close()


def _svc(db, *, pivot_fields=None, pivot_constraints=None, unique_pair=False):
    return PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_fields=pivot_fields,
        pivot_constraints=pivot_constraints,
        unique_pair=unique_pair,
        fetch_one=db["fetch_one"],
        fetch_all=db["fetch_all"],
        execute=db["execute"],
        insert_fn=db["insert_fn"],
    )


# ── Fixture make:pivot-crud ───────────────────────────────────────────────────

_RELATIONS_JSON = {
    "schema_version": "1.0",
    "relations": [{
        "type": "many_to_many",
        "from": "Article",
        "to": "Tag",
        "name": "tags",
        "pivot": {
            "table": "article_tag",
            "from_key": "article_id",
            "to_key": "tag_id",
            "id": True,
            "unique_pair": True,
            "fields": [
                {"name": "position", "type": "integer", "nullable": True},
                {"name": "note", "type": "string", "max_length": 120, "nullable": True},
            ],
        },
    }],
}


@pytest.fixture()
def generated(tmp_path):
    rel_path = tmp_path / "mvc" / "entities" / "relations.json"
    rel_path.parent.mkdir(parents=True, exist_ok=True)
    rel_path.write_text(json.dumps(_RELATIONS_JSON), encoding="utf-8")
    make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    ctrl = tmp_path / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    form = tmp_path / "mvc" / "views" / "pivot" / "article_tags" / "form.html"
    return {"ctrl": ctrl.read_text(encoding="utf-8"), "form": form.read_text(encoding="utf-8")}


# ── PivotFormError ────────────────────────────────────────────────────────────

def test_pivot_form_error_importable():
    from forge_mvc_entities import PivotFormError
    assert PivotFormError is not None


def test_pivot_form_error_attributs():
    err = PivotFormError(code="required_field_missing", message="Position requis.", field="position")
    assert err.code == "required_field_missing"
    assert err.message == "Position requis."
    assert err.field == "position"


def test_pivot_form_error_field_optionnel():
    err = PivotFormError(code="duplicate_pair", message="Doublon.")
    assert err.field is None


# ── PivotConstraintError enrichi ──────────────────────────────────────────────

def test_pivot_constraint_error_est_value_error():
    exc = PivotConstraintError("test")
    assert isinstance(exc, ValueError)


def test_pivot_constraint_error_porte_code_et_field():
    exc = PivotConstraintError("requis", code="required_field_missing", field="position")
    assert exc.code == "required_field_missing"
    assert exc.field == "position"
    assert str(exc) == "requis"


def test_pivot_constraint_error_code_defaut():
    exc = PivotConstraintError("erreur générique")
    assert exc.code == "invalid_pivot_data"
    assert exc.field is None


# ── Codes émis par le service ─────────────────────────────────────────────────

def test_required_field_missing_produit_bon_code(db):
    svc = _svc(db, pivot_constraints=[PivotFieldConstraint("position", required=True)])
    with pytest.raises(PivotConstraintError) as exc_info:
        svc.attach(1, 10, {})
    assert exc_info.value.code == "required_field_missing"
    assert exc_info.value.field == "position"


def test_nullable_field_rejected_produit_bon_code(db):
    svc = _svc(db, pivot_constraints=[PivotFieldConstraint("position", nullable=False)])
    with pytest.raises(PivotConstraintError) as exc_info:
        svc.attach(1, 10, {"position": None})
    assert exc_info.value.code == "nullable_field_rejected"
    assert exc_info.value.field == "position"


def test_duplicate_pair_produit_bon_code(db):
    svc = _svc(db, pivot_fields=["position"], unique_pair=True)
    svc.attach(1, 10, {"position": 1})
    with pytest.raises(PivotConstraintError) as exc_info:
        svc.attach(1, 10, {"position": 2})
    assert exc_info.value.code == "duplicate_pair"
    assert exc_info.value.field is None


def test_missing_id_field_produit_bon_code(db):
    svc = _svc(db, pivot_fields=["position"])
    with pytest.raises(PivotConstraintError) as exc_info:
        svc.get_by_id(1)
    assert exc_info.value.code == "missing_id_field"


def test_unknown_pivot_field_produit_value_error(db):
    svc = _svc(db, pivot_fields=["position"])
    with pytest.raises(ValueError):
        svc.attach(1, 10, {"champ_inconnu": "x"})


# ── pivot_error_to_form_error ─────────────────────────────────────────────────

def test_helper_convertit_pivot_constraint_error():
    exc = PivotConstraintError("Position requise.", code="required_field_missing", field="position")
    form_err = pivot_error_to_form_error(exc)
    assert isinstance(form_err, PivotFormError)
    assert form_err.code == "required_field_missing"
    assert form_err.field == "position"
    assert form_err.message == "Position requise."


def test_helper_convertit_value_error_en_unknown_pivot_field():
    exc = ValueError("Champs pivot inconnus : ['x'].")
    form_err = pivot_error_to_form_error(exc)
    assert form_err.code == "unknown_pivot_field"
    assert form_err.message == "Champs pivot inconnus : ['x']."


def test_helper_convertit_exception_inconnue_sans_detail_sql():
    exc = Exception("syntax error near SELECT something internal")
    form_err = pivot_error_to_form_error(exc)
    assert form_err.code == "invalid_pivot_data"
    assert "SELECT" not in form_err.message
    assert "syntax error" not in form_err.message


def test_helper_retourne_message_humain():
    exc = PivotConstraintError("Doublon.", code="duplicate_pair")
    form_err = pivot_error_to_form_error(exc)
    assert len(form_err.message) > 0
    assert isinstance(form_err.message, str)


def test_helper_required_code_via_service(db):
    svc = _svc(db, pivot_constraints=[PivotFieldConstraint("position", required=True)])
    try:
        svc.attach(1, 10, {})
    except Exception as exc:
        form_err = pivot_error_to_form_error(exc)
        assert form_err.code == "required_field_missing"
        assert form_err.field == "position"


def test_helper_nullable_code_via_service(db):
    svc = _svc(db, pivot_constraints=[PivotFieldConstraint("position", nullable=False)])
    try:
        svc.attach(1, 10, {"position": None})
    except Exception as exc:
        form_err = pivot_error_to_form_error(exc)
        assert form_err.code == "nullable_field_rejected"


def test_helper_duplicate_code_via_service(db):
    svc = _svc(db, pivot_fields=["position"], unique_pair=True)
    svc.attach(1, 10, {"position": 1})
    try:
        svc.attach(1, 10, {"position": 2})
    except Exception as exc:
        form_err = pivot_error_to_form_error(exc)
        assert form_err.code == "duplicate_pair"


# ── Contrôleur généré ─────────────────────────────────────────────────────────

def test_controleur_genere_importe_pivot_constraint_error(generated):
    assert "PivotConstraintError" in generated["ctrl"]


def test_controleur_genere_importe_pivot_error_to_form_error(generated):
    assert "pivot_error_to_form_error" in generated["ctrl"]


def test_controleur_genere_importe_depuis_core_pivot_advanced(generated):
    assert "from forge_mvc_entities import" in generated["ctrl"]
    assert "PivotConstraintError" in generated["ctrl"]
    assert "pivot_error_to_form_error" in generated["ctrl"]


def test_controleur_genere_contient_try_except(generated):
    assert "try:" in generated["ctrl"]
    assert "except Exception as exc:" in generated["ctrl"]


def test_controleur_genere_passe_error_au_template(generated):
    assert '"error": error' in generated["ctrl"]
    assert '"error": None' in generated["ctrl"]


# ── Template form.html généré ─────────────────────────────────────────────────

def test_template_form_affiche_error_message(generated):
    assert "error.message" in generated["form"]


def test_template_form_bloc_if_error(generated):
    assert "{% if error %}" in generated["form"]


def test_template_form_mentionne_champs_pivot(generated):
    assert "position" in generated["form"]
    assert "note" in generated["form"]


# ── Neutralité make:crud ──────────────────────────────────────────────────────

def test_make_crud_ne_reference_pas_pivot_ux():
    from forge_mvc_entities import make_crud as mc_mod
    import inspect
    src = inspect.getsource(mc_mod)
    assert "PivotConstraintError" not in src
    assert "PivotFormError" not in src
    assert "pivot_error_to_form_error" not in src
    assert "make:pivot-crud" not in src
