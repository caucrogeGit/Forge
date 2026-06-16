"""Garde-fou SKELETON-VSCODE-DX-001.

Le squelette (`forge new`, ADR-024) embarque, dans son `.vscode/settings.json`,
de quoi offrir une bonne DX VS Code dès la création du projet :

- les **associations de schémas JSON** (`json.schemas`) pour valider et
  autocompléter `mvc/entities/*/*.json`, `mvc/entities/relations.json` et
  `mvc/security/rbac.json`, en pointant vers un dossier `schemas/` embarqué à la
  racine du projet (URL relatives `./schemas/*.schema.json`) ;
- l'**auto-import des classes** (Pylance) via
  `python.analysis.autoImportCompletions` et l'indexation du paquet `core`.

Pour que les `json.schemas` fonctionnent dans un projet généré, les fichiers de
schémas doivent être livrés par le squelette (il n'y a pas de `schemas/` ailleurs
dans un projet `forge new`).

Test documentaire / structurel : il lit du texte, il n'exécute aucun service.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SKELETON_DATA = PROJECT_ROOT / "forge_cli" / "skeleton" / "data"
SKELETON_VSCODE = SKELETON_DATA / ".vscode" / "settings.json"
SKELETON_SCHEMAS = SKELETON_DATA / "schemas"

# Schémas référencés par json.schemas (et leurs dépendances $ref minimales).
REFERENCED_SCHEMAS = ["entity.schema.json", "relations.schema.json", "rbac.schema.json"]


def _settings() -> dict:
    return json.loads(SKELETON_VSCODE.read_text(encoding="utf-8"))


# ── Auto-import des classes (Pylance) ─────────────────────────────────────────

def test_settings_active_auto_import():
    data = _settings()
    assert data.get("python.analysis.autoImportCompletions") is True, (
        "Le squelette doit activer python.analysis.autoImportCompletions pour "
        "que VS Code propose les imports de classes automatiquement."
    )


def test_settings_active_indexation():
    data = _settings()
    assert data.get("python.analysis.indexing") is True
    depths = data.get("python.analysis.packageIndexDepths", [])
    assert any(entry.get("name") == "core" for entry in depths), (
        "packageIndexDepths doit indexer le paquet core en profondeur."
    )


# ── Associations de schémas JSON ──────────────────────────────────────────────

def test_settings_contient_json_schemas():
    data = _settings()
    schemas = data.get("json.schemas")
    assert isinstance(schemas, list) and schemas, "json.schemas doit être une liste non vide."


def test_json_schemas_referencent_les_trois_contrats():
    data = _settings()
    urls = {entry.get("url") for entry in data.get("json.schemas", [])}
    for name in REFERENCED_SCHEMAS:
        assert f"./schemas/{name}" in urls, (
            f"json.schemas doit associer ./schemas/{name} (URL relative au projet)."
        )


# ── Schémas embarqués par le squelette ────────────────────────────────────────

def test_squelette_embarque_les_schemas():
    assert SKELETON_SCHEMAS.is_dir(), (
        "Le squelette doit embarquer un dossier schemas/ pour que les json.schemas "
        "résolvent dans un projet généré."
    )
    for name in REFERENCED_SCHEMAS:
        assert (SKELETON_SCHEMAS / name).is_file(), f"schemas/{name} manquant dans le squelette."


def test_schemas_embarques_sont_du_json_valide():
    for path in SKELETON_SCHEMAS.glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


# ── Association env/* conservée (ne pas régresser SKELETON-VSCODE-ENV-ASSOCIATION-001) ──

def test_settings_conserve_association_env():
    data = _settings()
    assert data.get("files.associations", {}).get("**/env/*") == "properties"
