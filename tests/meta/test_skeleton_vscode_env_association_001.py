"""Garde-fou SKELETON-VSCODE-ENV-ASSOCIATION-001.

Le squelette (`forge new`, ADR-024) embarque un `.vscode/settings.json` qui
associe les fichiers `env/*` au langage `properties`, afin que VS Code colore
`env/dev`, `env/prod`, `env/example` (KEY=VALUE, commentaires `#`) sans qu'il
faille renommer ces fichiers ni installer une extension dédiée.

Vérifie que :
- le fichier existe et est un JSON valide ;
- l'association `env/*` -> `properties` est présente, au niveau racine ;
- `iter_skeleton_files()` le retourne, donc `forge new` le matérialise
  (la copie depuis un checkout source est couverte ; l'inclusion dans le
  wheel dépend en plus d'un glob package-data, voir le test ci-dessous).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SKELETON_VSCODE = PROJECT_ROOT / "forge_cli" / "skeleton" / "data" / ".vscode" / "settings.json"


def test_skeleton_vscode_settings_exists():
    assert SKELETON_VSCODE.exists(), (
        "Le squelette doit fournir .vscode/settings.json pour colorer env/* dans VS Code"
    )


def test_skeleton_vscode_settings_is_valid_json():
    json.loads(SKELETON_VSCODE.read_text(encoding="utf-8"))


def test_skeleton_vscode_associates_env_to_properties():
    data = json.loads(SKELETON_VSCODE.read_text(encoding="utf-8"))
    assoc = data.get("files.associations")
    assert isinstance(assoc, dict), "files.associations doit être un objet au niveau racine"
    assert assoc.get("env/*") == "properties", (
        "env/* doit être associé au langage intégré 'properties' "
        "(pas de dépendance à une extension dotenv)"
    )


def test_skeleton_vscode_is_materialized_by_forge_new():
    from forge_cli.skeleton import DATA_DIR, iter_skeleton_files
    rel = {str(p.relative_to(DATA_DIR)) for p in iter_skeleton_files()}
    assert ".vscode/settings.json" in rel, (
        "iter_skeleton_files() doit inclure .vscode/settings.json pour que "
        "forge new le copie dans le projet généré"
    )
