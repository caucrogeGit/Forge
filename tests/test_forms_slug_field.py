import pytest

from core.forms import SlugField, ValidationError


def _field(**kw):
    return SlugField(**kw)


# ---------------------------------------------------------------------------
# Valeurs valides
# ---------------------------------------------------------------------------

class TestSlugFieldValid:

    @pytest.mark.parametrize("value", [
        "gite-du-centre",
        "commune-dreux",
        "hebergement-2026",
        "maison-bleue-12",
        "a",
        "abc",
        "abc123",
        "123",
        "a-b-c",
        "slug-avec-plusieurs-mots",
    ])
    def test_valide(self, value):
        assert _field().clean(value) == value

    def test_strips_whitespace(self):
        assert _field().clean("  gite-du-centre  ") == "gite-du-centre"

    def test_required_empty_returns_default(self):
        f = _field(required=False)
        assert f.clean("") is None

    def test_required_false_valeur_valide_passe(self):
        assert _field(required=False).clean("commune-dreux") == "commune-dreux"


# ---------------------------------------------------------------------------
# Valeurs invalides — format
# ---------------------------------------------------------------------------

class TestSlugFieldInvalidFormat:

    @pytest.mark.parametrize("value", [
        "Gite-Du-Centre",       # majuscules
        "SLUG",                 # majuscules
        "gîte-du-centre",       # accent
        "café",                 # accent
        "gite du centre",       # espace
        "gite_du_centre",       # underscore
        "/gite-du-centre",      # slash
        "gite.du.centre",       # point
        "-gite-du-centre",      # tiret initial
        "gite-du-centre-",      # tiret final
        "gite--du-centre",      # double tiret
        "javascript:alert-1",   # colon
        "gite@centre",          # arobase
        "gite#centre",          # dièse
    ])
    def test_invalide(self, value):
        with pytest.raises(ValidationError, match="minuscules"):
            _field().clean(value)

    def test_required_empty_raises(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field().clean("")

    def test_optional_invalide_toujours_refuse(self):
        with pytest.raises(ValidationError):
            _field(required=False).clean("Invalide-Slug")


# ---------------------------------------------------------------------------
# Longueur
# ---------------------------------------------------------------------------

class TestSlugFieldLength:

    def test_max_length_par_defaut_est_120(self):
        assert _field().max_length == 120

    def test_max_length_depasse_refuse(self):
        value = "a" * 121
        with pytest.raises(ValidationError, match="depasser"):
            _field().clean(value)

    def test_max_length_exact_passe(self):
        value = "a" * 120
        assert _field().clean(value) == value

    def test_max_length_personnalise_respecte(self):
        with pytest.raises(ValidationError, match="depasser"):
            _field(max_length=10).clean("slug-trop-long-ici")

    def test_max_length_personnalise_passe(self):
        assert _field(max_length=10).clean("court") == "court"

    def test_min_length_respecte(self):
        with pytest.raises(ValidationError, match="au moins"):
            _field(min_length=5).clean("ab")

    def test_min_length_exact_passe(self):
        assert _field(min_length=3).clean("abc") == "abc"


# ---------------------------------------------------------------------------
# Label dans les messages
# ---------------------------------------------------------------------------

class TestSlugFieldLabel:

    def test_label_dans_message_format(self):
        field = SlugField(label="Identifiant URL")
        with pytest.raises(ValidationError) as exc:
            field.clean("Invalide!")
        assert "Identifiant URL" in str(exc.value)

    def test_label_dans_message_obligatoire(self):
        field = SlugField(label="Slug")
        with pytest.raises(ValidationError) as exc:
            field.clean("")
        assert "Slug" in str(exc.value)
