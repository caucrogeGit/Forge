# Débutant 3 — La liste paginée

Objectif : consulter les lignes de l'entité depuis le back-office.

## Ouvrir la liste

Depuis le tableau de bord, la ressource « Articles » mène à `/admin/articles`.

La page affiche un tableau :

- une colonne par champ de `list_fields` ;
- une ligne par enregistrement ;
- une pagination en bas (page courante, précédent, suivant).

## Comment la liste lit la base

La liste construit une requête contrainte à partir de votre déclaration :

```sql
SELECT title, published_at FROM articles ORDER BY title ASC LIMIT ? OFFSET ?
```

Seules les colonnes déclarées entrent dans la requête.
Les bornes de pagination passent par des paramètres.
Il n'y a pas d'ORM ni d'introspection : le SQL reste lisible et prévisible.

## Choisir le tri

Par défaut, la liste trie sur le premier champ de `list_fields`.
Pour trier sur une autre colonne, ajoutez `order_by` à la ressource :

```python
registry.register(AdminResource(
    entity="Article",
    slug="articles",
    label="Article",
    plural_label="Articles",
    list_fields=("title", "published_at"),
    form_fields=("title", "body"),
    table="articles",
    order_by="published_at",
))
```

## À retenir

- La liste est paginée et triée, à partir de votre seule déclaration.
- Le SQL est contraint : colonnes en liste blanche, valeurs paramétrées.

## Étape suivante

[Bilan du niveau débutant](bilan.md)
