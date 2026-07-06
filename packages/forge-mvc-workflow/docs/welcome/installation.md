# Installation : Progression « Welcome Workflow »

Ce préambule installe le module **opt-in** `forge-mvc-workflow` dans un projet Forge existant.
La progression se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir Installer Forge.

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Sinon, suivre d'abord Installer Forge.
- **Python 3.12+**.
- Aucune base de données : `forge-mvc-workflow` est **sans état**, il fournit des fonctions pures (statuts, transitions, badges).
  L'application décide où stocker le statut courant de ses objets.

## 1. Installer le module opt-in Workflow

`forge-mvc-workflow` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-workflow
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-workflow
```

Le détail de la création d'un projet est décrit dans Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au fil des paliers.

## 3. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance Workflow.

## Après l'installation

Vous pouvez attaquer le premier palier de code, où vous créerez vous-même le contrôleur, la vue et la route `/workflow-welcome`.

[Continuer sur le starter Welcome Workflow](debutant/workflow-welcome.md)
