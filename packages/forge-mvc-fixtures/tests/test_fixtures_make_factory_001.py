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
    column_for_field,
    fk_targets,
    make_factory,
    provider_for_field,
    reference_expr,
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

    def test_foreign_key_scaffolds_reference(self) -> None:
        # F43 : une clé étrangère devient un self.reference(...) commenté, plus un random_int.
        expr, comment = provider_for_field({"name": "category_id", "type": "foreign_key"})
        assert expr.startswith("self.reference(")
        assert "TODO (F43)" in comment

    def test_name_heuristic_ignored_on_typed_field(self) -> None:
        # Un champ « published » booléen ne doit pas être capté par une heuristique de nom.
        expr, _ = provider_for_field({"name": "published", "type": "boolean"})
        assert "boolean" in expr


class TestColumnMapping:
    """F45 (ADR-077) : le scaffold porte les colonnes réelles de l'entité."""

    @pytest.mark.parametrize("name, ftype, expected", [
        ("title", "string", "Title"),
        ("content", "text", "Content"),
        ("published_at", "datetime", "PublishedAt"),
        ("author_email", "email", "AuthorEmail"),
        ("category_id", "foreign_key", "category_id"),
    ])
    def test_column_for_field(self, name: str, ftype: str, expected: str) -> None:
        assert column_for_field({"name": name, "type": ftype}) == expected


class TestRenderFactory:

    def test_valid_python_with_class_and_table(self) -> None:
        src = render_factory(ARTICLE)
        assert "class ArticleFactory(Factory):" in src
        assert 'table = "articles"' in src
        # F45 : colonnes réelles (PascalCase) ; une clé étrangère garde son snake.
        assert '"Title":' in src
        assert '"PublishedAt":' in src
        assert '"AuthorEmail":' in src
        # F43 : le champ foreign_key est scaffoldé en self.reference(...).
        assert '"category_id": self.reference(' in src
        # pas de fuite du nom de champ snake pour les champs ordinaires
        assert '"title":' not in src
        # le code généré doit être du Python valide
        compile(src, "<factory>", "exec")


def _write_relations(root: Path, relations: list[dict]) -> None:
    d = root / "mvc" / "entities"
    d.mkdir(parents=True, exist_ok=True)
    (d / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": relations}), encoding="utf-8"
    )


class TestForeignKeyReferences:
    """F43 (ADR-077) : références inter-fixtures via relations.json."""

    def test_reference_expr_uses_target_table(self) -> None:
        expr, comment = reference_expr("users")
        assert expr == 'self.reference("users", "cle_naturelle", "valeur")'
        assert "TODO (F43)" in comment

    def test_reference_expr_falls_back_without_table(self) -> None:
        expr, _ = reference_expr(None)
        assert '"table_cible"' in expr

    def test_fk_targets_maps_column_to_target_table(self, tmp_path: Path) -> None:
        # L'entité cible User (snake « user ») déclare sa table « users ».
        _write_entity(tmp_path, "user", {"name": "User", "table": "users", "fields": []})
        _write_relations(tmp_path, [
            {"type": "many_to_one", "from": "Eleve", "to": "User",
             "name": "compte", "foreign_key": "user_id"},
        ])
        assert fk_targets(tmp_path, "eleve") == {"user_id": "users"}

    def test_fk_targets_absent_relations_is_empty(self, tmp_path: Path) -> None:
        assert fk_targets(tmp_path, "eleve") == {}

    def test_fk_targets_default_column_from_name(self, tmp_path: Path) -> None:
        # foreign_key non déclaré : colonne par défaut <name>_id.
        _write_relations(tmp_path, [
            {"type": "many_to_one", "from": "Classe", "to": "AnneeScolaire",
             "name": "annee_scolaire"},
        ])
        assert fk_targets(tmp_path, "classe") == {"annee_scolaire_id": "annee_scolaire"}

    def test_render_uses_relations_target_table(self) -> None:
        contract = {"name": "Eleve", "table": "eleve", "fields": [
            {"name": "user_id", "type": "foreign_key"},
        ]}
        src = render_factory(contract, fk_map={"user_id": "users"})
        assert '"user_id": self.reference("users", "cle_naturelle", "valeur")' in src

    def test_integer_named_fk_detected_via_relations(self) -> None:
        # RéférenCiel : user_id typé integer, mais FK déclarée dans relations.json.
        contract = {"name": "Eleve", "table": "eleve", "fields": [
            {"name": "user_id", "type": "integer"},
        ]}
        src = render_factory(contract, fk_map={"user_id": "users"})
        # La colonne réelle (UserId, integer -> PascalCase) porte la référence.
        assert '"UserId": self.reference("users",' in src
        assert "random_int" not in src


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
