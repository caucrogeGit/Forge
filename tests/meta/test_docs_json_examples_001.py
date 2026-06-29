"""ENTITY-CONTRACT-020 — Validation des exemples JSON documentaires.

Vérifie que les exemples JSON complets présents dans docs/entities/ sont
valides selon les schémas JSON Forge (entity.schema.json, relations.schema.json,
pivot.schema.json).

Stratégie :
- Les exemples complets canoniques sont extraits directement des fichiers
  Markdown par recherche de blocs ```json, puis classifiés automatiquement.
- Un exemple est "canonique" s'il parse comme JSON valide ET possède
  schema_version + les clés requises d'une entité ou d'un fichier de relations.
- Les exemples volontairement invalides (sections "Erreurs fréquentes",
  "Ce qui n'est plus canonique") ne portent pas schema_version — ils ne
  sont donc pas sélectionnés pour validation.
- Les fragments partiels (champs isolés, valeurs JSON incomplètes) ne
  parsent pas comme JSON valide et sont automatiquement ignorés.
- Les exemples VS Code (json.schemas) ne sont pas des fichiers Forge :
  ils sont vérifiés par inspection textuelle de la page dédiée.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ENTITIES = PROJECT_ROOT / "docs" / "entities"
SCHEMAS_DIR = PROJECT_ROOT / "cli" / "schemas"

LEGACY_KEYS = frozenset(
    [
        "format_version",
        "from_entity",
        "to_entity",
        "foreign_key_name",
        "pivot_table",
        "source_key",
        "target_key",
        "sql_type",
        "python_type",
        "primary_key",
        "auto_increment",
    ]
)

DOCS_PAGES = [
    "entity-schema.md",
    "json-canonique.md",
    "relations-schema.md",
    "pivots-many-to-many.md",
    "entity-validate.md",
    "vscode-json-schema.md",
    "limites-contrats-json.md",
    "types-forge-mariadb.md",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_schema_registry(schemas_dir: Path = SCHEMAS_DIR) -> tuple[Registry, dict[str, Any]]:
    resources: list[tuple[str, Resource]] = []
    by_id: dict[str, Any] = {}
    for sf in schemas_dir.glob("*.json"):
        schema = json.loads(sf.read_text(encoding="utf-8"))
        sid = schema.get("$id")
        if sid:
            resources.append((sid, Resource.from_contents(schema, DRAFT202012)))
            by_id[sid] = schema
    registry = Registry().with_resources(resources)
    return registry, by_id


def _extract_json_blocks(text: str) -> list[str]:
    """Extrait les blocs ```json ... ``` d'un fichier Markdown."""
    blocks: list[str] = []
    in_block = False
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "```json":
            in_block = True
            current = []
        elif stripped == "```" and in_block:
            in_block = False
            blocks.append("\n".join(current))
        elif in_block:
            current.append(line)
    return blocks


def _try_parse_json(raw: str) -> Any | None:
    """Retourne l'objet Python si raw est du JSON valide, None sinon."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _classify_blocks(page: Path) -> dict[str, list[Any]]:
    """
    Retourne trois listes d'objets JSON parsés depuis une page Markdown :
      "entity"    — blocs reconnus comme entités canoniques complètes
      "relations" — blocs reconnus comme relations.json canoniques complets
      "other"     — blocs valides JSON mais ni entité ni relations (ignorés)
    """
    text = page.read_text(encoding="utf-8")
    blocks = _extract_json_blocks(text)
    result: dict[str, list[Any]] = {"entity": [], "relations": [], "other": []}
    for raw in blocks:
        obj = _try_parse_json(raw)
        if not isinstance(obj, dict):
            continue
        if obj.get("schema_version") == "1.0":
            required_entity = {"name", "table", "fields"}
            required_relations = {"relations"}
            if required_entity.issubset(obj.keys()):
                result["entity"].append(obj)
            elif required_relations.issubset(obj.keys()):
                result["relations"].append(obj)
            else:
                result["other"].append(obj)
    return result


REGISTRY, SCHEMAS_BY_ID = _load_schema_registry()
# pivot.schema.json est extrait vers l'opt-in forge-mvc-pivot (ADR-057/058) :
# on valide les exemples pivot des docs contre le schéma embarqué par le paquet.
PIVOT_SCHEMAS_DIR = (
    PROJECT_ROOT / "packages" / "forge-mvc-pivot" / "forge_mvc_pivot" / "schemas"
)
PIVOT_REGISTRY, PIVOT_SCHEMAS_BY_ID = _load_schema_registry(PIVOT_SCHEMAS_DIR)
ENTITY_SCHEMA_ID = "https://forge-mvc.dev/schemas/entity.schema.json"
RELATIONS_SCHEMA_ID = "https://forge-mvc.dev/schemas/relations.schema.json"
PIVOT_SCHEMA_ID = "https://forge-mvc.dev/schemas/pivot.schema.json"


# ---------------------------------------------------------------------------
# Tests — existence des pages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("page", DOCS_PAGES)
def test_docs_entities_page_exists(page):
    assert (DOCS_ENTITIES / page).exists(), f"Page introuvable : docs/entities/{page}"


# ---------------------------------------------------------------------------
# Tests — exemples d'entités canoniques
# ---------------------------------------------------------------------------


def _all_canonical_entities() -> list[tuple[str, Any]]:
    """Collecte tous les exemples d'entités canoniques de docs/entities/."""
    results = []
    for page_name in DOCS_PAGES:
        page = DOCS_ENTITIES / page_name
        if not page.exists():
            continue
        classified = _classify_blocks(page)
        for example in classified["entity"]:
            results.append((page_name, example))
    return results


