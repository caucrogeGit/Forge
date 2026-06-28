# Cartes, badges et retours

**Objectif** : remplir la page avec des cartes, des chiffres-clés, des pastilles
de statut et des messages.

**Ce que vous allez apprendre :** les composants de présentation de
`components/ui.html` : `button`, `card`, `badge`, `stat`, `alert`, `empty_state`.

## Boutons

Trois variantes, en bouton ou en lien (avec `href`) :

```jinja
{% from "components/ui.html" import button %}

{{ button("Enregistrer", variant="primary") }}
{{ button("Filtrer", variant="secondary") }}
{{ button("Annuler", variant="ghost", href="/showcase") }}
```

## Chiffres-clés et cartes

Ajoutez une bande de statistiques puis une carte, dans le bloc `content` :

```jinja
{% from "components/ui.html" import card, stat, badge %}

<div class="grid grid-cols-3 gap-4 mb-8">
  {{ stat("128", "contacts") }}
  {{ stat("12", "classes") }}
  {{ stat("98 %", "joignables") }}
</div>

{% call card() %}
  <div class="flex items-center justify-between">
    <h3 class="font-bold">Collège Jean Moulin</h3>
    {{ badge("Actif", tone="success") }}
  </div>
  <p class="text-sm text-muted mt-1">Académie de Paris</p>
{% endcall %}
```

## Pastilles de statut

`badge` accepte un `tone` : `success`, `warning`, `danger`, `neutral`.

```jinja
{{ badge("Actif", tone="success") }}
{{ badge("En attente", tone="warning") }}
{{ badge("Archivé", tone="neutral") }}
```

## Messages et état vide

```jinja
{% from "components/ui.html" import alert, empty_state %}

{{ alert("Pensez à compléter les coordonnées.", level="info") }}

{{ empty_state("Aucun contact pour l'instant.",
     hint="Ajoutez-en un avec le bouton Nouveau contact.") }}
```

`alert` accepte `success`, `error`, `warning`, `info`. `empty_state` se pose à la
place d'une liste vide.

??? note "À retenir"
    - `button(label, variant=..., href=...)` : `primary`, `secondary`, `ghost`.
    - `card` s'utilise avec `{% call card() %} ... {% endcall %}`.
    - `badge(label, tone=...)` et `alert(message, level=...)` partagent la même
      logique de tons.
    - `stat(valeur, libellé)` pour un chiffre-clé, `empty_state` pour une liste
      vide.

Au palier suivant, nous ajoutons un formulaire de saisie.

[Continuer avec Le formulaire](formulaire.md)
