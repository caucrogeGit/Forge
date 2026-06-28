# La mise en page

**Objectif** : poser l'ossature de la page showcase : un en-tête de page, une
barre de navigation et un fil d'Ariane.

**Ce que vous allez apprendre :** le gabarit `layouts/base.html` fournit
l'enveloppe (en-tête de site, pied) ; les composants `page_header`, `navbar` et
`breadcrumb` structurent le contenu.

## La navigation du site

Le gabarit `base.html` expose un bloc `nav`. Remplissez-le avec la macro
`navbar`, dans `showcase/index.html` :

```jinja
{% extends "layouts/base.html" %}
{% from "components/ui.html" import navbar, page_header, breadcrumb %}

{% block title %}Annuaire · {{ app_name }}{% endblock %}

{% block nav %}
  {{ navbar([("Accueil", "/"), ("Annuaire", "/showcase")], current="/showcase") }}
{% endblock %}
```

La barre se place dans l'en-tête de site, et le lien actif (`current`) est
surligné.

## L'en-tête de page et le fil d'Ariane

Dans le bloc `content`, ajoutez un fil d'Ariane puis un en-tête de page avec un
bouton d'action :

```jinja
{% block content %}
  {{ breadcrumb([("Accueil", "/"), ("Annuaire", "")]) }}

  {{ page_header("Annuaire",
       subtitle="Les contacts de l'établissement.",
       action_label="Nouveau contact",
       action_href="/showcase/new") }}
{% endblock %}
```

Le dernier élément du fil d'Ariane (href vide) est la page courante, non
cliquable. `page_header` aligne le titre à gauche et le bouton d'action à droite.

??? note "À retenir"
    - `navbar(liens, current=...)` se pose dans le bloc `nav` du gabarit.
    - `breadcrumb(items)` : le dernier item sans href est la page courante.
    - `page_header(titre, subtitle=..., action_label=..., action_href=...)`
      titre une page et offre un bouton d'action.

Votre page a maintenant une vraie ossature.

[Voir le bilan du niveau](bilan.md)
