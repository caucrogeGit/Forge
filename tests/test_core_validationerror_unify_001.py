"""Tests — CORE-VALIDATIONERROR-UNIFY-001 : collision de noms ValidationError levée.

Deux classes publiques `ValidationError` coexistaient, aux contrats opposés :
`core.forms.ValidationError(message)` (erreur de formulaire) et
`core.validation.ValidationError(property_name, message)` (validation d'entité).
La seconde est renommée `PropertyValidationError` (principe 11). Ce garde
verrouille le renommage et l'absence de retour de la collision.
"""
from __future__ import annotations

import pytest


class TestValidationRenamed:
    def test_property_validation_error_expose(self):
        from core.validation import PropertyValidationError

        err = PropertyValidationError("age", "doit être positif")
        assert err.property_name == "age"
        assert err.message == "doit être positif"
        assert isinstance(err, ValueError)

    def test_ancien_nom_absent_de_core_validation(self):
        import core.validation as validation

        assert not hasattr(validation, "ValidationError"), (
            "core.validation ne doit plus exporter ValidationError "
            "(renommé PropertyValidationError, CORE-VALIDATIONERROR-UNIFY-001)."
        )
        assert "ValidationError" not in validation.__all__


class TestFormsUnchanged:
    def test_forms_validation_error_intacte(self):
        from core.forms import ValidationError

        # Contrat message-based inchangé (l'autre classe).
        err = ValidationError(["champ requis", "trop long"])
        assert err.messages == ["champ requis", "trop long"]


class TestGeneratorEmitsNewName:
    def test_make_entity_genere_property_validation_error(self, tmp_path):
        pytest.importorskip("forge_mvc_entities")
        from forge_mvc_entities.make_entity import build_entity_base

        definition = {
            "entity": "Client",
            "table": "clients",
            "fields": [
                {"name": "id", "column": "id", "python_type": "int", "sql_type": "INT",
                 "nullable": False, "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "nom", "python_type": "str", "sql_type": "VARCHAR(80)",
                 "nullable": False, "primary_key": False, "auto_increment": False},
            ],
        }
        source = build_entity_base(definition)
        assert "PropertyValidationError" in source
        assert "import ValidationError" not in source
