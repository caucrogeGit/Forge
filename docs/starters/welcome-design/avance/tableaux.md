# Tableaux et pagination

**Objectif** : afficher la liste des contacts dans un tableau stylé, avec une
recherche et une pagination.

**Ce que vous allez apprendre :** les composants de `components/data.html` :
`table` et `pagination`, complétés par `search_field` et `empty_state`.

## Une barre de recherche

```jinja
{% from "components/forms.html" import search_field %}

<form method="get" action="/showcase" class="mb-5 max-w-sm">
  {{ search_field("q", placeholder="Rechercher un contact...") }}
</form>
```

## Le tableau

`table(headers, rows)` attend des en-têtes et des lignes (listes de cellules).
Ici, une liste d'exemple ; dans une vraie application, le contrôleur la passe
en contexte.

```jinja
{% from "components/data.html" import table %}

{{ table(
     ["Nom", "Courriel", "Académie"],
     [
       ["Ada Lovelace", "ada@exemple.fr", "Paris"],
       ["Alan Turing", "alan@exemple.fr", "Lyon"],
     ]
) }}
```

Quand la liste est vide, le tableau affiche un message ; pour un rendu plus
visible, utilisez `empty_state` à la place du tableau.

!!! note "Colonne d'actions"
    Le rendu des cellules est échappé (sécurité), donc `table` affiche du texte.
    Pour une colonne d'actions (liens éditer / supprimer), composez le tableau à
    la main en reprenant les classes de `data.html`.

## La pagination

```jinja
{% from "components/data.html" import pagination %}

{{ pagination(page, total_pages, base_url="/showcase") }}
```

Les liens pointent vers `/showcase?page=N`. Les boutons Précédent / Suivant se
désactivent aux extrémités, et la macro n'affiche rien s'il n'y a qu'une page.

??? note "À retenir"
    - `table(headers, rows)` : tableau en lecture, cellules texte échappées.
    - `pagination(page, total_pages, base_url=...)` : navigation `?page=N`.
    - `search_field` pour un filtre, `empty_state` pour une liste vide.

Au dernier palier, nous ajoutons de l'interactivité sans JavaScript.

[Continuer avec Les composants interactifs](interactif.md)
