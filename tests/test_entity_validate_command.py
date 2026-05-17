"""Garde-fou ENTITY-CONTRACT-007 + ENTITY-CONTRACT-007-FIX-DEPENDENCY.

Vérifie que la commande forge entity:validate :
- est reconnue par le CLI ;
- retourne 0 pour un projet temporaire avec entité valide ;
- retourne 0 pour relations.json valide ;
- retourne non-nul pour une entité avec champ 'id' ;
- retourne non-nul pour une entité avec type inconnu ;
- retourne non-nul pour une entité avec clé inconnue ;
- retourne non-nul pour relations.json avec one_to_one ;
- retourne non-nul pour relations.json avec many_to_many sans pivot ;
- ne plante pas si relations.json est absent ;
- retourne non-nul pour un JSON syntaxiquement invalide ;
- produit une sortie mentionnant le fichier concerné ;
- produit une synthèse finale.

Vérifie aussi (ENTITY-CONTRACT-007-FIX-DEPENDENCY) que :
- jsonschema est déclaré dans pyproject.toml.

Les tests utilisent des projets temporaires isolés (tmp_path) et n'ont
pas de dépendance au format legacy réel du dépôt.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"

jsonschema = pytest.importorskip("jsonschema", reason="jsonschema non installé — pip install jsonschema>=4.18")


def _run(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), "entity:validate"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _make_project(tmp_path: Path, entities: dict[str, dict], relations: dict | None = None) -> Path:
    """Crée un projet temporaire avec les fichiers d'entités donnés."""
    entities_dir = tmp_path / "mvc" / "entities"
    entities_dir.mkdir(parents=True)
    for filename, data in entities.items():
        (entities_dir / filename).write_text(json.dumps(data), encoding="utf-8")
    if relations is not None:
        (entities_dir / "relations.json").write_text(json.dumps(relations), encoding="utf-8")
    return tmp_path


_VALID_ENTITY = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "title", "type": "string"}
    ],
}

_VALID_RELATIONS = {
    "schema_version": "1.0",
    "relations": [],
}


class TestCommandRecognized:
    def test_command_is_recognized(self, tmp_path):
        """La commande entity:validate est connue du CLI (pas d'erreur 'commande inconnue')."""
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        combined = result.stdout + result.stderr
        assert "commande inconnue" not in combined.lower()
        assert "unknown command" not in combined.lower()


class TestValidProject:
    def test_valid_entity_returns_zero(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"

    def test_valid_entity_shows_ok(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        assert "[OK]" in result.stdout

    def test_valid_entity_shows_summary(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        assert "Validation terminée" in result.stdout

    def test_valid_relations_returns_zero(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=_VALID_RELATIONS)
        result = _run(proj)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"

    def test_valid_relations_shows_ok(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=_VALID_RELATIONS)
        result = _run(proj)
        assert "[OK]" in result.stdout
        assert "relations.json" in result.stdout

    def test_multiple_valid_entities_returns_zero(self, tmp_path):
        entities = {
            "article.json": _VALID_ENTITY,
            "category.json": {
                "schema_version": "1.0",
                "name": "Category",
                "table": "categories",
                "fields": [{"name": "label", "type": "string"}],
            },
        }
        proj = _make_project(tmp_path, entities)
        result = _run(proj)
        assert result.returncode == 0


class TestInvalidEntities:
    def test_field_named_id_returns_nonzero(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert result.returncode != 0

    def test_unknown_field_type_returns_nonzero(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "photo", "type": "image"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert result.returncode != 0

    def test_unknown_entity_key_returns_nonzero(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "title", "type": "string"}],
            "controller": "ArticleController",
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert result.returncode != 0

    def test_missing_required_field_returns_nonzero(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "fields": [{"name": "title", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert result.returncode != 0

    def test_error_output_mentions_file(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert "article.json" in result.stdout


class TestInvalidRelations:
    def test_one_to_one_returns_nonzero(self, tmp_path):
        relations = {
            "schema_version": "1.0",
            "relations": [
                {"type": "one_to_one", "from": "A", "to": "B", "name": "ab"}
            ],
        }
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=relations)
        result = _run(proj)
        assert result.returncode != 0

    def test_many_to_many_without_pivot_returns_nonzero(self, tmp_path):
        relations = {
            "schema_version": "1.0",
            "relations": [
                {"type": "many_to_many", "from": "Article", "to": "Tag", "name": "tags"}
            ],
        }
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=relations)
        result = _run(proj)
        assert result.returncode != 0


class TestEdgeCases:
    def test_no_relations_file_does_not_crash(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        assert result.returncode == 0

    def test_invalid_json_returns_nonzero(self, tmp_path):
        entities_dir = tmp_path / "mvc" / "entities"
        entities_dir.mkdir(parents=True)
        (entities_dir / "broken.json").write_text("{invalid json}", encoding="utf-8")
        result = _run(tmp_path)
        assert result.returncode != 0

    def test_missing_entities_dir_returns_nonzero(self, tmp_path):
        result = _run(tmp_path)
        assert result.returncode != 0

    def test_missing_entities_dir_shows_error(self, tmp_path):
        result = _run(tmp_path)
        combined = result.stdout + result.stderr
        assert "mvc/entities" in combined


class TestOutputFormat:
    def test_output_has_no_json_machine(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        try:
            json.loads(result.stdout)
            assert False, "La sortie ne doit pas être du JSON machine."
        except json.JSONDecodeError:
            pass

    def test_error_output_mentions_path(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert "Chemin" in result.stdout or "chemin" in result.stdout.lower()

    def test_summary_shows_counts(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        assert "0 erreur" in result.stdout

    def test_error_summary_shows_error_count(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert "erreur" in result.stdout


class TestDependencyDeclaration:
    def test_pyproject_declares_jsonschema_dependency(self):
        """jsonschema doit être déclaré dans pyproject.toml (ENTITY-CONTRACT-007-FIX-DEPENDENCY)."""
        import tomllib
        pyproject = PROJECT_ROOT / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        deps = data.get("project", {}).get("dependencies", [])
        declared = any("jsonschema" in dep for dep in deps)
        assert declared, (
            "jsonschema doit être dans [project].dependencies de pyproject.toml "
            "(requis par forge entity:validate)."
        )
