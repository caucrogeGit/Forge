# Cartes, badges et retours

**Objectif** : afficher les données passées par le contrôleur sous forme de
chiffre-clé et de cartes, avec des pastilles de statut.

**Ce que vous allez apprendre :** les composants de présentation de
`components/ui.html` (`button`, `card`, `badge`, `stat`, `alert`,
`empty_state`), alimentés par le contexte du contrôleur (`total`, `contacts`).

## Rappel : ce que le contrôleur passe

Au préambule, `index` passe déjà `total` et `contacts`. Nous les consommons ici.

## Chiffre-clé et cartes alimentées par les données

Dans `showcase/index.html`, remplacez le paragraphe par :

```jinja
{% extends "layouts/base.html" %}
{% from "components/ui.html" import card, stat, badge, button %}

{% block title %}Annuaire · {{ app_name }}{% endblock %}

{% block content %}
  <div class="grid grid-cols-3 gap-4 mb-8">
    {{ stat(total, "contacts") }}
    {{ stat(contacts | selectattr("statut", "equalto", "actif") | list | length, "actifs") }}
    {{ button("Nouveau contact", variant="primary", href="/showcase/new", extra="self-center") }}
  </div>

  <div class="grid grid-cols-2 gap-4">
    {% for contact in contacts %}
      {% call card() %}
        <div class="flex items-center justify-between">
          <h3 class="font-bold">{{ contact.nom }}</h3>
          {% if contact.statut == "actif" %}{{ badge("Actif", tone="success") }}
          {% else %}{{ badge("Archivé", tone="neutral") }}{% endif %}
        </div>
        <p class="text-sm text-muted mt-1">{{ contact.email }} · {{ contact.academie }}</p>
      {% endcall %}
    {% endfor %}
  </div>
{% endblock %}
```

Le `stat` affiche un compte calculé, et une carte par contact réel boucle sur
`contacts`. La pastille reflète le statut de chaque enregistrement.

## Boutons et messages

```jinja
{% from "components/ui.html" import button, alert, empty_state %}

{{ button("Enregistrer", variant="primary") }}
{{ button("Annuler", variant="ghost", href="/showcase") }}

{{ alert("Pensez à compléter les coordonnées.", level="info") }}
```

`button` a trois variantes (`primary`, `secondary`, `ghost`). Pour une liste
vide, `empty_state("Aucun contact.")` remplace l'affichage.

??? note "À retenir"
    - Les composants consomment le **contexte du contrôleur** (`contacts`,
      `total`), pas des données en dur.
    - `card` s'utilise avec `{% call card() %} ... {% endcall %}`.
    - `badge(label, tone=...)` reflète une donnée (ici le statut).
    - `stat`, `alert`, `empty_state` complètent la présentation.

Au palier suivant, nous ajoutons le formulaire d'ajout (route `/showcase/new`).

[Continuer avec Le formulaire](formulaire.md)
