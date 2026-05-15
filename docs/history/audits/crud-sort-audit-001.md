# Audit CRUD-SORT-001

## Résumé

Conclusion : **Cas B — le tri existait déjà, avec une stabilisation mineure nécessaire**.

Forge générait déjà un tri CRUD simple côté serveur :

- lecture de `sort` ;
- lecture de `direction` ;
- allowlist `_ALLOWED_SORT` ;
- fallback `_DEFAULT_SORT` ;
- `ORDER BY` construit depuis une colonne validée ;
- liens de tri dans `index.html` ;
- conservation de `q`, des filtres, de `sort` et de `direction` dans la pagination.

Le seul point corrigé est le fallback de `direction` invalide dans le contrôleur généré : il revient maintenant à `asc`.

## Surface auditée

Audit limité à :

- `forge_cli/entities/make_crud.py` ;
- `tests/test_make_crud.py` ;
- `tests/test_entity_list_filter.py` ;
- `tests/test_make_crud_search.py` ;
- tests de pagination/list CRUD ;
- `docs/reference.md` ;
- `docs/guide.md` ;
- `docs/roadmap.md` ;
- `docs/audits/crud-filter-audit-001.md`.

## État du code

`build_model` génère :

- `_ALLOWED_SORT = {"champ": "ColonneSql", ...}` ;
- `_DEFAULT_SORT = "<pk>"` ;
- `sort_col = _ALLOWED_SORT.get(sort, _DEFAULT_SORT)` ;
- `sort_dir = "DESC" if direction == "desc" else "ASC"` ;
- `ORDER BY " + sort_col + " " + sort_dir`.

La valeur GET `sort` n'est donc pas injectée directement dans SQL. Elle sert seulement de clé dans `_ALLOWED_SORT`.

La valeur GET `direction` n'est pas injectée directement. Elle est réduite à `DESC` uniquement si elle vaut exactement `desc`; tous les autres cas utilisés par le modèle donnent `ASC`.

`build_controller` génère :

- lecture de `sort` via `_query_param(request, "sort")` ;
- validation de `sort` contre les champs autorisés ;
- fallback `sort = ""` si la clé est inconnue ;
- lecture de `direction` via `_query_param(request, "direction", "desc")` ;
- fallback `direction = "asc"` si la valeur n'est ni `asc` ni `desc`.

`build_index_view` génère :

- liens `?sort=<champ>` sur les colonnes simples affichées ;
- inversion simple de direction quand on clique à nouveau sur la colonne active ;
- flèche `↑` ou `↓` sur la colonne active ;
- conservation de `q` ;
- conservation de `page` selon la convention existante ;
- conservation des filtres via `pagination.filters.items()`.

La pagination conserve :

- `q` ;
- `sort` ;
- `direction` ;
- `filters`.

## État des tests

Avant ce ticket, les tests couvraient déjà :

- lecture de `sort` ;
- lecture de `direction` ;
- présence de `_ALLOWED_SORT` ;
- absence de clés arbitraires dans `_ALLOWED_SORT` ;
- usage de `_ALLOWED_SORT.get(sort, _DEFAULT_SORT)` ;
- conservation de `q` dans les liens ;
- conservation des filtres dans les liens de tri et pagination.

Ce ticket ajoute `tests/test_make_crud_sort.py`, qui couvre :

- lecture de `sort` et `direction` ;
- fallback `direction` invalide vers `asc` ;
- fallback `sort` invalide ;
- `ORDER BY` depuis allowlist ;
- absence de concaténation directe de `sort` et `direction` ;
- liens de tri ;
- conservation de `q` ;
- conservation des filtres ;
- conservation de `sort` et `direction` dans la pagination ;
- compatibilité avec filtres simples ;
- compatibilité avec filtres `many_to_one` ;
- absence de tri `many_to_many` ;
- absence de HTMX et JavaScript.

## État de la documentation

`docs/reference.md` ne documentait pas encore clairement le tri CRUD généré.

`docs/guide.md` mentionnait la recherche, mais pas le tri. Une phrase courte suffit pour le guide.

`docs/roadmap.md` marquait `CRUD-SORT-001` comme prochain. Après validation, il est marqué terminé et `CRUD-PAGINATION-001` devient le prochain ticket.

## Analyse

Le tri CRUD existe-t-il déjà ?

Oui. Le modèle, le contrôleur et le template index contenaient déjà la mécanique de tri.

Le tri est-il sécurisé ?

Oui, après stabilisation. La sécurité repose sur `_ALLOWED_SORT` pour les colonnes et sur une réduction stricte de `direction` vers `ASC` ou `DESC`.

Le tri est-il documenté ?

Partiellement avant ce ticket. La référence est maintenant explicite.

Les tests sont-ils suffisants ?

Ils étaient partiels. Le fichier `tests/test_make_crud_sort.py` verrouille désormais le contrat attendu.

## Conclusion

### Cas B — Tri présent, stabilisation mineure

`CRUD-SORT-001` n'avait pas besoin d'une réécriture du CRUD. Le socle existait déjà. Le ticket a stabilisé le fallback de direction invalide, ajouté la couverture dédiée et documenté le comportement.

## Recommandation

Marquer `CRUD-SORT-001` terminé.
Conserver le tri comme un tri simple par colonne allowlistée.
Ne pas ajouter de tri multi-colonnes dans ce périmètre.
Ne pas ajouter de tri `many_to_many`.
Prochain ticket recommandé : `CRUD-PAGINATION-001`.
