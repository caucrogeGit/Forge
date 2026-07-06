# Installation : Progression « Welcome Stats »

Ce préambule installe le module **opt-in** `forge-mvc-stats` dans un projet Forge existant.
La progression se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir Installer Forge.

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Sinon, suivre d'abord Installer Forge.
- **Python 3.12+**.
- Aucune base de données pour ce parcours : les opérations sur la base sont démontrées via un **exécuteur injecté** de démonstration.
  Une vraie application crée la table `forge_stats_events` et passe `core.database.db.execute` / `fetch_all`.

## 1. Installer le module opt-in Stats

`forge-mvc-stats` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-stats
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-stats
```

Le détail de la création d'un projet est décrit dans Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au fil des paliers.

## 3. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance Stats.

## Après l'installation

Vous pouvez attaquer le premier palier de code, où vous créerez vous-même le contrôleur, la vue et la route `/stats-welcome`.

[Continuer sur le starter Welcome Stats](debutant/stats-welcome.md)
