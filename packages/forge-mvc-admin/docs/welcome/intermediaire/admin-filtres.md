# Intermédiaire 4 : Filtrer et rechercher

Objectif : retrouver une ligne parmi mille, sans quitter la liste.

## Deux mécanismes, deux usages

La liste paginée du palier débutant affiche tout, page après page.
Deux attributs de la ressource lui ajoutent de quoi réduire l'affichage.

```python
registry.register(AdminResource(
    entity="Article",
    slug="articles",
    label="Article",
    plural_label="Articles",
    list_fields=("title", "status", "published_at"),
    form_fields=("title", "body"),
    table="articles",
    filter_fields=("status",),
    search_fields=("title", "body"),
))
```

| Attribut | Ce qu'il produit |
|---|---|
| `filter_fields` | une **égalité** exacte, `?status=draft` dans l'URL |
| `search_fields` | une recherche **partielle**, `?q=forge`, sur toutes les colonnes citées |

Les deux se combinent : `?status=draft&q=forge` cherche « forge » parmi les seuls brouillons.

## Le SQL engendré

```sql
WHERE status = ? AND (title LIKE ? ESCAPE '!' OR body LIKE ? ESCAPE '!')
```

Les valeurs partent en paramètres liés, jamais dans le texte de la requête.

!!! danger "Une colonne non déclarée est refusée, et c'est le point"
    `?mot_de_passe=x` répond une erreur, pas une ligne.

    Sans cette liste blanche, l'URL choisirait la colonne à interroger : un visiteur filtrerait sur une colonne que la liste n'affiche pas, et déduirait son contenu des lignes rendues.

!!! info "Les jokers d'une recherche sont neutralisés"
    Chercher `%` ou `_` cherche ces caractères, il ne les prend pas pour des jokers.

    Sans cela, un `%` seul rendrait toute la table, et un `_` toutes les lignes d'un caractère : la recherche deviendrait un moyen de tout lire.

## À retenir

- `filter_fields` filtre par égalité, `search_fields` cherche par fragment.
- Seules les colonnes déclarées sont interrogeables ; les autres sont refusées.
- Les valeurs sont liées et les jokers échappés.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
