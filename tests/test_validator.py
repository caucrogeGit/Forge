import pytest
from core.mvc.model.validator import Validator


class TestValidator:
    def test_valide_sans_erreur(self):
        v = Validator()
        assert v.is_valid()
        assert v.errors() == []

    def test_required_champ_vide(self):
        v = Validator()
        v.required("", "Nom")
        assert not v.is_valid()
        assert len(v.errors()) == 1

    def test_required_champ_espace(self):
        v = Validator()
        v.required("   ", "Nom")
        assert not v.is_valid()

    def test_required_champ_none(self):
        v = Validator()
        v.required(None, "Nom")
        assert not v.is_valid()

    def test_required_champ_rempli(self):
        v = Validator()
        v.required("Alice", "Nom")
        assert v.is_valid()

    def test_max_length_depasse(self):
        v = Validator()
        v.max_length("abcdef", 5, "Code")
        assert not v.is_valid()

    def test_max_length_exact(self):
        v = Validator()
        v.max_length("abcde", 5, "Code")
        assert v.is_valid()

    def test_max_length_vide_ignore(self):
        v = Validator()
        v.max_length("", 5, "Code")
        assert v.is_valid()

    def test_add_error_manuel(self):
        v = Validator()
        v.add_error("Doublon détecté.")
        assert not v.is_valid()
        assert "Doublon détecté." in v.errors()

    def test_errors_retourne_copie(self):
        v = Validator()
        v.add_error("x")
        copy = v.errors()
        copy.clear()
        assert len(v.errors()) == 1

    def test_chaining(self):
        v = Validator()
        v.required("", "A").max_length("trop_long", 3, "B")
        assert len(v.errors()) == 2
