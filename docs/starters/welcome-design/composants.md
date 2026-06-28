# La bibliothèque de composants

**Objectif**{ .intro-label } : réutiliser des composants HTML normalisés
(boutons, cartes, champs de formulaire) au lieu de recopier des classes
Tailwind dans chaque page.

**Ce que vous allez apprendre :**{ .intro-label } les composants sont des
**macros Jinja** rangées dans `mvc/views/components/`.
On les importe avec `{% from ... import ... %}`, puis on les appelle comme des
fonctions.

## Quatre fichiers

| Fichier | Macros |
|---|---|
| `components/ui.html` | `button`, `card`, `badge`, `alert`, `flash_messages`, `page_header`, `empty_state`, `stat`, `breadcrumb`, `navbar` |
| `components/forms.html` | `field`, `textarea_field`, `select_field`, `radio_group`, `file_field`, `search_field`, `checkbox`, `fieldset`, `form_errors`, `submit` |
| `components/data.html` | `table`, `pagination` |
| `components/interactive.html` | `accordion`, `dropdown`, `modal` (HTML natif, sans framework JS) |

## Boutons, cartes, badges

```jinja
{% from "components/ui.html" import button, card, badge %}

{{ badge("Nouveau") }}

{{ button("Enregistrer", variant="primary") }}
{{ button("Annuler", variant="ghost", href="/") }}

{% call card() %}
  <h2 class="text-lg font-bold mb-2">Une carte</h2>
  <p class="text-muted text-sm">Le contenu passe entre call et endcall.</p>
{% endcall %}
```

Le bouton accepte `variant` (`primary`, `secondary`, `ghost`) ; passez `href`
pour produire un lien `<a>`, sinon un `<button>`.

## Un formulaire complet

Les macros produisent uniquement les champs.
La balise `<form>`, la méthode, l'action et le jeton CSRF restent à votre
charge (principe : pas de magie cachée).

```jinja
{% from "components/forms.html" import field, select_field, checkbox, submit %}

<form method="post" action="/contact/store">
  {% include "partials/csrf.html" %}

  {{ field("nom", label="Nom", required=True) }}
  {{ field("email", label="Courriel", type="email", required=True) }}
  {{ select_field("role", label="Rôle",
       options=[("admin", "Administrateur"), ("membre", "Membre")]) }}
  {{ checkbox("cgu", "J'accepte les conditions", checked=False) }}
  {{ submit("Envoyer") }}
</form>
```

## Erreurs de validation

Passez `error` à un champ pour afficher la bordure rouge et le message, et
`form_errors` pour un résumé en tête (réponses 422, validation serveur) :

```jinja
{% from "components/forms.html" import field, form_errors, submit %}

{{ form_errors(errors) }}
{{ field("email", label="Courriel", type="email", error="Adresse invalide.") }}
{{ submit("Réessayer") }}
```

## Listes et tableaux

```jinja
{% from "components/data.html" import table, pagination %}
{% from "components/ui.html" import page_header, empty_state %}

{{ page_header("Contacts", action_label="Nouveau", action_href="/contact/new") }}
{{ table(["Nom", "Courriel"], lignes) }}
{{ pagination(page, total_pages, base_url="/contact") }}
```

Quand la liste est vide : `{{ empty_state("Aucun contact pour l'instant.") }}`.

## Messages contextuels

```jinja
{% from "components/ui.html" import alert, flash_messages %}

{{ alert("Enregistrement réussi.", level="success") }}
{{ flash_messages(flash) }}   {# rend le message flash de session, s'il existe #}
```

## Composants interactifs sans JavaScript

`components/interactive.html` s'appuie sur les éléments natifs `<details>`
(accordéon, menu) et `<dialog>` (modale), sans framework JS :

```jinja
{% from "components/interactive.html" import accordion, modal, modal_trigger %}

{% call accordion("Détails") %}Contenu repliable.{% endcall %}

{{ modal_trigger("confirm", "Supprimer") }}
{% call modal("confirm", "Confirmer la suppression") %}
  Cette action est définitive.
{% endcall %}
```

!!! tip "Étendre la bibliothèque"
    Ces macros sont **votre code**.
    Ajoutez vos propres composants en réutilisant les tokens de la charte pour
    rester cohérent.

??? note "À retenir"
    - Les composants sont des macros Jinja dans `mvc/views/components/`.
    - On les importe avec `{% from "components/..." import ... %}`.
    - Les champs de formulaire ne gèrent pas la balise `<form>` ni le CSRF :
      composez-les vous-même autour des macros.

[Terminer avec le bilan](bilan.md)
