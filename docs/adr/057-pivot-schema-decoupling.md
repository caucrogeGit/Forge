# ADR-057 : Découplage du schéma pivot et extraction vers forge-mvc-pivot

## Statut

Proposé, Forge 1.0.0-rc (ticket `ADR-PIVOT-SCHEMA-DECOUPLE-001`).
Décision de périmètre cœur/opt-in et de frontière de contrat ; relève du mainteneur.

---

## Date

2026-06-29

---

## Contexte

Le pivot enrichi (table `many_to_many` portant des attributs) est un opt-in, `forge-mvc-pivot` (ADR-021).
Pourtant, son contrat JSON Schema vit dans le cœur, et il y est **entrelacé** :

- `schemas/pivot.schema.json` (et sa copie `cli/schemas/pivot.schema.json`) décrivent la structure du bloc pivot enrichi ;
- surtout, `relations.schema.json` **du cœur** référence `pivot.schema.json` (`"$ref": "pivot.schema.json"`) dans la définition `manyToMany`.

C'est l'inverse de RBAC : `rbac.schema.json` était autonome (ADR-056), alors que `pivot.schema.json` est référencé par un schéma du cœur.
Un simple déplacement du fichier casserait la résolution du schéma `relations` du cœur.

Graphe des `$ref` (vérifié, refs `#` comprises) :

```
relations  -> pivot, common (entityName, relationName, columnName, onDelete, schemaVersion)
pivot      -> field, common (columnName, onDelete, tableName)
field      -> common (fieldName)
entity     -> field, common
common     -> (interne)
```

`relations` dépend de `pivot`, et `pivot` dépend de `field` et `common`.

Constat d'usage : le générateur `make:pivot-crud` de l'opt-in **ne charge pas** `pivot.schema.json` (il contrôle `schema_version` à la main).
Le schéma pivot est donc un **contrat de documentation / validation IDE**, pas un artefact chargé au runtime du cœur.

Maintenir le contrat d'un opt-in dans le cœur, et coupler un schéma du cœur (`relations`) à ce contrat, contredit les principes 4, 8 et 10.

---

## Décision

### 1. Découpler `relations` (cœur) de `pivot` (opt-in)

Le schéma `relations.schema.json` du cœur **cesse de référencer** `pivot.schema.json`.
Dans la définition `manyToMany`, le bloc `pivot` devient un **objet optionnel opaque** : le cœur valide qu'il s'agit d'un objet, sans en valider la structure interne.

Justification : le `many_to_many` **de base** (table de jonction simple) relève du cœur ; la **structure enrichie** du pivot (attributs, contraintes) relève de l'opt-in.
Un projet sans l'opt-in ne déclare pas de bloc pivot enrichi ; un projet avec l'opt-in obtient la validation stricte de l'opt-in.
Ainsi `relations.json` reste valide pour le cœur avec ou sans l'opt-in (`entity:validate` ne dépend plus du contrat pivot).

### 2. Extraire `pivot.schema.json` vers `forge-mvc-pivot`

Le schéma rejoint le paquet (`forge_mvc_pivot/schemas/`, package-data), où il valide strictement le bloc pivot enrichi.
Pour être **autonome** (comme `rbac` l'est devenu en inlinant `schemaVersion`, ADR-056), l'opt-in règle ses dépendances de schéma :

- les définitions `common` utilisées (`columnName`, `onDelete`, `tableName`) sont **inlinées** dans le schéma pivot du paquet ;
- la référence à `field.schema.json` est satisfaite en **embarquant une copie de `field.schema.json`** (et de `common.schema.json` si nécessaire) aux côtés du schéma pivot dans le paquet, faute de base de schémas partagée publiée.

Note : la duplication de `field`/`common` dans l'opt-in est assumée à ce stade ; le chantier de déduplication des schémas (source unique) pourra la résorber plus tard.

### 3. Retirer le pivot du cœur

`pivot.schema.json` est retiré de `cli/schemas/`, de `schemas/` (racine), du gabarit `skeleton/data/schemas/`, et de l'entrée `pivot` des deux `forge.schema.index.json`.
Le jeu de schémas du cœur passe à quatre : `common`, `field`, `entity`, `relations`.

---

## Conséquences

Le cœur ne porte plus le contrat pivot ni de dépendance vers lui : périmètre réduit, `relations` autoporteur.
`forge-mvc-pivot` devient autoporteur pour son contrat (schéma embarqué et autonome).
La validation du bloc pivot par le cœur devient permissive (objet opaque) ; la validation stricte est du ressort de l'opt-in.

Blast radius de l'implémentation (ticket distinct) : retirer le `$ref` pivot de `relations.schema.json` (cœur + copies) et rendre le bloc pivot opaque ; déplacer `pivot.schema.json` dans le paquet et le rendre autonome (inline common + copie field) ; retirer pivot des trois dossiers de schémas et des deux index ; adapter les tests (`test_forge_schema_index`, `schema:list`/`schema:doctor` 5 -> 4, `test_pivot_json_schema`, garde de synchro, wheel) et la documentation.

---

## Alternatives écartées

**Laisser `pivot.schema.json` dans le cœur.**
Maintient le contrat d'un opt-in dans le cœur et un schéma du cœur couplé à l'opt-in (principes 4/8/10).

**Retirer entièrement le bloc `pivot` du schéma `relations` du cœur.**
`entity:validate` (cœur) rejetterait alors un `relations.json` contenant un bloc pivot, cassant les projets qui utilisent l'opt-in (la validation des relations reste une commande du cœur).
L'objet opaque préserve la compatibilité.

**Publier une base de schémas partagée (`field`/`common`) consommable par les opt-ins.**
Plus propre à terme, mais hors périmètre : cela relève du chantier de déduplication.
En attendant, l'opt-in embarque les copies nécessaires.

---

## Charte appliquée

- Principe 4 (périmètre du cœur) : le pivot quitte le cœur.
- Principe 8 (noyau minimal, briques opt-in) : l'opt-in porte son contrat.
- Principe 10 (contrat de complétude) : `forge-mvc-pivot` fournit son schéma complet.
- Règle A (retirer la cause) : on supprime le `$ref` cœur -> opt-in dans `relations`.

---

## Référence

- [ADR-021](021-pivot-extraction.md) : extraction du pivot enrichi vers forge-mvc-pivot.
- [ADR-056](056-rbac-contract-tooling-extraction.md) : extraction RBAC (schéma autonome par inline).
- [ADR-038](038-optin-docs-embedded-per-package.md) : doc des opt-ins embarquée par paquet.
- `cli/schemas/relations.schema.json` : `$ref` pivot à retirer (rendre le bloc opaque).
- `forge-mvc-pivot/forge_mvc_pivot/make_pivot_crud.py` : consommateur du format pivot.
