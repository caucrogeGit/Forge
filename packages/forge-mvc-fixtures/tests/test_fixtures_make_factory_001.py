"""Commande fixtures:make-factory (FIXTURES-MAKE-FACTORY-001, ADR-076).

Scaffold riche depuis le contrat d'entité : mapping type/nom vers provider Faker,
code Python valide, write-if-new.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures.cli.make_factory import (
    make_factory,
    provider_for_field,
    render_factory,
)


def _write_entity(root: Path, entity: str, contract: dict) -> None:
    d = root / "mvc" / "entities" / entity
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{entity}.json").write_text(json.dumps(contract), encoding="utf-8")


ARTICLE = {
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "title", "type": "string"},
        {"name": "content", "type": "text"},
        {"name": "published", "type": "boolean"},
        {"name": "published_at", "type": "datetime"},
        {"name": "author_email", "type": "email"},
        {"name": "category_id", "type": "foreign_key"},
    ],
}


class TestProviderMapping:

    @pytest.mark.parametrize("ftype, expected_fragment", [
        ("text", "paragraph"),
        ("boolean", "boolean"),
        ("datetime", "date_time"),
        ("email", "email"),
        ("integer", "random_int"),
        ("date", "date_object"),
    ])
    def test_by_type(self, ftype: str, expected_fragment: str) -> None:
        expr, _ = provider_for_field({"name": "x", "type": ftype})
        assert expected_fragment in expr

    def test_name_heuristic_on_string(self) -> None:
        expr, _ = provider_for_field({"name": "ville", "type": "string"})
        assert "city" in expr

    def test_name_heuristic_prenom_before_nom(self) -> None:
        expr, _ = provider_for_field({"name": "prenom", "type": "string"})
        assert "first_name" in expr

    def test_foreign_key_placeholder_with_comment(self) -> None:
        expr, comment = provider_for_field({"name": "category_id", "type": "foreign_key"})
        assert expr == "1"
        assert "clé étrangère" in comment

    def test_name_heuristic_ignored_on_typed_field(self) -> None:
        # Un champ « published » booléen ne doit pas être capté par une heuristique de nom.
        expr, _ = provider_for_field({"name": "published", "type": "boolean"})
        assert "boolean" in expr


class TestRenderFactory:

    def test_valid_python_with_class_and_table(self) -> None:
        src = render_factory(ARTICLE)
        assert "class ArticleFactory(Factory):" in src
        assert 'table = "articles"' in src
        assert '"title":' in src and '"category_id": 1,' in src
        # le code généré doit être du Python valide
        compile(src, "<factory>", "exec")


class TestMakeFactory:

    def test_writes_factory_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_entity(tmp_path, "article", ARTICLE)
        rc = make_factory(tmp_path, "article", force=False)
        assert rc == 0
        target = tmp_path / "mvc" / "fixtures" / "factories" / "article_factory.py"
        assert target.is_file()
        assert "ArticleFactory" in target.read_text(encoding="utf-8")
        assert "[OK]" in capsys.readouterr().out

    def test_missing_contract_returns_2(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        rc = make_factory(tmp_path, "ghost", force=False)
        assert rc == 2
        assert "introuvable" in capsys.readouterr().err

    def test_write_if_new_refuses_existing(self, tmp_path: Path) -> None:
        _write_entity(tmp_path, "article", ARTICLE)
        target = tmp_path / "mvc" / "fixtures" / "factories" / "article_factory.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# à moi\n", encoding="utf-8")
        rc = make_factory(tmp_path, "article", force=False)
        assert rc == 1
        assert target.read_text(encoding="utf-8") == "# à moi\n"

    def test_force_overwrites(self, tmp_path: Path) -> None:
        _write_entity(tmp_path, "article", ARTICLE)
        target = tmp_path / "mvc" / "fixtures" / "factories" / "article_factory.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# ancien\n", encoding="utf-8")
        rc = make_factory(tmp_path, "article", force=True)
        assert rc == 0
        assert "ArticleFactory" in target.read_text(encoding="utf-8")
