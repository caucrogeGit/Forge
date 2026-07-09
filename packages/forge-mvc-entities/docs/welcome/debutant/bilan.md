# Bilan : niveau débutant (Entités)

Récapitulatif du **niveau débutant** de la progression *Welcome Entités*.
Ce niveau pose toute la chaîne de base : déclarer, relier, générer le modèle, générer le CRUD.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Welcome Entités](entity-welcome.md) | Comprendre le contrat d'entité, source unique de la couche de données. |
| 2 : [Déclarer une entité](entity-make.md) | Créer et compléter un contrat avec `make:entity`, valider avec `entity:validate`. |
| 3 : [Relier deux entités](relation-make.md) | Déclarer un `many_to_one` avec `make:relation` ; la clé étrangère devient un champ `foreign_key`. |
| 4 : [Générer le SQL et le modèle](build-model.md) | Dériver le SQL et le modèle depuis les contrats avec `build:model`. |
| 5 : [Générer le CRUD](crud-make.md) | Échafauder les écrans complets d'une entité avec `make:crud`. |

Vous savez modéliser une couche de données à SQL visible et en générer l'interface.

## Et ensuite

Place au niveau **intermédiaire** : faire **évoluer** le schéma dans le temps avec les migrations.

[Niveau intermédiaire : les migrations](../intermediaire/migrations.md)
