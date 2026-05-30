"""
Tests documentaires MODULE-LIFECYCLE-DOC-001 — Cycle de vie des modules.

Valide que docs/reference/reference.md documente correctement :
- les capacités actuelles du système de modules ;
- ce qui n'est pas encore supporté ;
- les risques connus ;
- les bonnes pratiques ;
- les tickets futurs MODULE-REMOVE-001 et MODULE-UPDATE-001.
"""
import pathlib

import pytest
pytestmark = pytest.mark.meta

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
REF = (ROOT / "docs" / "reference" / "modules.md").read_text(encoding="utf-8")


# ── Section cycle de vie présente ───────────────────────────────────────────────

def test_reference_contient_section_cycle_de_vie():
    assert "Cycle de vie" in REF


def test_reference_contient_ce_qui_est_supporte():
    assert "Ce qui est supporté" in REF


def test_reference_contient_ce_qui_nest_pas_supporte():
    assert "Ce qui n'est pas encore supporté" in REF or "n'est pas encore supporté" in REF


def test_reference_contient_risques_connus():
    assert "Risques connus" in REF


def test_reference_contient_bonnes_pratiques():
    assert "Bonnes pratiques" in REF


def test_reference_contient_tickets_futurs():
    assert "Tickets futurs" in REF


# ── Commandes supportées documentées ───────────────────────────────────────────

def test_reference_mentionne_module_list():
    assert "module:list" in REF


def test_reference_mentionne_module_install():
    assert "module:install" in REF


def test_reference_mentionne_module_files():
    assert "module:files" in REF


def test_reference_mentionne_module_routes():
    assert "module:routes" in REF


# ── Limites non supportées documentées ─────────────────────────────────────────

def test_reference_mentionne_module_remove_non_dispo():
    assert "module:remove" in REF


def test_reference_mentionne_module_update_non_dispo():
    assert "module:update" in REF


def test_reference_mentionne_rollback():
    assert "rollback" in REF.lower() or "Rollback" in REF


def test_reference_mentionne_absence_registre_distant():
    assert "registre distant" in REF or "distant" in REF


# ── Tickets futurs documentés ───────────────────────────────────────────────────

def test_reference_mentionne_module_remove_001():
    assert "MODULE-REMOVE-001" in REF


def test_reference_mentionne_module_update_001():
    assert "MODULE-UPDATE-001" in REF


# ── Roadmap ─────────────────────────────────────────────────────────────────────

def test_roadmap_mentionne_module_lifecycle_doc_001():
    roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "MODULE-LIFECYCLE-DOC-001" in roadmap


def test_consolidation_roadmap_mentionne_module_lifecycle_doc_001():
    roadmap = (ROOT / "docs" / "history" / "forge_post_2_0_consolidation_roadmap.md").read_text(encoding="utf-8")
    assert "MODULE-LIFECYCLE-DOC-001" in roadmap


def test_roadmap_mentionne_module_remove_001_comme_suivant():
    roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "MODULE-REMOVE-001" in roadmap
