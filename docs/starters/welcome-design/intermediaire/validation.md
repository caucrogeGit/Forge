# La validation

**Objectif** : afficher proprement les erreurs de saisie, au champ et en
résumé.

**Ce que vous allez apprendre :** l'état d'erreur des champs (`error=...`), le
résumé `form_errors`, et le message de succès via `flash_messages`. C'est le
pendant visuel de la validation serveur de Forge (réponses 422).

## Erreur sur un champ

Passez `error` à un champ : il prend la bordure rouge et affiche le message
sous le champ.

```jinja
{{ field("email", label="Courriel", type="email",
     value="pas-un-email", error="Adresse électronique invalide.") }}
```

## Résumé en tête de formulaire

`form_errors` liste les erreurs en haut du formulaire. Le contrôleur passe la
liste des messages ; ici, une liste d'exemple :

```jinja
{% from "components/forms.html" import form_errors %}

{{ form_errors(["Le nom est obligatoire.", "Le courriel est invalide."]) }}
```

Quand la liste est vide, la macro n'affiche rien.

## Message de succès après envoi

Après un enregistrement réussi, on redirige avec un message flash. La macro
`flash_messages` le rend (placez-la en haut du contenu) :

```jinja
{% from "components/ui.html" import flash_messages %}

{{ flash_messages(flash) }}
```

Côté contrôleur, le flash se pose avec `redirect_with_flash` (voir
[Messages flash](../../welcome-forge/intermediaire/flash-messages.md) dans le
parcours Welcome Forge).

??? note "À retenir"
    - `field(..., error="message")` : bordure rouge et message au champ.
    - `form_errors(liste)` : résumé en tête, rien si la liste est vide.
    - `flash_messages(flash)` : rend le message flash de session, s'il existe.

[Voir le bilan du niveau](bilan.md)
