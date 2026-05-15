import pytest

from core.forms import Form, RelationField, ValidationError


_VILLE_CHOICES = [("1", "Dreux"), ("2", "Chartres"), ("3", "Paris")]


def _field(**kw):
    kw.setdefault("choices", _VILLE_CHOICES)
    return RelationField(**kw)


# ---------------------------------------------------------------------------
# Import et attributs sémantiques
# ---------------------------------------------------------------------------

class TestRelationFieldAttrs:

    def test_import(self):
        from core.forms import RelationField  # noqa: F401

    def test_conserve_target(self):
        f = RelationField(target="Ville", choices=_VILLE_CHOICES)
        assert f.target == "Ville"

    def test_target_vide_par_defaut(self):
        f = RelationField(choices=_VILLE_CHOICES)
        assert f.target == ""

    def test_conserve_target_label_field(self):
        f = RelationField(target="Ville", target_label_field="nom", choices=_VILLE_CHOICES)
        assert f.target_label_field == "nom"

    def test_target_label_field_vide_par_defaut(self):
        f = RelationField(choices=_VILLE_CHOICES)
        assert f.target_label_field == ""


# ---------------------------------------------------------------------------
# Validation — valeurs présentes dans les choix
# ---------------------------------------------------------------------------

class TestRelationFieldValidation:

    def test_valeur_dans_les_choix_passe(self):
        assert _field().clean("1") == "1"

    def test_autre_valeur_dans_les_choix_passe(self):
        assert _field().clean("3") == "3"

    def test_valeur_absente_des_choix_echoue(self):
        with pytest.raises(ValidationError, match="invalide"):
            _field().clean("99")

    def test_valeur_absente_message_comprehensible(self):
        f = _field(label="Ville")
        with pytest.raises(ValidationError) as exc:
            f.clean("999")
        assert "Ville" in str(exc.value)

    def test_required_true_refuse_vide(self):
        with pytest.raises(ValidationError, match="obligatoire"):
            _field(required=True).clean("")

    def test_required_false_accepte_vide(self):
        result = _field(required=False).clean("")
        assert result is None

    def test_required_false_empty_value_none(self):
        result = _field(required=False, empty_value=None).clean("")
        assert result is None

    def test_required_false_empty_value_zero(self):
        result = _field(required=False, empty_value=0).clean("")
        assert result == 0

    def test_choix_absents_et_required_true_refuse_vide(self):
        f = RelationField(choices=[], required=True)
        with pytest.raises(ValidationError):
            f.clean("")

    def test_choix_absents_et_required_false_accepte_vide(self):
        f = RelationField(choices=[], required=False)
        assert f.clean("") is None

    def test_valeur_numerique_coercee_si_choix_sont_int(self):
        f = RelationField(choices=[(1, "Dreux"), (2, "Chartres")])
        assert f.clean("1") == 1

    def test_valeur_absente_liste_int_echoue(self):
        f = RelationField(choices=[(1, "Dreux"), (2, "Chartres")])
        with pytest.raises(ValidationError):
            f.clean("99")


# ---------------------------------------------------------------------------
# Intégration via Form + choices_key
# ---------------------------------------------------------------------------

class TestRelationFieldInForm:

    def test_choices_key_resolu_depuis_form_options(self):
        class ContactForm(Form):
            ville_id = RelationField(
                label="Ville",
                target="Ville",
                required=False,
                choices_key="ville_id_choices",
                empty_value=None,
            )

        form = ContactForm(
            {"ville_id": "2"},
            ville_id_choices=_VILLE_CHOICES,
        )
        assert form.is_valid()
        assert form.cleaned_data["ville_id"] == "2"

    def test_valeur_absente_depuis_form_options_invalide(self):
        class ContactForm(Form):
            ville_id = RelationField(
                label="Ville",
                target="Ville",
                required=True,
                choices_key="ville_id_choices",
            )

        form = ContactForm(
            {"ville_id": "999"},
            ville_id_choices=_VILLE_CHOICES,
        )
        assert not form.is_valid()
        assert "ville_id" in form.errors

    def test_vide_accepte_si_required_false(self):
        class ContactForm(Form):
            ville_id = RelationField(
                label="Ville",
                target="Ville",
                required=False,
                choices_key="ville_id_choices",
                empty_value=None,
            )

        form = ContactForm(
            {"ville_id": ""},
            ville_id_choices=_VILLE_CHOICES,
        )
        assert form.is_valid()
        assert form.cleaned_data["ville_id"] is None
