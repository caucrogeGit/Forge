from core.forms import ChoiceField, Form, StringField


class ContactForm(Form):
    nom = StringField(label="Nom", required=True, max_length=80)
    prenom = StringField(label="Prénom", required=True, max_length=80)
    email = StringField(label="Email", required=True, max_length=120)
    telephone = StringField(label="Téléphone", required=False, max_length=20)
    ville_id = ChoiceField(
        label="Ville",
        required=False,
        choices_key="ville_choices",
        coerce=int,
        empty_value=None,
    )
