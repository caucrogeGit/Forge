# Bilan : niveau avancé (Entités)

Récapitulatif du **niveau avancé** de la progression *Welcome Entités* : le pivot enrichi.
Ce niveau modélise une relation `many_to_many` qui porte ses propres attributs, avec intégrité et UX.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Le pivot enrichi](pivot-welcome.md) | Distinguer pivot ordinaire et pivot enrichi ; construire un `PivotAdvancedService`. |
| 2 : [Générer le sous-CRUD pivot](pivot-make.md) | Produire le sous-CRUD avec `make:pivot-crud` (et `--dry-run`). |
| 3 : [Le schéma SQL du pivot](pivot-schema.md) | Lire la table : clés composites + colonnes d'attributs. |
| 4 : [Attacher une association](pivot-attach.md) | Créer une association avec attributs (`attach`). |
| 5 : [Modifier et détacher](pivot-update.md) | Mettre à jour (`update`) et supprimer (`detach`). |
| 6 : [Lister les associations](pivot-list.md) | Lire les `PivotRow` d'une source (`list_for_source`). |
| 7 : [Contraintes de champ](pivot-constraints.md) | Déclarer `required`/`nullable` (`PivotFieldConstraint`). |
| 8 : [Unicité de la paire](pivot-unique.md) | Refuser un doublon avant l'`INSERT` (`unique_pair`). |
| 9 : [Erreurs de formulaire](pivot-form.md) | Traduire une erreur en `PivotFormError` affichable. |

Vous maîtrisez le pivot enrichi : modèle, manipulation, intégrité et UX.

## Progression terminée

Vous avez parcouru tout le moteur d'entités : déclarer et relier des entités, générer leur modèle et leur CRUD, faire évoluer le schéma par migrations, et modéliser une relation qui porte sa propre donnée.

Consultez l'**aide-mémoire** pour retrouver d'un coup d'œil chaque palier et son API.

[Aide-mémoire de la progression Entités](../recapitulatif.md)