_CANONICAL_ENTITIES = _all_canonical_entities()


@pytest.mark.parametrize("page_name,example", _CANONICAL_ENTITIES, ids=[p for p, _ in _CANONICAL_ENTITIES])
def test_canonical_entity_valid_schema(page_name, example):
    """Chaque exemple d'entité canonique doit respecter entity.schema.json."""
    schema = SCHEMAS_BY_ID[ENTITY_SCHEMA_ID]
    validator = Draft202012Validator(schema, registry=REGISTRY)
    errors = list(validator.iter_errors(example))
    assert not errors, (
        f"Exemple entité dans {page_name} invalide selon entity.schema.json :\n"
        + "\n".join(f"  - {e.json_path}: {e.message}" for e in errors)
    )


@pytest.mark.parametrize("page_name,example", _CANONICAL_ENTITIES, ids=[p for p, _ in _CANONICAL_ENTITIES])
def test_canonical_entity_no_id_in_fields(page_name, example):
    """Aucun champ 'id' ne doit apparaître dans fields[] des exemples canoniques."""
    field_names = [f.get("name") for f in example.get("fields", []) if isinstance(f, dict)]
    assert "id" not in field_names, (
        f"Exemple entité dans {page_name} déclare 'id' dans fields[] — interdit dans le format canonique"
    )


@pytest.mark.parametrize("page_name,example", _CANONICAL_ENTITIES, ids=[p for p, _ in _CANONICAL_ENTITIES])
def test_canonical_entity_no_legacy_keys(page_name, example):
    """Aucune clé legacy ne doit apparaître dans les exemples d'entités canoniques."""
    found = LEGACY_KEYS & set(example.keys())
    assert not found, (
        f"Exemple entité dans {page_name} contient des clés legacy : {found}"
    )


# ---------------------------------------------------------------------------
# Tests — exemples de relations canoniques
# ---------------------------------------------------------------------------


def _all_canonical_relations() -> list[tuple[str, Any]]:
    results = []
    for page_name in DOCS_PAGES:
        page = DOCS_ENTITIES / page_name
        if not page.exists():
            continue
        classified = _classify_blocks(page)
        for example in classified["relations"]:
            results.append((page_name, example))
    return results


_CANONICAL_RELATIONS = _all_canonical_relations()


@pytest.mark.parametrize("page_name,example", _CANONICAL_RELATIONS, ids=[p for p, _ in _CANONICAL_RELATIONS])
def test_canonical_relations_valid_schema(page_name, example):
    """Chaque exemple relations.json canonique doit respecter relations.schema.json."""
    schema = SCHEMAS_BY_ID[RELATIONS_SCHEMA_ID]
    validator = Draft202012Validator(schema, registry=REGISTRY)
    errors = list(validator.iter_errors(example))
    assert not errors, (
        f"Exemple relations dans {page_name} invalide selon relations.schema.json :\n"
        + "\n".join(f"  - {e.json_path}: {e.message}" for e in errors)
    )


