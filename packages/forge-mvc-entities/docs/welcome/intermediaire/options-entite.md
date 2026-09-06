# Intermédiaire 2 : Horodatages et suppression logique

Objectif : savoir quand une ligne a été écrite, et la retirer sans la perdre.

## Deux options du contrat

Elles se déclarent dans le bloc `options`, et `forge make:entity` les pose avec `--timestamps` et `--soft-delete`.

```json
{
  "schema_version": "1.0",
  "name": "Seance",
  "table": "seance",
  "fields": [
    {"name": "titre", "type": "string", "max_length": 120, "required": true}
  ],
  "options": {"timestamps": true, "soft_delete": true}
}
```

## Ce que les horodatages changent

La table gagne `CreatedAt` et `UpdatedAt`, et le code engendré les remplit lui même.

```sql
INSERT INTO seance (Titre, CreatedAt, UpdatedAt) VALUES (?, ?, ?)
UPDATE seance SET Titre = ?, UpdatedAt = ? WHERE Id = ?
```

Ils n'apparaissent pas dans le formulaire : une date d'écriture saisie à la main ne serait plus une date d'écriture ([ADR-081](../../../adr/081-managed-timestamps.md)).

## Ce que la suppression logique change

La table gagne `DeletedAt`, et la suppression cesse d'en être une.

```sql
DELETE       -> UPDATE seance SET DeletedAt = ? WHERE Id = ?
SELECT_ALL   -> SELECT ... FROM seance WHERE DeletedAt IS NULL ORDER BY Id
```

La ligne quitte les listes et les fiches, et reste en base ([ADR-083](../../../adr/083-soft-delete.md)).

!!! warning "Ce n'est pas une corbeille"
    Forge n'engendre aucun écran de restauration, et aucune purge.

    Une ligne marquée supprimée le reste jusqu'à ce que l'application décide d'en faire quelque chose : la remettre à `NULL`, ou l'effacer pour de bon.

!!! danger "Une contrainte d'unicité ne connaît pas la suppression logique"
    Supprimer logiquement un élève ne libère pas son adresse électronique : la ligne est toujours là, et la contrainte aussi.

    Réinscrire quelqu'un avec la même adresse échouera. C'est une conséquence de la suppression logique, pas un défaut, et elle se décide au moment de choisir l'option.

## À retenir

- `timestamps` remplit `CreatedAt` et `UpdatedAt`, et les tient hors du formulaire.
- `soft_delete` remplace la suppression par un marquage, et filtre les lectures.
- Une contrainte d'unicité continue de compter les lignes marquées supprimées.

## Étape suivante

[Suivant : les champs calculés](champs-calcules.md)
