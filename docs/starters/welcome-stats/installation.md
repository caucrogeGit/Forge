# Installation — Progression « Bonjour Forge Stats »

Ce préambule installe le module **opt-in** `forge-mvc-stats` et génère le projet de
départ. C'est la **seule page du parcours** qui contient des commandes de création :
tous les paliers suivants supposent le projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir [Installer Forge](../../install/poste-linux.md).

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/poste-linux.md).
- **Python 3.12+**.
- Aucune base de données pour ce parcours : les opérations sur la base sont démontrées
  via un **exécuteur injecté** de démonstration. Une vraie application crée la table
  `forge_stats_events` et passe `core.database.db.execute` / `fetch_all`.

## 1. Installer le module opt-in Stats

`forge-mvc-stats` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-stats
```

## 2. Générer le projet de départ

```bash
forge starter:build stats-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/stats-welcome` : la page affiche
**« Bonjour Forge Stats »**. `/stats-welcome/inspect` montre la table, les colonnes et
un événement de démo.

## 4. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance Stats.

## Après l'installation

[Continuer avec Bonjour Forge Stats](debutant/stats-welcome.md)
