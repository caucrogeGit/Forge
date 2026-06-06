# Installation — Progression « Bonjour Forge Workflow »

Ce préambule installe le module **opt-in** `forge-mvc-workflow` et génère le projet
de départ. C'est la **seule page du parcours** qui contient des commandes de
création : tous les paliers suivants supposent le projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir [Installer Forge](../../install/index.md).

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/index.md).
- **Python 3.12+**.
- Aucune base de données : `forge-mvc-workflow` est **sans état** — il fournit des
  fonctions pures (statuts, transitions, badges). L'application décide où stocker le
  statut courant de ses objets.

## 1. Installer le module opt-in Workflow

`forge-mvc-workflow` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-workflow
```

## 2. Générer le projet de départ

```bash
forge starter:build workflow-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/workflow-welcome` : la page affiche
**« Bonjour Forge Workflow »**. `/workflow-welcome/inspect` montre le jeu de statuts
de démonstration.

## 4. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance Workflow.

## Après l'installation

[Continuer avec Bonjour Forge Workflow](debutant/workflow-welcome.md)
