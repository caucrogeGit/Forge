"""Tests — ENTITIES-PUBLIC-NAMING-API-001 : to_snake / pk_field en API publique.

Les générateurs de pages publiques du cœur (cli/public/*) atteignaient les
symboles privés ``forge_mvc_entities.make_crud._to_snake`` / ``_pk_field``
(sous ``# pyright: reportPrivateUsage=false``). Ces helpers sont désormais
exposés à la racine du paquet — ``from forge_mvc_entities import to_snake,
pk_field`` — comme ``column_for_field`` (ADR-077). Le CLI ne re.pointe plus
aucun symbole privé de ``make_crud``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_entities")

import forge_mvc_entities as entities


class TestPublicApi:
    def test_to_snake_et_pk_field_exportes(self):
        assert "to_snake" in entities.__all__
        assert "pk_field" in entities.__all__
        assert callable(entities.to_snake)
        assert callable(entities.pk_field)

    @pytest.mark.parametrize("nom,attendu", [
        ("Contact", "contact"),
        ("MaBelleEntite", "ma_belle_entite"),
        ("Ligne-Commande", "ligne_commande"),
    ])
    def test_to_snake(self, nom: str, attendu: str):
        assert entities.to_snake(nom) == attendu

    def test_pk_field_retourne_la_cle_primaire(self):
        definition = {
            "entity": "Contact",
            "fields": [
                {"name": "id", "primary_key": True},
                {"name": "email", "primary_key": False},
            ],
        }
        assert entities.pk_field(definition)["name"] == "id"

    def test_pk_field_leve_sans_cle_primaire(self):
        with pytest.raises(ValueError):
            entities.pk_field({"entity": "X", "fields": [{"name": "a"}]})


class TestCliNoLongerReachesPrivate:
    def test_public_generators_importent_lapi_publique(self):
        root = Path(entities.__file__).resolve().parents[3]
        for name in ("public_list.py", "public_form.py"):
            src = (root / "cli" / "public" / name).read_text(encoding="utf-8")
            assert "make_crud import _to_snake" not in src, name
            assert "make_crud import _pk_field" not in src, name
            assert "from forge_mvc_entities import" in src, name
