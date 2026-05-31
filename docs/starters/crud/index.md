# CRUD

Le sujet **CRUD** regroupe les starters qui assemblent les quatre opérations
fondamentales d'une application web — **C**reate, **R**ead, **U**pdate,
**D**elete — sur une table unique, avec du **SQL visible** et **aucun ORM**.

Conformément à la charte Forge, le SQL reste écrit et nommé par vous :
chaque requête (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) est explicite, sans
couche d'abstraction ni magie cachée. L'entité manipulée est **neutre**
(`message`), sans notion métier.

## Parcours

Le sujet CRUD propose **deux starters sur la même entité neutre `message`**,
qui montrent **deux méthodes** pour obtenir le même CRUD — la paire
didactique « à la main » / « généré » :

| Méthode | Starter | Objectif |
|--------|---------|----------|
| À la main | [First CRUD — `first-crud`](first-crud.md) | Le CRUD complet **écrit à la main** : `fetch_all` / `fetch_one` / `insert` / `execute`, lecture d'un `{id}` de chemin, formulaire + CSRF des paliers précédents. SQL visible, aucun ORM. |
| Généré | [First CRUD (généré) — `first-crud-generated`](first-crud-generated.md) | Le même CRUD, mais **échafaudé par génération** : un manifeste d'entité canonique puis `forge make:crud` produit contrôleur, modèle SQL, formulaire et vues. Routes câblées manuellement. SQL visible, aucun ORM. |

Les deux portent sur une entité **neutre** (`message`), sans notion métier :
le premier montre comment **on écrit** un CRUD, le second comment Forge le
**génère** depuis un manifeste.

## Pour aller plus loin

- [Migrations SQL](../../features/migrations.md)
- [Référence HTTP (Request / Response)](../../reference/http.md)
- [Catalogue complet des starters](../index.md)
