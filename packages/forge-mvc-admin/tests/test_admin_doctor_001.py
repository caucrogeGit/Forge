"""Tests de `forge admin:doctor` (ADMIN-DOCTOR-001).

Cœur testé : la réconciliation pure (ressource ↔ contrat). Un test d'intégration
exerce le chemin complet (import du module projet + lecture des contrats) sur un
projet temporaire.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin import AdminResource, registry
from forge_mvc_admin.cli.doctor import (
    _EntityContract,
    has_failures,
    reconcile,
    run_all,
)


def _resource(**overrides: object) -> AdminResource:
    base: dict[str, object] = dict(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("title", "published_at"),
        form_fields=("title", "body"),
        table="articles",
    )
    base.update(overrides)
    return AdminResource(**base)  # type: ignore[arg-type]


def _contract(**overrides: object) -> dict[str, _EntityContract]:
    contract = _EntityContract(
        table="articles",
        columns=frozenset({"id", "title", "published_at", "body"}),
        pk="id",
    )
    data = {"Article": contract}
    data.update(overrides)  # type: ignore[arg-type]
    return data


# ── Réconciliation pure ──────────────────────────────────────────────────────


def test_reconcile_conforme():
    results = reconcile(_resource(), _contract())
    assert len(results) == 1
    assert results[0].status == "ok"


def test_reconcile_entite_introuvable():
    results = reconcile(_resource(), {})
    assert [r.status for r in results] == ["warn"]
    assert "introuvable" in results[0].detail


def test_reconcile_table_divergente():
    contracts = _contract(Article=_EntityContract("autre_table", frozenset({"id", "title", "published_at", "body"}), "id"))
    results = reconcile(_resource(), contracts)
    assert any(r.status == "warn" and "table" in r.detail for r in results)


def test_reconcile_colonne_absente():
    contracts = _contract(Article=_EntityContract("articles", frozenset({"id", "title"}), "id"))
    results = reconcile(_resource(), contracts)
    # published_at et body manquent au contrat
    details = " ".join(r.detail for r in results)
    assert "published_at" in details and "body" in details
    assert all(r.status == "warn" for r in results)


def test_reconcile_pk_absente():
    contracts = _contract(Article=_EntityContract("articles", frozenset({"title", "published_at", "body"}), None))
    results = reconcile(_resource(), contracts)
    assert any(r.status == "warn" and "primaire" in r.detail for r in results)


# ── Chemin complet (projet temporaire) ───────────────────────────────────────


def _write_project(tmp_path: Path, *, resources_py: str, entity: dict[str, object] | None) -> Path:
    admin_dir = tmp_path / "mvc" / "admin"
    admin_dir.mkdir(parents=True)
    (admin_dir / "__init__.py").write_text("", encoding="utf-8")
    (admin_dir / "resources.py").write_text(resources_py, encoding="utf-8")
    if entity is not None:
        ent_dir = tmp_path / "mvc" / "entities" / "article"
        ent_dir.mkdir(parents=True)
        (ent_dir / "article.json").write_text(json.dumps(entity), encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    registry.clear()


def test_run_all_skip_si_resources_absent(tmp_path: Path):
    (tmp_path / "mvc").mkdir()
    results = run_all(tmp_path)
    assert any(r.status == "skip" for r in results)
    assert not has_failures(results)


def test_run_all_projet_conforme(tmp_path: Path):
    resources_py = (
        "from forge_mvc_admin import AdminResource, registry\n"
        "registry.register(AdminResource(\n"
        "    entity='Article', slug='articles', label='Article',\n"
        "    plural_label='Articles', list_fields=('title',),\n"
        "    form_fields=('title',), table='articles'))\n"
    )
    entity = {
        "schema_version": "1.0",
        "name": "Article",
        "table": "articles",
        "fields": [
            {"name": "id", "primary_key": True},
            {"name": "title", "type": "string"},
        ],
    }
    root = _write_project(tmp_path, resources_py=resources_py, entity=entity)
    results = run_all(root)
    assert not has_failures(results)
    assert any(r.status == "ok" and "conforme" in r.detail for r in results)


def test_run_all_declaration_cassee_est_fail(tmp_path: Path):
    # slug invalide (majuscule) -> AdminResourceError à l'import
    resources_py = (
        "from forge_mvc_admin import AdminResource, registry\n"
        "registry.register(AdminResource(\n"
        "    entity='Article', slug='Articles', label='Article',\n"
        "    plural_label='Articles', list_fields=('title',),\n"
        "    form_fields=('title',), table='articles'))\n"
    )
    root = _write_project(tmp_path, resources_py=resources_py, entity=None)
    results = run_all(root)
    assert has_failures(results)
