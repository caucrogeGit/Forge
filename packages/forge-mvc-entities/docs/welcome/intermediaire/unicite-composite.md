# Intermédiaire 4 : L'unicité composite

Objectif : interdire deux fois la même inscription, sans interdire deux inscriptions.

## Une contrainte sur plusieurs colonnes

`unique` sur un champ interdit deux valeurs identiques dans **cette** colonne.
Un élève ne pourrait alors s'inscrire qu'à un seul cours, ce qui n'est pas la règle voulue.

La règle porte sur le **couple**, et se déclare dans `indexes`.

```json
{
  "schema_version": "1.0",
  "name": "Inscription",
  "table": "inscription",
  "fields": [
    {"name": "eleve_id", "type": "integer", "required": true},
    {"name": "cours_id", "type": "integer", "required": true}
  ],
  "indexes": [
    {
      "name": "uq_inscription_eleve_cours",
      "fields": ["eleve_id", "cours_id"],
      "unique": true
    }
  ]
}
```

La table engendrée porte la contrainte :

```sql
CREATE TABLE IF NOT EXISTS inscription (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    EleveId INTEGER NOT NULL,
    CoursId INTEGER NOT NULL,
    UNIQUE (EleveId, CoursId)
);
```

Un même élève peut suivre plusieurs cours, un même cours accueillir plusieurs élèves, et le couple ne peut exister qu'une fois.

!!! info "L'ordre des champs compte"
    `["eleve_id", "cours_id"]` et `["cours_id", "eleve_id"]` interdisent la même chose, mais n'accélèrent pas les mêmes lectures.

    Un index composite sert les recherches qui commencent par sa première colonne : placez en tête celle par laquelle vous interrogez le plus souvent.

!!! warning "Le doublon se rattrape, il ne se prévient pas"
    Vérifier l'absence avant d'insérer laisse une fenêtre entre le contrôle et l'écriture, et deux requêtes simultanées la traversent toutes les deux.

    Le motif portable est d'insérer et de rattraper `UniqueViolationError`, qualifiée sur les quatre backends.

!!! danger "Nommez l'index, ne laissez pas la base le faire"
    Un nom engendré varie d'un moteur à l'autre, et une migration qui doit le retirer ne saura pas comment l'appeler.

## À retenir

- L'unicité d'un couple se déclare dans `indexes`, jamais champ par champ.
- L'ordre des colonnes ne change pas l'interdit, mais change les lectures servies.
- Un doublon se rattrape à l'insertion, il ne se prévient pas par une lecture.

## Étape suivante

[Suivant : la validation métier](validation-metier.md)
