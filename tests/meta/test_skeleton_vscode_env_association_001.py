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

import glob
import json
import os
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SKELETON_VSCODE = PROJECT_ROOT / "skeleton" / "data" / ".vscode" / "settings.json"


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
    assert assoc.get("**/env/*") == "properties", (
        "**/env/* doit être associé au langage intégré 'properties' "
        "(motif ancré pour matcher le chemin ; pas de dépendance à une extension dotenv)"
    )


def test_skeleton_vscode_is_materialized_by_forge_new():
    from skeleton import DATA_DIR, iter_skeleton_files
    rel = {str(p.relative_to(DATA_DIR)) for p in iter_skeleton_files()}
    assert ".vscode/settings.json" in rel, (
        "iter_skeleton_files() doit inclure .vscode/settings.json pour que "
        "forge new le copie dans le projet généré"
    )


def test_pyproject_package_data_includes_dot_dir_files():
    """Le wheel doit embarquer les fichiers situés DANS un dossier dot du
    squelette (ex. .vscode/settings.json).

    Les globs `**/*` ne descendent pas dans les dossiers cachés, d'où le
    besoin d'un glob package-data dédié (ex. `data/.*/**/*`). Ce test vérifie
    l'effet, pas la formulation exacte : au moins un pattern de
    package-data['skeleton'] (paquet racine, ADR-065) doit matcher la cible.
    """
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = pyproject["tool"]["setuptools"]["package-data"]["skeleton"]
    pkg_dir = PROJECT_ROOT / "skeleton"
    target = "data/.vscode/settings.json"

    matched = any(
        target in {p.replace(os.sep, "/") for p in glob.glob(pat, root_dir=pkg_dir, recursive=True)}
        for pat in patterns
    )
    assert matched, (
        "package-data['skeleton'] doit contenir un glob couvrant les fichiers "
        "dans les dossiers dot du squelette (ex. 'data/.*/**/*'), sinon "
        ".vscode/settings.json est exclu du wheel et forge new ne le matérialise pas."
    )
