# Concepts Forge

Cette page définit les mots importants de Forge. Elle sert de glossaire court pour lire le guide, le starter app et l'architecture des entités.

## Modèle canonique

Le modèle canonique est la description de référence d'une entité ou d'une relation.

Dans Forge, il vit dans :

```text
mvc/entities/<entity>/<entity>.json
mvc/entities/relations.json
```

Le JSON n'est pas un fichier secondaire : c'est la source de vérité du modèle.

## Source de vérité

Une source de vérité est le fichier à partir duquel les autres fichiers peuvent être reconstruits.

Pour une entité, la source de vérité est le JSON canonique. Le SQL et la base Python sont des projections générées.

## Projection

Une projection est une représentation technique dérivée du modèle canonique.

Exemples :

- `contact.sql` est une projection SQL locale ;
- `contact_base.py` est une projection Python générée ;
- `relations.sql` est une projection SQL globale des relations.

## Fichier généré

Un fichier généré peut être recréé par Forge.

Exemples :

- `contact.sql` ;
- `contact_base.py` ;
- `relations.sql`.

Un fichier généré ne doit pas être modifié manuellement en usage normal.

## Fichier manuel

Un fichier manuel appartient au développeur.

Exemple :

```text
mvc/entities/contact/contact.py
```

Forge peut le créer s'il est absent, mais ne l'écrase pas ensuite.

## Fichier protégé

Un fichier protégé peut être créé par Forge, mais ne doit pas être écrasé automatiquement s'il existe déjà.

Exemples :

- `contact.py` ;
- `__init__.py`.

## Relation globale

Une relation globale décrit un lien entre deux entités.

Elle ne vit pas dans le JSON local d'une entité, mais dans :

```text
mvc/entities/relations.json
```

La projection SQL correspondante est :

```text
mvc/entities/relations.sql
```

## Pivot explicite

Forge V1 ne fournit pas de `many_to_many` implicite.

Un many-to-many se modélise avec une entité pivot normale.

Exemple :

```text
ContactGroupe
- id
- contact_id
- groupe_id
```

Puis deux relations `many_to_one` :

```text
ContactGroupe.contact_id -> Contact.id
ContactGroupe.groupe_id -> Groupe.id
```

## SQL visible

Forge ne cache pas le SQL derrière un ORM.

Le SQL généré reste lisible, versionnable et vérifiable par le développeur.

## Formulaire Forge

Un formulaire Forge transforme une requête en données validées et erreurs affichables.

Il lit les données HTTP, nettoie ou convertit les champs, remplit `cleaned_data` et expose les erreurs. Il ne fait pas de requête SQL, ne décide pas d'une redirection et ne porte pas de logique métier lourde.

## Modèle applicatif SQL explicite

Un modèle applicatif SQL explicite organise les opérations CRUD d'une ressource sans cacher le SQL.

Le contrôleur peut appeler `ContactModel.create(data)`, mais les requêtes restent visibles dans `mvc/models/sql/<env>/contact_queries.py`.

Ce n'est pas un repository généré automatiquement et ce n'est pas un ORM implicite.

## Formulaire de pivot explicite

Un formulaire de pivot explicite aide à manipuler une sélection liée à une entité pivot normale.

Exemple : `ContactGroupe` reste une entité Forge ordinaire, mais `ContactForm` peut exposer `groupe_ids` avec `RelatedIdsField`.

Le champ prépare des identifiants validés. Le modèle applicatif SQL reste responsable d'écrire dans la table pivot.

## Régénération

La régénération consiste à relire le JSON canonique pour reconstruire les fichiers techniques.

Commandes principales :

```bash
forge sync:entity Contact
forge sync:relations
forge build:model
```

## Validation croisée

La validation croisée vérifie que les entités, les champs et les relations sont cohérents entre eux.

Exemple : une relation est invalide si elle pointe vers une entité absente ou vers un champ cible qui n'est pas une clé primaire.