@pytest.mark.parametrize("page_name,example", _CANONICAL_RELATIONS, ids=[p for p, _ in _CANONICAL_RELATIONS])
def test_canonical_relations_no_legacy_keys(page_name, example):
    """Aucune clé legacy au niveau racine dans les relations canoniques."""
    found = LEGACY_KEYS & set(example.keys())
    assert not found, (
        f"Exemple relations dans {page_name} contient des clés legacy : {found}"
    )


# ---------------------------------------------------------------------------
# Tests — exemples de pivot (extraits des relations many_to_many)
# ---------------------------------------------------------------------------


def _all_pivot_examples() -> list[tuple[str, Any]]:
    """Collecte les blocs pivot dans les relations many_to_many des docs."""
    results = []
    for page_name in DOCS_PAGES:
        page = DOCS_ENTITIES / page_name
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")
        for raw in _extract_json_blocks(text):
            obj = _try_parse_json(raw)
            if not isinstance(obj, dict):
                continue
            # Relation many_to_many avec pivot intégré (fragment de relation)
            if obj.get("type") == "many_to_many" and isinstance(obj.get("pivot"), dict):
                results.append((page_name, obj["pivot"]))
            # Relations.json canonique — extraire les pivots des relations m2m
            if obj.get("schema_version") == "1.0" and "relations" in obj:
                for rel in obj.get("relations", []):
                    if isinstance(rel, dict) and rel.get("type") == "many_to_many":
                        if isinstance(rel.get("pivot"), dict):
                            results.append((page_name, rel["pivot"]))
    return results


_PIVOT_EXAMPLES = _all_pivot_examples()


@pytest.mark.parametrize("page_name,pivot", _PIVOT_EXAMPLES, ids=[p for p, _ in _PIVOT_EXAMPLES])
def test_pivot_example_valid_schema(page_name, pivot):
    """Chaque exemple de pivot doit respecter pivot.schema.json."""
    schema = PIVOT_SCHEMAS_BY_ID[PIVOT_SCHEMA_ID]
    validator = Draft202012Validator(schema, registry=PIVOT_REGISTRY)
    errors = list(validator.iter_errors(pivot))
    assert not errors, (
        f"Exemple pivot dans {page_name} invalide selon pivot.schema.json :\n"
        + "\n".join(f"  - {e.json_path}: {e.message}" for e in errors)
    )


@pytest.mark.parametrize("page_name,pivot", _PIVOT_EXAMPLES, ids=[p for p, _ in _PIVOT_EXAMPLES])
def test_pivot_id_is_true(page_name, pivot):
    assert pivot.get("id") is True, f"pivot.id doit être true dans {page_name}"


@pytest.mark.parametrize("page_name,pivot", _PIVOT_EXAMPLES, ids=[p for p, _ in _PIVOT_EXAMPLES])
def test_pivot_unique_pair_is_true(page_name, pivot):
    assert pivot.get("unique_pair") is True, f"pivot.unique_pair doit être true dans {page_name}"


@pytest.mark.parametrize("page_name,pivot", _PIVOT_EXAMPLES, ids=[p for p, _ in _PIVOT_EXAMPLES])
def test_pivot_from_key_differs_from_to_key(page_name, pivot):
    assert pivot.get("from_key") != pivot.get("to_key"), (
        f"pivot.from_key == pivot.to_key dans {page_name} — collision interdite"
    )


@pytest.mark.parametrize("page_name,pivot", _PIVOT_EXAMPLES, ids=[p for p, _ in _PIVOT_EXAMPLES])
def test_pivot_fields_no_reserved_names(page_name, pivot):
    """pivot.fields[] ne doit pas redéclarer id, from_key ou to_key."""
    reserved = {"id", pivot.get("from_key"), pivot.get("to_key")}
    field_names = {f["name"] for f in pivot.get("fields", []) if isinstance(f, dict) and "name" in f}
    collision = field_names & reserved
    assert not collision, (
        f"pivot.fields[] dans {page_name} redéclare des noms réservés : {collision}"
    )


# ---------------------------------------------------------------------------
# Tests — exemples canoniques : absence de clés legacy dans les relations items
# ---------------------------------------------------------------------------


