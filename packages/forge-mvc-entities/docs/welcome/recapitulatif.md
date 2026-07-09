# Aide-mémoire de la progression Entités

Récapitulatif des paliers de la progression *Welcome Entités* et des commandes ou API du moteur d'entités (`forge-mvc-entities`) introduites à chaque étape.

!!! note "Moteur à SQL visible"
    `forge-mvc-entities` est l'opt-in du moteur d'entités, à installer explicitement (`pip install --pre forge-mvc-entities`), au même titre que le backend.
    Le contrat JSON est la source unique ; le SQL et le modèle en sont des projections **lisibles** (charte principe 5), aucun ORM.

## Niveau débutant : modéliser et générer

| # | Palier | Ce qu'on apprend | Commande / API-clé |
|---|--------|------------------|---------|
| 1 | [Welcome Entités](debutant/entity-welcome.md) | Le contrat d'entité, source unique | `mvc/entities/<nom>/<nom>.json` |
| 2 | [Déclarer une entité](debutant/entity-make.md) | Créer et valider un contrat | `make:entity`, `entity:validate` |
| 3 | [Relier deux entités](debutant/relation-make.md) | `many_to_one` + clé étrangère de 1re classe | `make:relation`, type `foreign_key` |
| 4 | [Générer le SQL et le modèle](debutant/build-model.md) | Dériver les projections du contrat | `build:model`, `check:model` |
| 5 | [Générer le CRUD](debutant/crud-make.md) | Échafauder les écrans d'une entité | `make:crud` |

## Niveau intermédiaire : faire évoluer

| # | Palier | Ce qu'on apprend | Commande / API-clé |
|---|--------|------------------|---------|
| 1 | [Les migrations](intermediaire/migrations.md) | Provisionner et faire évoluer le schéma | `db:init`, `migration:make`, `migration:apply`, `migration:status` |

## Niveau avancé : le pivot enrichi

| # | Palier | Ce qu'on apprend | Commande / API-clé |
|---|--------|------------------|---------|
| 1 | [Le pivot enrichi](avance/pivot-welcome.md) | Pivot ordinaire vs enrichi, construire le service | `PivotAdvancedService` |
| 2 | [Générer le sous-CRUD](avance/pivot-make.md) | Produire le sous-CRUD pivot | `make:pivot-crud`, `--dry-run` |
| 3 | [Le schéma SQL](avance/pivot-schema.md) | Clés composites + colonnes d'attributs | `CREATE TABLE article_tag` |
| 4 | [Attacher une association](avance/pivot-attach.md) | Créer une association avec attributs | `attach` |
| 5 | [Modifier et détacher](avance/pivot-update.md) | Mettre à jour / supprimer | `update`, `detach` |
| 6 | [Lister les associations](avance/pivot-list.md) | Lire les `PivotRow` d'une source | `list_for_source`, `PivotRow` |
| 7 | [Contraintes de champ](avance/pivot-constraints.md) | Champs requis / non nullables | `PivotFieldConstraint`, `PivotConstraintError` |
| 8 | [Unicité de la paire](avance/pivot-unique.md) | Refuser un doublon avant l'`INSERT` | `unique_pair`, `get` |
| 9 | [Erreurs de formulaire](avance/pivot-form.md) | Erreur pivot → message de formulaire | `pivot_error_to_form_error`, `PivotFormError` |
