# Intermédiaire 1 : La fiche détail

Objectif : consulter une ligne précise.

## Ouvrir une fiche

Une ligne de la liste est accessible à `/admin/articles/<id>`, où `<id>` est la
valeur de la clé primaire.

La fiche affiche les champs de la ligne : la clé primaire, puis les champs de
`list_fields` et de `form_fields`, sans doublon.

## Comment la fiche lit la ligne

La fiche lit une seule ligne par sa clé primaire :

```sql
SELECT id, title, published_at, body FROM articles WHERE id = ? LIMIT 1
```

La valeur de la clé passe par un paramètre.
Si la ligne n'existe pas, le back-office répond par une page « introuvable ».

## La colonne de clé primaire

Par défaut, la clé primaire est `id`.
Si votre table utilise une autre colonne, déclarez-la :

```python
AdminResource(
    entity="Article",
    slug="articles",
    label="Article",
    plural_label="Articles",
    list_fields=("title", "published_at"),
    form_fields=("title", "body"),
    table="articles",
    pk="article_id",
)
```

## À retenir

- La fiche lit une ligne par sa clé primaire, en requête paramétrée.
- `pk` est `id` par défaut, redéclarable.

## Étape suivante

[Suivant : créer](admin-new.md)
