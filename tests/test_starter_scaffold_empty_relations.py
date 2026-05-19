"""Tests LEGACY-SCAFFOLD-FIX-001 : détection relations.json vide (legacy et canonique)."""

from __future__ import annotations

import json
from pathlib import Path

from forge_cli.starters.scaffold import check_existing


# ── Helpers ────────────────────────────────────────────────────────────────────


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _relations_path(root: Path) -> Path:
    return root / "mvc" / "entities" / "relations.json"


def _meta_carnet() -> dict:
    return {
        "id": "carnet-contacts",
        "check_paths": ["mvc/entities/relations.json"],
    }


def _meta_suivi() -> dict:
    return {
        "id": "suivi-comportement-eleves",
        "check_paths": ["mvc/entities/relations.json"],
    }


# ── Legacy vide — adoptable ────────────────────────────────────────────────────


def test_relations_legacy_vide_carnet_adoptable(tmp_path):
    """relations.json legacy vide est adoptable par carnet-contacts."""
    _write(_relations_path(tmp_path), {"format_version": 1, "relations": []})
    assert check_existing(_meta_carnet(), tmp_path) == []


def test_relations_legacy_vide_suivi_adoptable(tmp_path):
    """relations.json legacy vide est adoptable par suivi-comportement-eleves."""
    _write(_relations_path(tmp_path), {"format_version": 1, "relations": []})
    assert check_existing(_meta_suivi(), tmp_path) == []


# ── Canonique vide — adoptable ─────────────────────────────────────────────────


def test_relations_canonique_vide_carnet_adoptable(tmp_path):
    """relations.json canonique vide est adoptable par carnet-contacts."""
    _write(_relations_path(tmp_path), {"schema_version": "1.0", "relations": []})
    assert check_existing(_meta_carnet(), tmp_path) == []


def test_relations_canonique_vide_suivi_adoptable(tmp_path):
    """relations.json canonique vide est adoptable par suivi-comportement-eleves."""
    _write(_relations_path(tmp_path), {"schema_version": "1.0", "relations": []})
    assert check_existing(_meta_suivi(), tmp_path) == []


# ── Non vide — non adoptable ──────────────────────────────────────────────────


def test_relations_canonique_non_vide_non_adoptable(tmp_path):
    """relations.json canonique avec relations réelles bloque check_existing."""
    _write(_relations_path(tmp_path), {
        "schema_version": "1.0",
        "relations": [{"type": "many_to_one", "from": "Contact", "to": "Ville"}],
    })
    result = check_existing(_meta_carnet(), tmp_path)
    assert "mvc/entities/relations.json" in result


def test_relations_legacy_non_vide_non_adoptable(tmp_path):
    """relations.json legacy avec relations réelles bloque check_existing."""
    _write(_relations_path(tmp_path), {
        "format_version": 1,
        "relations": [{"type": "many_to_one", "from_entity": "Contact", "to_entity": "Ville"}],
    })
    result = check_existing(_meta_carnet(), tmp_path)
    assert "mvc/entities/relations.json" in result


# ── Structure inattendue — pas de traceback ────────────────────────────────────


def test_relations_json_invalide_non_adoptable(tmp_path):
    """JSON invalide n'est pas adoptable et ne lève pas de traceback."""
    p = _relations_path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json {{{", encoding="utf-8")
    result = check_existing(_meta_carnet(), tmp_path)
    assert "mvc/entities/relations.json" in result


def test_relations_json_liste_non_adoptable(tmp_path):
    """Un relations.json contenant une liste (structure inattendue) n'est pas adoptable."""
    _write(_relations_path(tmp_path), [])
    result = check_existing(_meta_carnet(), tmp_path)
    assert "mvc/entities/relations.json" in result


def test_relations_sans_cle_relations_non_adoptable(tmp_path):
    """Un dict sans la clé 'relations' n'est pas adoptable."""
    _write(_relations_path(tmp_path), {"schema_version": "1.0"})
    result = check_existing(_meta_carnet(), tmp_path)
    assert "mvc/entities/relations.json" in result


# ── Starter non concerné — non adoptable via cette règle ──────────────────────


def test_relations_canonique_vide_autre_starter_non_adoptable(tmp_path):
    """La règle d'adoption ne s'applique pas aux starters non listés."""
    _write(_relations_path(tmp_path), {"schema_version": "1.0", "relations": []})
    meta = {
        "id": "contact-simple",
        "check_paths": ["mvc/entities/relations.json"],
    }
    result = check_existing(meta, tmp_path)
    assert "mvc/entities/relations.json" in result
