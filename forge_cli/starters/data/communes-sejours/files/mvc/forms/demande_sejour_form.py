from core.forms import DateField, EmailField, Form, IntegerField, StringField, TextAreaField
from core.i18n import trans


class DemandeSejourForm(Form):
    nom = StringField(label=trans("starter.cs.form.nom"), required=True, max_length=100)
    email = EmailField(label=trans("starter.cs.form.email"), required=True)
    telephone = StringField(label=trans("starter.cs.form.phone"), required=False, max_length=30)
    date_arrivee = DateField(label=trans("starter.cs.form.arrival"), required=True)
    date_depart = DateField(label=trans("starter.cs.form.departure"), required=True)
    nombre_personnes = IntegerField(label=trans("starter.cs.form.people"), required=True, min_value=1, max_value=99)
    message = TextAreaField(label=trans("starter.cs.form.message"), required=False, max_length=2000)
