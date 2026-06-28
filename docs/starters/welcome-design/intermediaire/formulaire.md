# Le formulaire

**Objectif** : construire un formulaire d'ajout de contact avec les composants de
saisie.

**Ce que vous allez apprendre :** les macros de `components/forms.html` :
`field`, `select_field`, `radio_group`, `checkbox`, `file_field`, `fieldset`,
`submit`. Les macros produisent les champs ; la balise `<form>` et le jeton CSRF
restent à votre charge (pas de magie cachée).

## Un formulaire complet

Ajoutez dans le bloc `content` :

```jinja
{% from "components/forms.html" import field, select_field, radio_group, checkbox, fieldset, submit %}

<form method="post" action="/showcase/store">
  {% include "partials/csrf.html" %}

  {% call fieldset("Identité") %}
    {{ field("nom", label="Nom", required=True) }}
    {{ field("email", label="Courriel", type="email", required=True) }}
  {% endcall %}

  {{ select_field("academie", label="Académie",
       options=[("paris", "Paris"), ("lyon", "Lyon"), ("lille", "Lille")]) }}

  {{ radio_group("statut", label="Statut",
       options=[("actif", "Actif"), ("archive", "Archivé")], selected="actif") }}

  {{ checkbox("newsletter", "Recevoir les actualités", checked=True) }}

  {{ submit("Enregistrer le contact") }}
</form>
```

## Le catalogue des champs

| Macro | Usage |
|---|---|
| `field(name, label, type, required, help)` | texte, courriel, mot de passe, nombre... (via `type`) |
| `textarea_field(name, label, rows)` | texte multi-lignes |
| `select_field(name, label, options, selected)` | liste déroulante (`options` = couples) |
| `radio_group(name, label, options, selected)` | choix exclusif |
| `checkbox(name, label, checked)` | case à cocher |
| `file_field(name, label, accept)` | envoi de fichier |
| `search_field(name, placeholder)` | champ de recherche |
| `fieldset(legend)` | regroupe des champs (`{% call %}`) |
| `submit(label)` | bouton d'envoi pleine largeur |

??? note "À retenir"
    - Les macros produisent les champs, pas la balise `<form>` ni le CSRF.
    - Incluez toujours `partials/csrf.html` dans vos formulaires POST.
    - `fieldset` regroupe des champs sous un titre avec `{% call %}`.

Au palier suivant, nous affichons les erreurs de validation.

[Continuer avec La validation](validation.md)
