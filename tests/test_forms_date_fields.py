import datetime

import pytest

from core.forms import DateField, DateTimeField, ValidationError


# ---------------------------------------------------------------------------
# DateField
# ---------------------------------------------------------------------------

class TestDateField:
    def _field(self, **kw):
        return DateField(**kw)

    # --- valeurs valides ---

    @pytest.mark.parametrize("value,expected", [
        ("2026-05-01", datetime.date(2026, 5, 1)),
        ("2024-02-29", datetime.date(2024, 2, 29)),   # bissextile
        ("2000-01-01", datetime.date(2000, 1, 1)),
        ("1999-12-31", datetime.date(1999, 12, 31)),
    ])
    def test_valid_returns_date(self, value, expected):
        assert self._field().clean(value) == expected

    def test_returns_date_type(self):
        result = self._field().clean("2026-05-01")
        assert isinstance(result, datetime.date)
        assert not isinstance(result, datetime.datetime)

    # --- strip ---

    def test_strips_whitespace(self):
        assert self._field().clean("  2026-05-01  ") == datetime.date(2026, 5, 1)

    # --- format strict YYYY-MM-DD ---

    @pytest.mark.parametrize("value", [
        "01/05/2026",      # format français
        "2026/05/01",      # slashes
        "2026-5-1",        # non zero-padded
        "2026-05-1",       # jour non padded
        "2026-5-01",       # mois non padded
        "20260501",        # sans séparateurs
        "2026-05",         # incomplet
        "texte",
        "2026-05-01T00:00",  # datetime dans un DateField
    ])
    def test_invalid_format(self, value):
        with pytest.raises(ValidationError, match="YYYY-MM-DD"):
            self._field().clean(value)

    # --- dates impossibles ---

    @pytest.mark.parametrize("value", [
        "2026-13-01",   # mois 13
        "2026-00-01",   # mois 00
        "2026-02-30",   # 30 février
        "2025-02-29",   # 29 février année non bissextile
        "2026-04-31",   # avril n'a pas 31 jours
        "2026-01-00",   # jour 00
    ])
    def test_impossible_date(self, value):
        with pytest.raises(ValidationError, match="YYYY-MM-DD"):
            self._field().clean(value)

    # --- required / optional ---

    def test_required_empty_raises(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            self._field().clean("")

    def test_optional_empty_returns_none(self):
        assert self._field(required=False).clean("") is None

    def test_optional_empty_returns_default(self):
        default = datetime.date(2000, 1, 1)
        assert self._field(required=False, default=default).clean("") == default

    def test_optional_invalid_still_raises(self):
        with pytest.raises(ValidationError):
            self._field(required=False).clean("pas-une-date")

    # --- label dans le message ---

    def test_error_contains_label(self):
        field = DateField(label="Date de naissance")
        with pytest.raises(ValidationError) as exc:
            field.clean("invalide")
        assert "Date de naissance" in str(exc.value)


# ---------------------------------------------------------------------------
# DateTimeField
# ---------------------------------------------------------------------------

class TestDateTimeField:
    def _field(self, **kw):
        return DateTimeField(**kw)

    # --- valeurs valides ---

    @pytest.mark.parametrize("value,expected", [
        ("2026-05-01T14:30", datetime.datetime(2026, 5, 1, 14, 30)),
        ("2026-05-01T14:30:45", datetime.datetime(2026, 5, 1, 14, 30, 45)),
        ("2024-02-29T00:00", datetime.datetime(2024, 2, 29, 0, 0)),   # bissextile
        ("2026-12-31T23:59:59", datetime.datetime(2026, 12, 31, 23, 59, 59)),
    ])
    def test_valid_returns_datetime(self, value, expected):
        assert self._field().clean(value) == expected

    def test_returns_datetime_type(self):
        result = self._field().clean("2026-05-01T14:30")
        assert isinstance(result, datetime.datetime)

    # --- strip ---

    def test_strips_whitespace(self):
        assert self._field().clean("  2026-05-01T14:30  ") == datetime.datetime(2026, 5, 1, 14, 30)

    # --- format strict YYYY-MM-DDTHH:MM ---

    @pytest.mark.parametrize("value", [
        "2026-05-01 14:30",       # espace au lieu de T
        "01/05/2026 14:30",       # format français
        "2026/05/01T14:30",       # slashes
        "2026-05-01T14",          # heure seule sans minutes
        "2026-05-01",             # date seule dans DateTimeField
        "texte",
        "2026-5-1T14:30",         # non zero-padded
        "2026-05-01T4:30",        # heure non paddée
    ])
    def test_invalid_format(self, value):
        with pytest.raises(ValidationError, match="YYYY-MM-DDTHH:MM"):
            self._field().clean(value)

    # --- dates/heures impossibles ---

    @pytest.mark.parametrize("value", [
        "2026-13-01T14:30",    # mois 13
        "2026-02-30T14:30",    # 30 février
        "2025-02-29T14:30",    # 29 février non bissextile
        "2026-05-01T25:00",    # heure 25
        "2026-05-01T14:60",    # minutes 60
        "2026-05-01T14:30:60", # secondes 60
    ])
    def test_impossible_datetime(self, value):
        with pytest.raises(ValidationError, match="YYYY-MM-DDTHH:MM"):
            self._field().clean(value)

    # --- required / optional ---

    def test_required_empty_raises(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            self._field().clean("")

    def test_optional_empty_returns_none(self):
        assert self._field(required=False).clean("") is None

    def test_optional_empty_returns_default(self):
        default = datetime.datetime(2000, 1, 1, 0, 0)
        assert self._field(required=False, default=default).clean("") == default

    def test_optional_invalid_still_raises(self):
        with pytest.raises(ValidationError):
            self._field(required=False).clean("pas-une-date")

    # --- label dans le message ---

    def test_error_contains_label(self):
        field = DateTimeField(label="Date de début")
        with pytest.raises(ValidationError) as exc:
            field.clean("invalide")
        assert "Date de début" in str(exc.value)
