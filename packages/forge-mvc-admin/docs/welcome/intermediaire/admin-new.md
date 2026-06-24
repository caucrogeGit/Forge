# Intermédiaire 2 — Créer une ligne

Objectif : ajouter un article depuis le back-office.

## Le formulaire de création

La fiche et la liste mènent à `/admin/articles/new`.
La page affiche un formulaire avec un champ par colonne de `form_fields`.

Le formulaire est protégé contre la falsification de requête (CSRF) : un jeton
caché est inséré automatiquement et vérifié à la soumission.

## Ce qui est écrit

À la soumission (`POST /admin/articles/new`), seules les colonnes de
`form_fields` sont insérées :

```sql
INSERT INTO articles (title, body) VALUES (?, ?)
```

Les valeurs passent par des paramètres.
Une valeur laissée vide est enregistrée comme `NULL`.
Aucune autre colonne ne peut être écrite : c'est une liste blanche.

En cas de succès, le back-office redirige vers la fiche de la ligne créée et
affiche un message de confirmation.

## Limite à connaître

À ce stade, il n'y a pas de validation par champ dans le back-office.
Les contraintes (obligatoire, type) sont celles de la base de données.
Une contrainte violée produit une erreur ; ajustez la saisie en conséquence.

## À retenir

- Seules les colonnes déclarées sont écrites, en requête paramétrée.
- Le jeton CSRF protège la soumission.

## Étape suivante

[Suivant : éditer](admin-edit.md)
