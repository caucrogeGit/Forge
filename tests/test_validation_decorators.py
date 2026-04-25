import pytest
from datetime import date, datetime

from core.validation import (
    ValidationError,
    max_length,
    max_value,
    min_length,
    min_value,
    not_empty,
    nullable,
    pattern,
    typed,
)


class DummyEntity:
    def __init__(self):
        self.values = {}

    @typed(str)
    def nom(self, value):
        self.values["nom"] = value

    @typed(int)
    def age(self, value):
        self.values["age"] = value

    @nullable
    @typed(str)
    def email(self, value):
        self.values["email"] = value

    @not_empty
    def code(self, value):
        self.values["code"] = value

    @min_length(3)
    def prenom(self, value):
        self.values["prenom"] = value

    @max_length(5)
    def sigle(self, value):
        self.values["sigle"] = value

    @min_value(10)
    def minimum(self, value):
        self.values["minimum"] = value

    @max_value(20)
    def maximum(self, value):
        self.values["maximum"] = value

    @pattern(r"[A-Z]{2}\d{2}")
    def reference(self, value):
        self.values["reference"] = value


def test_typed_string_ok():
    entity = DummyEntity()
    entity.nom("Alice")
    assert entity.values["nom"] == "Alice"


def test_typed_int_rejects_bool():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="age"):
        entity.age(True)


def test_typed_rejects_wrong_type():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="nom"):
        entity.nom(123)


def test_nullable_allows_none():
    entity = DummyEntity()
    entity.email(None)
    assert entity.values["email"] is None


def test_non_nullable_decorators_ignore_none():
    entity = DummyEntity()
    entity.nom(None)
    entity.code(None)
    entity.minimum(None)
    assert entity.values["nom"] is None
    assert entity.values["code"] is None
    assert entity.values["minimum"] is None


def test_not_empty_rejects_blank_string():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="code"):
        entity.code("   ")


def test_min_length_rejects_short_string():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="prenom"):
        entity.prenom("Al")


def test_max_length_rejects_long_string():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="sigle"):
        entity.sigle("ABCDEZ")


def test_min_value_rejects_too_small_number():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="minimum"):
        entity.minimum(9)


def test_max_value_rejects_too_large_number():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="maximum"):
        entity.maximum(21)


def test_pattern_rejects_invalid_value():
    entity = DummyEntity()
    with pytest.raises(ValidationError, match="reference"):
        entity.reference("ab12")


def test_typed_date_accepts_python_date():
    @typed(date)
    def valeur(self, value):
        return value

    result = valeur(None, date(2026, 4, 23))
    assert result == date(2026, 4, 23)


def test_typed_datetime_accepts_python_datetime():
    @typed(datetime)
    def valeur(self, value):
        return value

    result = valeur(None, datetime(2026, 4, 23, 10, 15, 30))
    assert result == datetime(2026, 4, 23, 10, 15, 30)
