# Les formulaires dans Forge

Ce document décrit la classe `Form` et la déclaration de champs.

Le fichier de code correspondant est `core/forms/form.py`.

## 1. À quoi sert ce module ?

Un formulaire lit les données d'une requête, les convertit et les valide avant que l'application ne les utilise.
`Form` rassemble des [champs](fields.md) déclarés sur la classe et expose les données nettoyées ou les erreurs.

## 2. Déclarer un formulaire

```python
from core.forms.form import Form
from core.forms.fields import StringField, IntegerField

class ArticleForm(Form):
    title = StringField(required=True, max_length=120)
    category_id = IntegerField(required=True)

form = ArticleForm(request.body)
if form.is_valid():
    data = form.cleaned_data
else:
    errors = form.errors
```

| Élément | Rôle |
|---|---|
| `Form` | formulaire : valide les champs déclarés, expose `cleaned_data` / `errors` |
| `FormMeta` | métaclasse qui collecte les `Field` déclarés sur la classe |

## 3. Le contrat

La validation est **explicite** : un formulaire invalide n'écrit rien ; on lit `errors` pour afficher les messages par champ.

## 4. Contextes d'utilisation

- **Contrôleur** : valider un POST avant l'insert.
- **CRUD généré** : les formulaires d'entité sont des `Form`.

## 5. Voir aussi

- [Les champs](fields.md) : les types de champ disponibles.
- [L'erreur de validation](exceptions.md) : `ValidationError`.
