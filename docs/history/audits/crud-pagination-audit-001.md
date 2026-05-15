# Audit CRUD-PAGINATION-001

## Résumé

Conclusion : **Cas B — pagination présente, stabilisation nécessaire**.

Forge générait déjà une pagination côté serveur dans les listes CRUD :

- lecture de `page` ;
- retour à la page 1 si la valeur était invalide ;
- `limit` fixe ;
- `offset` calculé ;
- `count_<entites>` ;
- `find_<entites>_paginated` ;
- liens précédent/suivant ;
- conservation de `q`, filtres, `sort` et `direction`.

Mais le CRUD généré recalculait sa pagination à la main alors que Forge possède déjà `core.mvc.view.pagination.Pagination`. Le ticket a donc stabilisé le générateur pour utiliser cette classe.

## Surface auditée

Audit limité à :

- `forge_cli/entities/make_crud.py` ;
- `core/mvc/view/pagination.py` ;
- `tests/test_make_crud.py` ;
- `tests/test_make_crud_search.py` ;
- `tests/test_make_crud_sort.py` ;
- `tests/test_entity_list_filter.py` ;
- `tests/test_pagination.py` ;
- documentation `reference`, `guide`, `roadmap`.

## État du code

`Pagination` expose déjà :

- `page` ;
- `nb_pages` ;
- `limit` ;
- `offset` ;
- `has_previous` / `has_next` ;
- `previous_page` / `next_page` ;
- `to_dict()`.

Elle lit `request.params["page"]`, borne la page entre 1 et le nombre de pages, et garantit un offset non négatif.

Le CRUD généré utilise maintenant :

```python
pagination_state = Pagination(request, total, limit)
limit = pagination_state.limit
offset = pagination_state.offset
pagination = pagination_state.to_dict()
pagination.update({
    "q": q, "sort": sort, "direction": direction,
    "filters": filters,
})
```

Le modèle généré conserve :

- `count_<entites>(q=None, filters=None)` ;
- `find_<entites>_paginated(q=None, sort=None, direction="asc", limit=10, offset=0, filters=None)` ;
- `LIMIT ? OFFSET ?` avec paramètres SQL ;
- les mêmes clauses `q` et `filters` pour le count et la liste paginée.

## État des tests

Les tests existants couvraient déjà :

- présence de `count` et `find_paginated` ;
- `LIMIT ? OFFSET ?` ;
- contexte `pagination` ;
- conservation de `q` ;
- conservation des filtres ;
- conservation de `sort` et `direction`.

Ce ticket ajoute `tests/test_make_crud_pagination.py`, qui couvre :

- usage de `Pagination` dans le contrôleur généré ;
- gestion de page absente, invalide ou négative par le core ;
- `limit` fixe à 20 côté CRUD généré ;
- `offset` fourni par `Pagination` ;
- passage de `q`, filtres, `sort` et `direction` ;
- liens précédent/suivant ;
- conservation de `q`, filtres, `sort`, `direction` ;
- compatibilité avec filtres simples ;
- compatibilité avec filtres `many_to_one` ;
- compatibilité avec tri ;
- absence de HTMX et JavaScript.

## État de la documentation

`docs/reference.md` documente maintenant la pagination CRUD générée :

- `page` ;
- `limit` fixe ;
- usage de `Pagination` ;
- conservation de `q`, filtres, `sort`, `direction` ;
- limites : pas de HTMX, infinite scroll ou taille de page dynamique.

`docs/guide.md` garde une mention courte.

`docs/roadmap.md` marque `CRUD-PAGINATION-001` terminé et place `CRUD-EMPTY-001` comme prochain ticket.

## Analyse

La pagination CRUD existe-t-elle déjà ?

Oui. Elle existait dans `make:crud`, mais était calculée localement dans le contrôleur généré.

La pagination est-elle robuste ?

Oui après stabilisation. La classe `Pagination` centralise la lecture de page, borne les valeurs et calcule `limit` / `offset`.

La pagination est-elle cohérente avec `q`, filtres et tri ?

Oui. Le contrôleur enrichit le dict `Pagination.to_dict()` avec `q`, `filters`, `sort` et `direction`, puis le template les conserve dans les liens.

La documentation est-elle alignée ?

Oui après mise à jour.

Les tests sont-ils suffisants ?

Oui pour le périmètre simple. Les tests dédiés verrouillent le contrat généré.

## Conclusion

### Cas B — Pagination présente, stabilisation mineure

`CRUD-PAGINATION-001` n'a pas nécessité de nouvelle pagination. Le ticket a relié le CRUD généré à la classe `Pagination` existante et ajouté les tests/documentations manquants.

## Recommandation

Marquer `CRUD-PAGINATION-001` terminé.
Conserver une taille de page fixe dans ce périmètre.
Ne pas ajouter de `limit` GET tant qu'un ticket dédié ne le demande pas.
Prochain ticket recommandé : `CRUD-EMPTY-001`.
