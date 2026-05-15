# Audit CRUD-FILTER-AUDIT-001

## Résumé

Les filtres CRUD sont complets pour le périmètre simple déjà attendu par Forge :

- recherche `q` côté serveur ;
- filtres simples déclaratifs via `list.filter=true` ;
- filtres relationnels `many_to_one` automatiques ;
- combinaison `q` + filtres + pagination ;
- SQL paramétré.

Conclusion : **Cas A — CRUD-FILTER-001 déjà couvert** pour les filtres déclaratifs simples. Le ticket `CRUD-FILTER-001` est redondant en l'état. Le prochain ticket recommandé est `CRUD-SORT-001`.

## État du code

`forge make:crud` génère déjà la recherche `q` dans le contrôleur index :

- lecture de `q` via `_query_param(request, "q").strip()` ;
- passage de `q or None` à `count_<entites>` et `find_<entites>_paginated` ;
- conservation de `q` dans le contexte `pagination`.

Le modèle généré possède déjà :

- `_SEARCH_COLS` pour les colonnes texte recherchables ;
- `count_<entites>(q=None, filters=None)` ;
- `find_<entites>_paginated(q=None, sort=None, direction="asc", limit=10, offset=0, filters=None)` ;
- ajout de clauses `LIKE ?` pour `q` ;
- ajout de clauses `col = ?` pour les filtres ;
- combinaison des conditions par `" AND ".join(clauses)`.

Les filtres simples existent déjà via la métadonnée de champ :

```json
{
  "name": "statut",
  "sql_type": "VARCHAR(50)",
  "python_type": "str",
  "list": { "filter": true }
}
```

La fonction `_filter_fields` inclut :

- les champs portant `list.filter=true` ;
- les champs `many_to_one` déclarés dans `relations.json`, même sans `list.filter=true`.

Le contrôleur généré lit déjà des paramètres GET hors `q` :

- champ simple : `_query_param(request, "<champ>").strip()` ;
- booléen : valeur acceptée uniquement si `"0"` ou `"1"` ;
- relation `many_to_one` : parse entier, valeur vide ignorée, valeur invalide ignorée proprement.

Les filtres relationnels `many_to_one` existent déjà :

- chargement des options via `get_<target>_choices()` ;
- rendu `<select name="<fk>">` dans la vue index ;
- ajout de `WHERE <fk> = ?` via le dict `_filters` ;
- conservation dans `pagination.filters`.

La pagination générée conserve déjà :

- `q` ;
- `sort` ;
- `direction` ;
- tous les filtres via une boucle sur `pagination.filters.items()`.

## État des tests

`tests/test_entity_list_filter.py` couvre déjà :

- validation JSON de la clé `list` ;
- refus de `list` non objet ;
- refus de clé `list` inconnue ;
- refus de `list.filter` non booléen ;
- types supportés pour `list.filter=true` : `VARCHAR`, `CHAR`, entiers, `BOOL`, `BOOLEAN` ;
- types refusés : `TEXT`, `DATE`, `DATETIME`, `TIMESTAMP`, `DECIMAL`, `FLOAT` ;
- inclusion des champs `list.filter=true` ;
- exclusion des champs sans `list.filter` ;
- inclusion automatique des FK `many_to_one` ;
- génération des paramètres `filters` dans `count` et `find_paginated` ;
- combinaison `q` + filtres via `AND` ;
- SQL paramétré avec `col = ?` ;
- lecture des filtres depuis la requête ;
- booléens limités à `0` ou `1` ;
- parse entier des filtres relationnels ;
- valeur relationnelle vide ou invalide ignorée ;
- conservation des filtres dans `pagination`;
- rendu des filtres simples dans l'index ;
- rendu des filtres relationnels sous forme de `<select>` ;
- conservation des filtres dans les liens de tri et de pagination.

`tests/test_make_crud.py` couvre en plus :

- génération de la pagination ;
- lecture de `q`, `sort` et `page` ;
- conservation de `q` dans les liens ;
- options de filtre relationnel `many_to_one` ;
- absence de HTMX/Alpine dans les vues générées.

`tests/test_make_crud_search.py` couvre :

- recherche `q` GET ;
- `q.strip()` ;
- recherche inactive si `q` est vide ;
- `LIKE ?` paramétré ;
- exclusion des champs numériques, booléens, dates, PK et FK relationnelles ;
- conservation de `q` dans la pagination ;
- compatibilité avec `many_to_many`.

## État de la documentation

`docs/reference.md` est cohérent avec le code :

- documente la recherche `q` ;
- documente les filtres simples via `list.filter=true` ;
- documente les types supportés et refusés ;
- documente la combinaison `q` + filtres avec `AND` ;
- documente les filtres relationnels `many_to_one` ;
- précise que les valeurs sont paramétrées.

`docs/guide.md` mentionne la recherche `q`, mais ne détaille pas les filtres. Ce n'est pas une contradiction : le guide reste volontairement introductif.

`docs/roadmap.md` indiquait encore `CRUD-FILTER-001` comme prochain ticket. Cette information n'était plus alignée avec l'état réel du code et des tests.

## Analyse

Les filtres simples existent-ils ?

Oui. Ils sont déclarés au niveau des champs avec `list.filter=true`, rendus dans la vue index et appliqués au SQL via `filters`.

Les filtres relationnels existent-ils ?

Oui. Les relations `many_to_one` déclarées dans `relations.json` génèrent déjà un filtre `<select>`, chargent leurs options et appliquent `WHERE fk = ?`.

Les filtres sont-ils déclaratifs ?

Oui pour les champs simples via `list.filter=true`. Les filtres relationnels sont déduits déclarativement de `relations.json`.

Les filtres sont-ils paramétrés SQL ?

Oui. Les conditions de filtre utilisent `col = ?` et `params.append(val)`. La recherche utilise `LIKE ?` et `params.extend("%" + q + "%" ...)`.

`q` + filtres + pagination fonctionnent-ils ensemble ?

Oui. Le modèle combine les clauses par `AND`, le contrôleur passe `q` et `filters` aux fonctions de liste, et la vue conserve `q` et `pagination.filters` dans les liens.

Manque-t-il un vrai `CRUD-FILTER-001` ?

Pas pour les filtres simples et relationnels déjà prévus. Un futur ticket de filtres pourrait exister, mais il devrait être reformulé comme une extension avancée : opérateurs autres que l'égalité, filtres de dates, plages numériques, filtres multi-valeurs, interface plus riche ou HTMX. Ce n'est pas le périmètre de `CRUD-FILTER-001` tel qu'il était annoncé.

## Conclusion

### Cas A — CRUD-FILTER-001 déjà couvert

Le ticket `CRUD-FILTER-001` est inutile dans sa forme actuelle.

Prochain ticket recommandé : `CRUD-SORT-001`.

## Recommandation

Marquer `CRUD-FILTER-AUDIT-001` terminé.
Considérer `CRUD-FILTER-001` comme couvert par l'existant.
Mettre `CRUD-SORT-001` comme prochain ticket.
Ne créer un nouveau ticket filtre que pour un besoin avancé explicitement reformulé.
