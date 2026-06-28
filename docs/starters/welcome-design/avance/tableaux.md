# Tableaux et pagination

**Objectif** : afficher l'annuaire dans un tableau, avec une recherche et une
pagination, le tout piloté par le contrôleur.

**Ce que vous allez apprendre :** les composants de `components/data.html`
(`table`, `pagination`) et `search_field`, alimentés par un contrôleur qui lit
la recherche et la page dans la requête.

## Le contrôleur lit la requête et façonne les données

Faites évoluer `index` pour lire `q` et `page`, filtrer, paginer, et passer des
lignes prêtes pour le tableau :

```python
    _PER_PAGE = 5

    @staticmethod
    def index(request: Request) -> Response:
        q = request.query("q", default="").strip()
        page = int(request.query("page", default="1") or 1)

        filtres = [c for c in _CONTACTS if q.lower() in c["nom"].lower()]
        total_pages = max(1, (len(filtres) + ShowcaseController._PER_PAGE - 1) // ShowcaseController._PER_PAGE)
        page = min(max(page, 1), total_pages)
        debut = (page - 1) * ShowcaseController._PER_PAGE
        visibles = filtres[debut:debut + ShowcaseController._PER_PAGE]

        rows = [[c["nom"], c["email"], c["academie"]] for c in visibles]

        return BaseController.render(
            "showcase/index.html",
            request=request,
            context={
                "rows": rows,
                "q": q,
                "page": page,
                "total_pages": total_pages,
                "total": len(_CONTACTS),
                "flash": get_flash(get_session_id(request)),
            },
        )
```

## La barre de recherche

Dans `showcase/index.html` :

```jinja
{% from "components/forms.html" import search_field %}

<form method="get" action="/showcase" class="mb-5 max-w-sm">
  {{ search_field("q", value=q, placeholder="Rechercher un contact...") }}
</form>
```

Le champ renvoie `?q=...` à `/showcase`, que le contrôleur relit dans `q`.

## Le tableau et la pagination

```jinja
{% from "components/data.html" import table, pagination %}

{{ table(["Nom", "Courriel", "Académie"], rows) }}
{{ pagination(page, total_pages, base_url="/showcase") }}
```

Le contrôleur a façonné `rows` (listes de cellules) ; `table` les affiche, et
`pagination` produit les liens `?page=N`. Quand `rows` est vide, le tableau
montre un message ; la macro `pagination` ne s'affiche pas s'il n'y a qu'une
page.

!!! note "Colonne d'actions"
    Le rendu des cellules est échappé (sécurité). Pour une colonne d'actions
    (liens éditer / supprimer), composez le tableau à la main en reprenant les
    classes de `data.html`.

??? note "À retenir"
    - Le contrôleur lit `request.query(...)` et **façonne** les données (filtre,
      pagination, lignes) ; la vue ne fait qu'afficher.
    - `table(headers, rows)` et `pagination(page, total_pages, base_url=...)`.
    - `search_field` renvoie `?q=...`, relu par le contrôleur.

Au dernier palier, nous ajoutons l'interactivité sans JavaScript.

[Continuer avec Les composants interactifs](interactif.md)
