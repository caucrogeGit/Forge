"""Tests pour APP-STABILITY-CONTRACT-001 — Contrat de stabilité Forge 2.x."""

from __future__ import annotations

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "release" / "stability-contract.md"
ROADMAP = ROOT / "docs" / "roadmap" / "forge-roadmap.md"
MKDOCS = ROOT / "mkdocs.yml"
REFERENCE = ROOT / "docs" / "reference.md"


# ── Existence ─────────────────────────────────────────────────────────────────

def test_stability_contract_exists():
    assert CONTRACT.exists()


# ── Sections obligatoires ─────────────────────────────────────────────────────

def test_section_stable():
    assert "stable" in CONTRACT.read_text(encoding="utf-8").lower()


def test_section_interne():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "interne" in content.lower() or "internal" in content.lower()


def test_section_experimental():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "expérimental" in content.lower() or "experimental" in content.lower()


def test_section_fichiers_generes():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "généré" in content.lower() or "generé" in content.lower() or "fichiers générés" in content.lower()


def test_section_fichiers_utilisateur():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "préservé" in content.lower() or "utilisateur" in content.lower()


def test_section_commandes_cli():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "commandes cli" in content.lower() or "cli" in content.lower()


def test_section_compatibilite():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "compatibilité" in content.lower() or "compatibilite" in content.lower()


def test_section_limites():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "ne garantit pas" in content.lower() or "limites" in content.lower()


# ── Notions clés ──────────────────────────────────────────────────────────────

def test_mention_base_py_regenerable():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "_base.py" in content


def test_mention_forge_3x():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "Forge 3.x" in content


def test_mention_mvc():
    assert "mvc/" in CONTRACT.read_text(encoding="utf-8")


def test_mention_json_entite():
    content = CONTRACT.read_text(encoding="utf-8")
    assert ".json" in content


def test_mention_routes():
    content = CONTRACT.read_text(encoding="utf-8")
    assert "routes" in content.lower()


# ── Intégration mkdocs ────────────────────────────────────────────────────────

def test_stability_contract_dans_mkdocs():
    content = MKDOCS.read_text(encoding="utf-8")
    assert "stability-contract.md" in content


# ── Intégration roadmap ───────────────────────────────────────────────────────

def test_roadmap_mentionne_app_stability_contract():
    content = ROADMAP.read_text(encoding="utf-8")
    assert "APP-STABILITY-CONTRACT-001" in content


# ── Lien depuis reference.md ──────────────────────────────────────────────────

def test_reference_mentionne_stability_contract():
    content = REFERENCE.read_text(encoding="utf-8")
    assert "stability-contract" in content or "contrat de stabilité" in content.lower()
