from decimal import Decimal

from core.forms import (
    BooleanField,
    ChoiceField,
    DecimalField,
    Form,
    IntegerField,
    RelatedIdsField,
    StringField,
    ValidationError,
)
from tests.fake_request import FakeRequest


class ContactForm(Form):
    nom = StringField(label="Nom", required=True, max_length=40)
    age = IntegerField(label="Age", required=False, min_value=0)
    actif = BooleanField(label="Actif")


def test_form_valide_remplit_cleaned_data():
    form = ContactForm({"nom": [" Alice "], "age": ["30"], "actif": ["on"]})

    assert form.is_valid() is True
    assert form.cleaned_data == {"nom": "Alice", "age": 30, "actif": True}
    assert form.errors == {}


def test_form_retourne_erreurs_affichables():
    form = ContactForm({"nom": [""], "age": ["-2"]})

    assert form.is_valid() is False
    assert "nom" in form.errors
    assert "age" in form.errors
    assert form.cleaned_data["actif"] is False


def test_form_from_request_lit_le_body_http():
    request = FakeRequest("POST", "/contacts", body={"nom": "Ada", "age": "41"})

    form = ContactForm.from_request(request)

    assert form.is_valid() is True
    assert form.cleaned_data["nom"] == "Ada"
    assert form.cleaned_data["age"] == 41


class PrixForm(Form):
    prix = DecimalField(label="Prix", min_value="0")


def test_decimal_field_convertit_virgule_francaise():
    form = PrixForm({"prix": ["12,50"]})

    assert form.is_valid() is True
    assert form.cleaned_data["prix"] == Decimal("12.50")


class PasswordForm(Form):
    password = StringField(label="Mot de passe", min_length=8)
    confirmation = StringField(label="Confirmation")

    def clean(self):
        if self.cleaned_data["password"] != self.cleaned_data["confirmation"]:
            raise ValidationError("Les mots de passe ne correspondent pas.")


def test_form_clean_ajoute_erreur_globale():
    form = PasswordForm({"password": ["secret123"], "confirmation": ["autre123"]})

    assert form.is_valid() is False
    assert form.non_field_errors == ["Les mots de passe ne correspondent pas."]


def test_form_context_est_pret_pour_template():
    form = ContactForm({"nom": ["Bob"]})
    form.is_valid()

    assert form.context["data"]["nom"] == "Bob"
    assert form.context["cleaned_data"]["nom"] == "Bob"
    assert form.context["errors"] == {}


def test_form_helpers_value_error_has_error():
    form = ContactForm({"nom": [""], "age": ["-1"]})
    form.is_valid()

    assert form.value("nom") == ""
    assert form.has_error("nom") is True
    assert form.error("nom") == "Le champ Nom est obligatoire."
    assert form.error("inconnu") == ""


class VilleForm(Form):
    ville_id = ChoiceField(label="Ville", required=True, choices_key="allowed_ville_ids")


def test_choice_field_convertit_et_valide_choix_autorise():
    form = VilleForm({"ville_id": ["3"]}, allowed_ville_ids={1, 3, 5})

    assert form.is_valid() is True
    assert form.cleaned_data["ville_id"] == 3


def test_choice_field_refuse_choix_absent():
    form = VilleForm({"ville_id": ["9"]}, allowed_ville_ids={1, 3, 5})

    assert form.is_valid() is False
    assert form.error("ville_id") == "Le champ Ville contient un choix invalide."


class ContactPivotForm(Form):
    nom = StringField(label="Nom", required=True)
    groupe_ids = RelatedIdsField(
        label="Groupes",
        required=False,
        allowed_ids_key="allowed_group_ids",
    )


def test_related_ids_field_convertit_dedoublonne_et_valide():
    form = ContactPivotForm(
        {"nom": ["Durand"], "groupe_ids": ["1", "3", "1", "5"]},
        allowed_group_ids={1, 3, 5, 8},
    )

    assert form.is_valid() is True
    assert form.cleaned_data == {"nom": "Durand", "groupe_ids": [1, 3, 5]}
    assert form.context["data"]["groupe_ids"] == ["1", "3", "1", "5"]


def test_related_ids_field_refuse_identifiant_non_autorise():
    form = ContactPivotForm(
        {"nom": ["Durand"], "groupe_ids": ["1", "9"]},
        allowed_group_ids={1, 3, 5},
    )

    assert form.is_valid() is False
    assert "groupe_ids" in form.errors


def test_related_ids_field_refuse_valeur_non_entiere():
    form = ContactPivotForm(
        {"nom": ["Durand"], "groupe_ids": ["abc"]},
        allowed_group_ids={1, 3, 5},
    )

    assert form.is_valid() is False
    assert form.field_errors("groupe_ids") == ["Le champ Groupes doit contenir des entiers."]


def test_related_ids_field_sans_selection_retourne_liste_vide():
    form = ContactPivotForm({"nom": ["Durand"]}, allowed_group_ids={1, 3, 5})

    assert form.is_valid() is True
    assert form.cleaned_data["groupe_ids"] == []


def test_related_ids_field_exige_liste_autorisee_si_cle_configuree():
    form = ContactPivotForm({"nom": ["Durand"], "groupe_ids": ["1"]})

    assert form.is_valid() is False
    assert "La liste autorisee" in form.field_errors("groupe_ids")[0]


class AutoAllowedIdsForm(Form):
    group_ids = RelatedIdsField(required=False)


def test_related_ids_field_lit_option_autorisee_par_convention():
    form = AutoAllowedIdsForm({"group_ids": ["2"]}, allowed_group_ids={2, 4})

    assert form.is_valid() is True
    assert form.cleaned_data["group_ids"] == [2]


def test_from_request_transmet_options_de_validation():
    request = FakeRequest("POST", "/contacts", body={"nom": "Ada", "groupe_ids": "3"})

    form = ContactPivotForm.from_request(request, allowed_group_ids={3})

    assert form.is_valid() is True
    assert form.cleaned_data["groupe_ids"] == [3]
