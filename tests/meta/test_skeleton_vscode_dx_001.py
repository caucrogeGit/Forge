"""Garde-fou SKELETON-VSCODE-DX-001.

Le squelette (`forge new`, ADR-024) embarque, dans son `.vscode/settings.json`,
de quoi offrir une bonne DX VS Code dès la création du projet :

- les **associations de schémas JSON** (`json.schemas`) **cœur** pour valider et
  autocompléter `mvc/entities/*/*.json` et `mvc/entities/relations.json`, en
  pointant vers un dossier `schemas/` embarqué à la racine du projet (URL
  relatives `./schemas/*.schema.json`). Les schémas opt-in (ex. `rbac.json` →
  `forge-mvc-rbac`) ne sont **pas** dans le squelette nu : c'est au câble de
  l'opt-in de les introduire (principe 8) ;
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

# Schémas cœur associés par json.schemas dans le squelette NU. RBAC est un
# opt-in (forge-mvc-rbac) : ni rbac.schema.json ni son fileMatch ne doivent
# figurer dans le squelette nu (principe 8). C'est au câble de l'opt-in de
# l'introduire.
REFERENCED_SCHEMAS = ["entity.schema.json", "relations.schema.json"]

# Schémas cœur embarqués : entity + relations et leurs dépendances $ref
# (field, common ; pivot car relations.schema.json référence pivot.schema.json
# pour les relations many_to_many).
SHIPPED_SCHEMAS = [
    "entity.schema.json", "field.schema.json", "common.schema.json",
    "relations.schema.json", "pivot.schema.json",
]


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

def test_squelette_embarque_les_schemas_coeur():
    assert SKELETON_SCHEMAS.is_dir(), (
        "Le squelette doit embarquer un dossier schemas/ pour que les json.schemas "
        "résolvent dans un projet généré."
    )
    for name in SHIPPED_SCHEMAS:
        assert (SKELETON_SCHEMAS / name).is_file(), f"schemas/{name} manquant dans le squelette."


def test_squelette_nu_sans_schema_opt_in():
    """Principe 8 : le squelette nu ne porte aucun schéma ni association opt-in."""
    assert not (SKELETON_SCHEMAS / "rbac.schema.json").exists(), (
        "rbac.schema.json (opt-in forge-mvc-rbac) ne doit pas figurer dans le "
        "squelette nu : c'est au câble de l'opt-in de l'introduire."
    )
    urls = {entry.get("url") for entry in _settings().get("json.schemas", [])}
    fmatches = {fm for entry in _settings().get("json.schemas", []) for fm in entry.get("fileMatch", [])}
    assert "./schemas/rbac.schema.json" not in urls, "Pas d'association rbac dans le squelette nu."
    assert "/mvc/security/rbac.json" not in fmatches, "Pas de fileMatch rbac.json dans le squelette nu."


def test_schemas_embarques_sont_du_json_valide():
    for path in SKELETON_SCHEMAS.glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


# ── Association env/* conservée (ne pas régresser SKELETON-VSCODE-ENV-ASSOCIATION-001) ──

def test_settings_conserve_association_env():
    data = _settings()
    assert data.get("files.associations", {}).get("**/env/*") == "properties"


# ── Mode strict par défaut (SKELETON-VSCODE-STRICT-DEFAULT-001) ──────────────

def test_settings_active_le_mode_strict():
    """Le cœur Forge est entièrement strict (cliquet ADR-036) et le code généré
    du squelette est strict-clean : un projet `forge new` démarre directement en
    `typeCheckingMode: strict`, sans bruit `reportUnknown*` sur le cœur typé."""
    assert _settings().get("python.analysis.typeCheckingMode") == "strict"


# ── Override reportUnknown* retiré (SKELETON-VSCODE-STRICT-NOISE-REMOVE-001) ──

def test_settings_ne_neutralise_plus_la_famille_reportunknown():
    """Le cœur Forge est désormais entièrement strict (cliquet ADR-036 terminé,
    `pyright core/` à 0 erreur). La famille reportUnknown* ne génère donc plus de
    bruit sur les symboles du cœur, et le squelette ne la neutralise plus : un
    projet généré bénéficie d'un mode strict complet, y compris sur l'interop
    avec le cœur typé. Garde-fou d'absence."""
    overrides = _settings().get("python.analysis.diagnosticSeverityOverrides", {})
    for rule in (
        "reportUnknownMemberType",
        "reportUnknownVariableType",
        "reportUnknownArgumentType",
        "reportUnknownParameterType",
        "reportUnknownLambdaType",
    ):
        assert rule not in overrides, (
            f"{rule} ne doit plus être neutralisé : le cœur est entièrement strict (ADR-036)."
        )