def test_canonical_relations_items_no_legacy_keys():
    """Les items de relation dans les exemples canoniques ne contiennent pas de clés legacy."""
    legacy_relation_keys = frozenset(
        ["from_entity", "to_entity", "foreign_key_name", "pivot_table", "source_key", "target_key"]
    )
    violations = []
    for page_name in DOCS_PAGES:
        page = DOCS_ENTITIES / page_name
        if not page.exists():
            continue
        classified = _classify_blocks(page)
        for example in classified["relations"]:
            for rel in example.get("relations", []):
                if not isinstance(rel, dict):
                    continue
                found = legacy_relation_keys & set(rel.keys())
                if found:
                    violations.append(f"{page_name}: {found}")
    assert not violations, "Clés legacy dans items de relations canoniques :\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# Tests — page VS Code
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def vscode_page_content() -> str:
    path = DOCS_ENTITIES / "vscode-json-schema.md"
    assert path.exists()
    return path.read_text(encoding="utf-8")


def test_vscode_page_has_dollar_schema(vscode_page_content):
    assert '"$schema"' in vscode_page_content or "$schema" in vscode_page_content


def test_vscode_page_has_json_schemas(vscode_page_content):
    assert "json.schemas" in vscode_page_content


def test_vscode_page_has_entity_schema_json(vscode_page_content):
    assert "entity.schema.json" in vscode_page_content


def test_vscode_page_has_relations_schema_json(vscode_page_content):
    assert "relations.schema.json" in vscode_page_content


def test_vscode_json_schemas_example_is_valid_json(vscode_page_content):
    """Les blocs json.schemas dans la page VS Code parsent comme JSON valide."""
    blocks = _extract_json_blocks(vscode_page_content)
    vscode_settings_blocks = [b for b in blocks if "json.schemas" in b]
    assert vscode_settings_blocks, "Aucun bloc json.schemas trouvé dans vscode-json-schema.md"
    for raw in vscode_settings_blocks:
        obj = _try_parse_json(raw)
        assert obj is not None, f"Bloc json.schemas invalide JSON :\n{raw}"
        assert "json.schemas" in obj, "Clé 'json.schemas' absente du bloc VS Code"


def test_vscode_settings_json_in_repo():
    """VSCODE-DX-001 crée .vscode/settings.json avec les json.schemas Forge."""
    vscode_settings = PROJECT_ROOT / ".vscode" / "settings.json"
    assert vscode_settings.exists(), (
        ".vscode/settings.json doit exister dans le dépôt Forge "
        "(créé par VSCODE-DX-001 — voir vscode-json-schema.md)"
    )
    assert "json.schemas" in vscode_settings.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests — couverture minimale garantie
# ---------------------------------------------------------------------------


def test_at_least_one_canonical_entity_found():
    """Au moins une entité canonique doit être détectée dans les docs."""
    assert _CANONICAL_ENTITIES, "Aucun exemple d'entité canonique détecté dans docs/entities/"


def test_at_least_one_canonical_relations_found():
    """Au moins un exemple relations.json canonique doit être détecté."""
    assert _CANONICAL_RELATIONS, "Aucun exemple de relations canonique détecté dans docs/entities/"


def test_at_least_one_pivot_found():
    """Au moins un exemple de pivot doit être détecté."""
    assert _PIVOT_EXAMPLES, "Aucun exemple de pivot détecté dans docs/entities/"


def test_canonical_entities_cover_required_pages():
    """Les pages principales doivent chacune fournir au moins un exemple canonique."""
    pages_with_entities = {p for p, _ in _CANONICAL_ENTITIES}
    required_pages = {"entity-schema.md", "json-canonique.md"}
    missing = required_pages - pages_with_entities
    assert not missing, f"Pages sans exemple d'entité canonique : {missing}"


def test_canonical_relations_cover_required_pages():
    """Les pages principales doivent fournir au moins un exemple de relations canonique."""
    pages_with_relations = {p for p, _ in _CANONICAL_RELATIONS}
    required_pages = {"relations-schema.md", "json-canonique.md"}
    missing = required_pages - pages_with_relations
    assert not missing, f"Pages sans exemple de relations canonique : {missing}"


def test_pivot_examples_cover_required_pages():
    """Les pages pivot et relations doivent fournir des exemples de pivot."""
    pages_with_pivots = {p for p, _ in _PIVOT_EXAMPLES}
    required_pages = {"pivots-many-to-many.md"}
    missing = required_pages - pages_with_pivots
    assert not missing, f"Pages sans exemple de pivot : {missing}"
