# Générer le CRUD avec `make:crud`

Objectif : générer les écrans de création, lecture, mise à jour et suppression d'`Article`.

**Ce que vous allez apprendre :** `forge make:crud` échafaude, à partir du contrat, un contrôleur, des vues et un formulaire complets pour une entité.
Les fichiers sont générés une fois ; ils vous appartiennent ensuite.

!!! note "Forge génère, puis se retire"
    `make:crud` crée des fichiers neufs et ne les réécrit pas.
    Le code généré est du code Forge ordinaire, lisible et modifiable : Forge ne reste pas dans votre dos.

## Générer

```bash
forge make:crud Article
```

Forge génère le contrôleur CRUD, les vues (liste, détail, formulaire) et branche les routes correspondantes.

La clé étrangère `auteur_id` est prise en charge naturellement : le formulaire propose un `select` des auteurs, et la persistance inclut la colonne.

## Voir le résultat

```bash
forge run
```

Ouvrez l'écran de liste des articles : vous pouvez créer, éditer et supprimer, avec le lien vers l'auteur.

Le CRUD repose sur le SQL et le modèle générés au palier précédent ; il ne fait que les exploiter.

## Aperçu du flux généré

- **Liste** : lecture paginée des articles.
- **Formulaire** : champs dérivés du contrat, `select` pour la clé étrangère.
- **Détail / suppression** : lecture par `id`, suppression contrôlée.

## Commandes Forge utilisées

| Commande | Rôle dans ce palier | Référence |
|---|---|---|
| `forge make:crud Article` | Générer le CRUD complet de l'entité. | [make:crud](../../modules/make_crud.md) |
| `forge run` | Lancer le serveur de développement. | Cœur Forge |

## La suite

Vous avez parcouru toute la chaîne débutant : déclarer, relier, générer le modèle, générer le CRUD.
Faisons le bilan du niveau débutant.

[Continuer : bilan du niveau débutant](bilan.md)
