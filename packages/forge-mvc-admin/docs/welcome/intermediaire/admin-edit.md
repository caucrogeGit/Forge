# Intermédiaire 3 : Éditer une ligne

Objectif : modifier un article existant.

## Le formulaire d'édition

La fiche détail propose un lien « Modifier »
vers `/admin/articles/<id>/edit`.
Le formulaire est pré-rempli avec les valeurs actuelles de la ligne.

Comme la création, il est protégé par un jeton CSRF.

## Ce qui est mis à jour

À la soumission (`POST /admin/articles/<id>/edit`), la ligne est mise à jour :

```sql
UPDATE articles SET title = ?, body = ? WHERE id = ?
```

Mêmes garanties que la création : seules les colonnes de `form_fields` sont écrites, les valeurs passent par des paramètres, et la clé primaire cible la bonne ligne.

En cas de succès, le back-office redirige vers la fiche avec un message de confirmation.

## À retenir

- L'édition réutilise le même formulaire que la création, pré-rempli.
- La mise à jour est contrainte aux colonnes déclarées et ciblée par la clé.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
