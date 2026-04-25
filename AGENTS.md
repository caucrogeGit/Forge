# AGENTS.md

## Objectif

Tu travailles sur le framework Python Forge.

Avant toute modification, lis obligatoirement :
- `docs/entity_architecture.md`

Cette architecture fait foi pour tout ce qui concerne les entités.

## Règles de travail

- Ne pas réinventer l’architecture des entités.
- Respecter strictement la doctrine définie dans `docs/entity_architecture.md`.
- Ne jamais remplacer cette architecture par un ORM implicite ou une solution magique.
- Séparer strictement :
  - source canonique JSON,
  - SQL généré,
  - base Python générée,
  - classe métier manuelle.
- `contact.py` et `__init__.py` ne doivent jamais être régénérés s’ils existent déjà.
- `*_base.py`, `*.sql` et `relations.sql` sont régénérables.
- Les relations sont globales via `mvc/entities/relations.json` et `mvc/entities/relations.sql`.
- V1 seulement :
  - clé primaire simple,
  - relations `many_to_one`,
  - pas de repository généré,
  - pas de logique métier dans les JSON,
  - pas de valeurs par défaut SQL complexes.

## Convention de nommage

- dossier d'entité : `snake_case`
- table : `snake_case`
- classe entité : `PascalCase`
- champ Python : `snake_case`
- colonne SQL : `PascalCase`

## Validation

- Bloquer toute génération si les JSON sont invalides.
- Les erreurs doivent être explicites et précises.
- Ne jamais générer un modèle incohérent.

## Décorateurs V1

Utiliser uniquement :
- `typed`
- `nullable`
- `not_empty`
- `min_length`
- `max_length`
- `min_value`
- `max_value`
- `pattern`

Ils vivent dans :
- `core/validation/exceptions.py`
- `core/validation/decorators.py`

`ValidationError` est l’exception de validation centrale.

## CLI

L’interface officielle doit être :
- `forge make:entity Contact`
- `forge sync:entity Contact`
- `forge sync:relations`
- `forge build:model`
- `forge db:apply`
- `forge check:model`

Ne pas orienter l’interface utilisateur vers `python3 forge.py ...`.

## Attendu pour chaque tâche

Avant de modifier :
1. lire les fichiers concernés,
2. proposer un plan court,
3. implémenter de manière minimale et cohérente,
4. ne pas toucher aux zones manuelles sans nécessité,
5. vérifier les impacts sur la doctrine.

## Définition de terminé

Une tâche n’est terminée que si :
- l’architecture du document `docs/entity_architecture.md` est respectée,
- les noms sont cohérents,
- la régénération n’écrase pas les fichiers manuels,
- la validation bloque les cas incohérents,
- les fichiers générés suivent la doctrine SQL et Python définie.