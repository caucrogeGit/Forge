"""Classe de base Factory (FIXTURES-FACTORY-001, ADR-076).

Contrat de la factory : definition() répétée ou rows(count) codé à la main,
self.faker optionnel et reproductible par seed, build() valide les lignes.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("faker")
pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures import Factory, FactoryError


class VilleFactory(Factory):
    table = "ville"

    def definition(self) -> dict[str, Any]:
        return {"nom": self.faker.city()}


class ManyVilleFactory(Factory):
    table = "ville"

    def rows(self, count: int) -> list[dict[str, Any]]:
        # L'utilisateur code sa génération : boucle + condition.
        return [{"nom": f"Ville {i}", "prefecture": i == 0} for i in range(count)]


class TestDefinitionPath:

    def test_repeats_definition_count_times(self) -> None:
        rows = VilleFactory(seed=1).build(3)
        assert len(rows) == 3
        assert all(set(r) == {"nom"} for r in rows)


class TestRowsOverride:

    def test_user_controlled_generation(self) -> None:
        rows = ManyVilleFactory().build(4)
        assert len(rows) == 4
        assert rows[0] == {"nom": "Ville 0", "prefecture": True}
        assert rows[3]["prefecture"] is False


class TestFaker:

    def test_optional_and_seeded_reproducible(self) -> None:
        a = VilleFactory(seed=42).build(5)
        b = VilleFactory(seed=42).build(5)
        assert a == b, "même seed -> mêmes données (reproductible)"

    def test_different_seed_differs(self) -> None:
        a = VilleFactory(seed=1).build(5)
        b = VilleFactory(seed=2).build(5)
        assert a != b

    def test_locale_is_configurable(self) -> None:
        class DeFactory(VilleFactory):
            locale = "de_DE"

        # Pas d'assertion sur le contenu (dépend de Faker) : on vérifie juste que
        # la locale est prise en compte sans erreur.
        assert DeFactory(seed=1).build(1)


class TestBuildValidation:

    def test_missing_table_raises(self) -> None:
        class NoTable(Factory):
            def definition(self) -> dict[str, Any]:
                return {"x": 1}

        with pytest.raises(FactoryError, match="table"):
            NoTable().build(1)

    def test_inconsistent_columns_raise(self) -> None:
        class Wobbly(Factory):
            table = "t"

            def rows(self, count: int) -> list[dict[str, Any]]:
                return [{"a": 1}, {"b": 2}]

        with pytest.raises(FactoryError, match="colonnes"):
            Wobbly().build(2)

    def test_negative_count_raises(self) -> None:
        with pytest.raises(FactoryError):
            VilleFactory().build(-1)

    def test_definition_not_overridden_raises(self) -> None:
        class Bare(Factory):
            table = "t"

        with pytest.raises(NotImplementedError):
            Bare().build(1)

    def test_zero_count_is_empty(self) -> None:
        assert VilleFactory().build(0) == []
