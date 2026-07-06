# La validation

**Objectif** : valider l'envoi côté contrôleur, réafficher le formulaire avec les erreurs, et confirmer le succès par un message flash.

**Ce que vous allez apprendre :** brancher la validation serveur (réponse 422) sur les composants visuels : état d'erreur des champs, résumé `form_errors`, message `flash_messages`.

## Valider dans le contrôleur

Faites valider `store` ; en cas d'erreur, il réaffiche `form.html` avec les erreurs et les valeurs saisies (statut 422) ; sinon il redirige avec un flash :

```python
    @staticmethod
    def store(request: Request) -> Response:
        nom = request.form("nom", default="").strip()
        email = request.form("email", default="").strip()

        errors = []
        if not nom:
            errors.append("Le nom est obligatoire.")
        if "@" not in email:
            errors.append("Le courriel est invalide.")

        if errors:
            return BaseController.render(
                "showcase/form.html",
                status=422,
                request=request,
                context={"errors": errors, "values": {"nom": nom, "email": email}},
            )

        _CONTACTS.append({"nom": nom, "email": email, "academie": "Paris", "statut": "actif"})
        return BaseController.redirect("/showcase", request=request, flash="Contact ajouté.")
```

## Afficher les erreurs dans le formulaire

Dans `showcase/form.html`, ajoutez le résumé en tête et l'erreur sur le champ :

```jinja
{% from "components/forms.html" import field, form_errors, submit %}

<form method="post" action="/showcase/store">
  {% include "partials/csrf.html" %}

  {{ form_errors(errors) }}

  {{ field("nom", label="Nom", value=values.get("nom", ""),
       error="Le nom est obligatoire." if errors and not values.get("nom") else "") }}
  {{ field("email", label="Courriel", type="email", value=values.get("email", "")) }}

  {{ submit("Enregistrer") }}
</form>
```

`form_errors(errors)` n'affiche rien si la liste est vide.
`field(..., error=...)` passe la bordure en rouge et affiche le message sous le champ.

## Le message de succès

Le préambule lit déjà le flash dans `index` (`get_flash`).
Affichez-le en haut de `showcase/index.html` :

```jinja
{% from "components/ui.html" import flash_messages %}

{{ flash_messages(flash) }}
```

Après un ajout réussi, `store` redirige vers `/showcase` avec le flash « Contact ajouté.
», et `flash_messages` le rend une seule fois.

??? note "À retenir"
    - La validation vit dans le contrôleur ; les composants n'affichent que le résultat.
    - `form_errors(errors)` pour le résumé, `field(..., error=...)` au champ.
    - `flash_messages(flash)` pour le succès, via le motif POST-Redirect-GET.

[Voir le bilan du niveau](bilan.md)
