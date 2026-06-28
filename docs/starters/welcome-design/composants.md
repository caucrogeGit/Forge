# La bibliothèque de composants

**Objectif**{ .intro-label } : réutiliser des composants HTML normalisés
(boutons, cartes, champs de formulaire) au lieu de recopier des classes
Tailwind dans chaque page.

**Ce que vous allez apprendre :**{ .intro-label } les composants sont des
**macros Jinja** rangées dans `mvc/views/components/`.
On les importe avec `{% from ... import ... %}`, puis on les appelle comme des
fonctions.

## Deux fichiers

| Fichier | Macros |
|---|---|
| `components/ui.html` | `button`, `card`, `badge`, `alert` |
| `components/forms.html` | `field`, `textarea_field`, `select_field`, `checkbox`, `submit` |

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

## Messages contextuels

```jinja
{% from "components/ui.html" import alert %}

{{ alert("Enregistrement réussi.", level="success") }}
{{ alert("Une erreur est survenue.", level="error") }}
```

!!! tip "Étendre la bibliothèque"
    Ces macros sont **votre code**.
    Ajoutez vos propres composants (tableau, pagination, fenêtre modale) dans
    `components/`, en réutilisant les tokens de la charte pour rester cohérent.

??? note "À retenir"
    - Les composants sont des macros Jinja dans `mvc/views/components/`.
    - On les importe avec `{% from "components/..." import ... %}`.
    - Les champs de formulaire ne gèrent pas la balise `<form>` ni le CSRF :
      composez-les vous-même autour des macros.

[Terminer avec le bilan](bilan.md)
