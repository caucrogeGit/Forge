import pytest

from core.forms import EmailField, PhoneField, UrlField, ValidationError


# ---------------------------------------------------------------------------
# EmailField
# ---------------------------------------------------------------------------

class TestEmailField:
    def _field(self, **kw):
        return EmailField(**kw)

    # --- valeurs acceptées ---

    @pytest.mark.parametrize("value", [
        "user@example.com",
        "user.name+tag@sub.domain.org",
        "first.last@company.fr",
        "x@y.io",
        "user_123@mail-server.net",
        "a@b.museum",
    ])
    def test_valid(self, value):
        assert self._field().clean(value) == value

    # --- strip ---

    def test_strips_whitespace(self):
        assert self._field().clean("  user@example.com  ") == "user@example.com"

    # --- valeurs rejetées ---

    @pytest.mark.parametrize("value", [
        "notanemail",
        "@nodomain.com",
        "user@",
        "user@domain",
        "user @example.com",
        "user@ example.com",
        "",
    ])
    def test_invalid_format(self, value):
        field = self._field(required=False)
        if value == "":
            assert field.clean(value) is None
        else:
            with pytest.raises(ValidationError, match="email"):
                field.clean(value)

    def test_required_empty_raises(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            self._field().clean("")

    def test_optional_empty_returns_none(self):
        assert self._field(required=False).clean("") is None

    def test_optional_empty_returns_default(self):
        assert self._field(required=False, default="fallback@x.com").clean("") == "fallback@x.com"

    # --- max_length par défaut ---

    def test_default_max_length_is_254(self):
        field = self._field()
        assert field.max_length == 254

    def test_max_length_exceeded(self):
        long_local = "a" * 250
        value = f"{long_local}@b.com"
        with pytest.raises(ValidationError, match="depasser"):
            self._field().clean(value)

    def test_custom_max_length(self):
        field = EmailField(max_length=20)
        assert field.max_length == 20

    # --- label dans le message ---

    def test_error_contains_label(self):
        field = EmailField(label="Courriel")
        with pytest.raises(ValidationError) as exc:
            field.clean("invalide")
        assert "Courriel" in str(exc.value)


# ---------------------------------------------------------------------------
# PhoneField
# ---------------------------------------------------------------------------

class TestPhoneField:
    def _field(self, **kw):
        return PhoneField(**kw)

    # --- valeurs acceptées ---

    @pytest.mark.parametrize("value", [
        "0612345678",
        "06 12 34 56 78",
        "06.12.34.56.78",
        "06-12-34-56-78",
        "+33612345678",
        "+33 6 12 34 56 78",
        "+33.6.12.34.56.78",
        "0123456789",
        "0988776655",
    ])
    def test_valid(self, value):
        assert self._field().clean(value) == value

    # --- valeurs rejetées ---

    @pytest.mark.parametrize("value", [
        "123",
        "06123",
        "+336",
        "06 12 34 56",
        "abcdefghij",
        "06 1 2 3 4 5 6 7 8",
    ])
    def test_invalid_format(self, value):
        with pytest.raises(ValidationError, match="telephone"):
            self._field().clean(value)

    def test_required_empty_raises(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            self._field().clean("")

    def test_optional_empty_returns_none(self):
        assert self._field(required=False).clean("") is None

    def test_optional_invalid_raises(self):
        with pytest.raises(ValidationError, match="telephone"):
            self._field(required=False).clean("123")

    # --- strip ---

    def test_strips_whitespace(self):
        assert self._field().clean("  0612345678  ") == "0612345678"

    # --- label dans le message ---

    def test_error_contains_label(self):
        field = PhoneField(label="Téléphone")
        with pytest.raises(ValidationError) as exc:
            field.clean("invalide")
        assert "Téléphone" in str(exc.value)


# ---------------------------------------------------------------------------
# UrlField
# ---------------------------------------------------------------------------

class TestUrlField:
    def _field(self, **kw):
        return UrlField(**kw)

    # --- valeurs acceptées ---

    @pytest.mark.parametrize("value", [
        "http://example.com",
        "https://example.com",
        "https://sub.domain.org/path",
        "https://example.com/page?q=1&lang=fr",
        "http://localhost.local",
        "HTTPS://EXAMPLE.COM",
        "https://shop.example.fr/produit/42",
    ])
    def test_valid(self, value):
        assert self._field().clean(value) == value

    # --- valeurs rejetées ---

    @pytest.mark.parametrize("value", [
        "ftp://example.com",
        "just-a-string",
        "example.com",
        "//example.com",
        "http://",
        "http://nodot",
    ])
    def test_invalid_format(self, value):
        with pytest.raises(ValidationError, match="URL"):
            self._field().clean(value)

    def test_required_empty_raises(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            self._field().clean("")

    def test_optional_empty_returns_none(self):
        assert self._field(required=False).clean("") is None

    def test_optional_invalid_raises(self):
        with pytest.raises(ValidationError, match="URL"):
            self._field(required=False).clean("not-a-url")

    # --- max_length par défaut ---

    def test_default_max_length_is_2048(self):
        field = self._field()
        assert field.max_length == 2048

    def test_max_length_exceeded(self):
        value = "https://example.com/" + "a" * 2048
        with pytest.raises(ValidationError, match="depasser"):
            self._field().clean(value)

    def test_custom_max_length(self):
        field = UrlField(max_length=100)
        assert field.max_length == 100

    # --- strip ---

    def test_strips_whitespace(self):
        assert self._field().clean("  https://example.com  ") == "https://example.com"

    # --- label dans le message ---

    def test_error_contains_label(self):
        field = UrlField(label="Site web")
        with pytest.raises(ValidationError) as exc:
            field.clean("invalide")
        assert "Site web" in str(exc.value)

    # --- case insensitive ---

    def test_https_uppercase_accepted(self):
        assert self._field().clean("HTTPS://EXAMPLE.COM") == "HTTPS://EXAMPLE.COM"
