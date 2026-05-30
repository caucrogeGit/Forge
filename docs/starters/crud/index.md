# CRUD

Le sujet **CRUD** regroupe les starters qui assemblent les quatre opérations
fondamentales d'une application web — **C**reate, **R**ead, **U**pdate,
**D**elete — sur une table unique, avec du **SQL visible** et **aucun ORM**.

Conformément à la charte Forge, le SQL reste écrit et nommé par vous :
chaque requête (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) est explicite, sans
couche d'abstraction ni magie cachée. L'entité manipulée est **neutre**
(`message`), sans notion métier.

## Parcours

| Niveau | Starter | Objectif |
|--------|---------|----------|
| Capstone fondamentaux | [First CRUD — `first-crud`](first-crud.md) | Le CRUD complet écrit à la main : `fetch_all` / `fetch_one` / `insert` / `execute`, lecture d'un `{id}` de chemin, formulaire + CSRF des paliers précédents. SQL visible, aucun ORM. |

Un seul niveau pour l'instant. Un second starter **`first-crud-generated`**
— même CRUD, mais échafaudé par génération — rejoindra ce sujet
prochainement (à venir).

## Pour aller plus loin

- [Migrations SQL](../../features/migrations.md)
- [Référence HTTP (Request / Response)](../../reference/http.md)
- [Catalogue complet des starters](../index.md)
