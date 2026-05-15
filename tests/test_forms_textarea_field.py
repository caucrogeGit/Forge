import pytest

from core.forms import TextAreaField, ValidationError


def _field(name="description", **kw):
    f = TextAreaField(**kw)
    f.name = name
    return f


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestTextAreaFieldValidation:

    def test_valid_simple_text(self):
        assert _field().clean("Bonjour le monde") == "Bonjour le monde"

    def test_valid_multiline(self):
        text = "Ligne 1\nLigne 2\nLigne 3"
        assert _field().clean(text) == text

    def test_valid_multiline_with_blank_lines(self):
        text = "Paragraphe 1\n\nParagraphe 2"
        assert _field().clean(text) == text

    def test_strips_leading_trailing_whitespace(self):
        assert _field().clean("  texte  ") == "texte"

    def test_required_empty_raises(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field().clean("")

    def test_optional_empty_returns_none(self):
        assert _field(required=False).clean("") is None

    def test_optional_empty_returns_default(self):
        assert _field(required=False, default="N/A").clean("") == "N/A"

    def test_min_length_respected(self):
        with pytest.raises(ValidationError, match="au moins"):
            _field(min_length=10).clean("court")

    def test_min_length_exact_passes(self):
        assert _field(min_length=5).clean("exact") == "exact"

    def test_max_length_respected(self):
        with pytest.raises(ValidationError, match="depasser"):
            _field(max_length=5).clean("trop long ici")

    def test_max_length_exact_passes(self):
        assert _field(max_length=5).clean("12345") == "12345"

    def test_no_length_constraints_passes_long_text(self):
        text = "a" * 10_000
        assert _field().clean(text) == text

    def test_strip_false_preserves_whitespace(self):
        text = "  texte avec espaces  "
        assert _field(strip=False).clean(text) == text


# ---------------------------------------------------------------------------
# Rendu HTML
# ---------------------------------------------------------------------------

class TestTextAreaFieldRender:

    def test_render_contains_textarea_tag(self):
        assert "<textarea " in _field().render()

    def test_render_closes_properly(self):
        rendered = _field().render()
        assert rendered.endswith("</textarea>")

    def test_render_contains_name(self):
        assert 'name="description"' in _field("description").render()

    def test_render_value_between_tags(self):
        rendered = _field().render("mon texte")
        assert ">mon texte<" in rendered

    def test_render_empty_value_by_default(self):
        rendered = _field().render()
        assert "></textarea>" in rendered

    def test_render_required_when_required(self):
        assert "required" in _field(required=True).render()

    def test_render_no_required_when_not_required(self):
        rendered = _field(required=False).render()
        assert "required" not in rendered

    def test_render_minlength_when_set(self):
        assert 'minlength="10"' in _field(min_length=10).render()

    def test_render_no_minlength_when_not_set(self):
        assert "minlength" not in _field().render()

    def test_render_maxlength_when_set(self):
        assert 'maxlength="500"' in _field(max_length=500).render()

    def test_render_no_maxlength_when_not_set(self):
        assert "maxlength" not in _field().render()

    def test_render_rows_when_set(self):
        assert 'rows="4"' in _field(rows=4).render()

    def test_render_no_rows_by_default(self):
        assert "rows" not in _field().render()

    # --- sécurité XSS ---

    def test_render_escapes_lt_gt(self):
        rendered = _field().render("<script>alert('xss')</script>")
        assert "<script>" not in rendered
        assert "&lt;script&gt;" in rendered

    def test_render_escapes_ampersand(self):
        rendered = _field().render("a & b")
        assert "&amp;" in rendered

    def test_render_escapes_quotes(self):
        rendered = _field().render('say "hello"')
        assert "&quot;" in rendered

    def test_render_no_executable_html(self):
        rendered = _field().render('<img src=x onerror="alert(1)">')
        assert "<img" not in rendered
        assert "&lt;img" in rendered

    # --- attributs combinés ---

    def test_render_full_example(self):
        f = _field("description", required=True, min_length=10, max_length=500)
        rendered = f.render("texte")
        assert 'name="description"' in rendered
        assert "required" in rendered
        assert 'minlength="10"' in rendered
        assert 'maxlength="500"' in rendered
        assert ">texte<" in rendered
        assert "<textarea " in rendered
        assert rendered.endswith("</textarea>")
