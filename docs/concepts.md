# Concepts Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Glossaire des termes utilisés dans le guide, l'architecture des entités et les starter apps.

---

## Modèle canonique

Le modèle canonique est la description de référence d'une entité ou d'une relation. Il vit dans :

```text
mvc/entities/<entity>/<entity>.json
mvc/entities/relations.json
```

Le JSON canonique est la source de vérité : les autres fichiers peuvent être reconstruits depuis lui.

## Projection

Une projection est un fichier technique dérivé du modèle canonique par `forge build:model`. Elle peut être régénérée à tout moment et ne doit pas être modifiée manuellement.

Exemples :

- `contact.sql` — projection SQL locale de l'entité
- `contact_base.py` — projection Python générée
- `relations.sql` — projection SQL globale des relations

## Fichier manuel

Un fichier manuel appartient au développeur. Forge peut le créer s'il est absent, mais ne l'écrase jamais ensuite.

Exemples : `contact.py`, `__init__.py`.

## Relation globale

Une relation globale décrit un lien entre deux entités. Elle ne vit pas dans le JSON local d'une entité, mais dans `mvc/entities/relations.json`. La projection SQL correspondante est `mvc/entities/relations.sql`.

## Pivot explicite

Forge V1 ne fournit pas de `many_to_many` implicite. Un many-to-many se modélise avec une entité pivot normale et deux relations `many_to_one`.

Exemple : `ContactGroupe(id, contact_id, groupe_id)` → `contact_id → Contact.id`, `groupe_id → Groupe.id`.

## SQL visible

Forge ne cache pas le SQL derrière un ORM. Le SQL généré reste lisible, versionnable et vérifiable par le développeur.

## Formulaire Forge

Un formulaire Forge transforme une requête en données validées et erreurs affichables. Il lit les données HTTP, nettoie les champs, remplit `cleaned_data` et expose les erreurs. Il ne fait pas de requête SQL, ne décide pas d'une redirection et ne porte pas de logique métier.

## Modèle applicatif SQL explicite

Un modèle applicatif SQL explicite organise les opérations CRUD d'une ressource sans cacher le SQL. Le contrôleur appelle `ContactModel.create(data)`, mais les requêtes restent visibles dans le fichier modèle.

Ce n'est pas un repository généré automatiquement et ce n'est pas un ORM implicite.

## Formulaire de pivot explicite

Un formulaire de pivot explicite aide à manipuler une sélection liée à une entité pivot. `ContactForm` peut exposer `groupe_ids` via `RelatedIdsField`. Le champ prépare des identifiants validés. Le modèle applicatif SQL reste responsable d'écrire dans la table pivot.

## Régénération

La régénération consiste à relire le JSON canonique pour reconstruire les projections techniques.

```bash
forge sync:entity Contact   # régénère une entité
forge sync:relations        # régénère relations.sql
forge build:model           # régénère tout le modèle
```

## Validation croisée

La validation croisée vérifie que les entités, les champs et les relations sont cohérents entre eux. Exemple : une relation est invalide si elle pointe vers une entité absente ou vers un champ cible qui n'est pas une clé primaire.
