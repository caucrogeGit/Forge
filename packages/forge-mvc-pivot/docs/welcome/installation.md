# Installation : Progression « Bonjour Forge Pivot »

Ce préambule installe le module **opt-in** `forge-mvc-pivot` dans un projet
Forge existant. La progression se réalise ensuite **à la main** : chaque palier
décrit les fichiers à créer et le code à écrire.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir [Installer Forge](../../install/poste-linux.md).
    Pour la référence du module, voir [Tables pivot enrichies](../reference.md).

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/poste-linux.md).
- **Python 3.12+**.
- Aucune base de données pour ce parcours : les opérations sur la base sont démontrées
  via un **exécuteur injecté** de démonstration. Une vraie application crée la table
  pivot et passe `core.database.db.execute` / `fetch_all` / `fetch_one`.

## 1. Installer le module opt-in Pivot

`forge-mvc-pivot` est **publié sur PyPI** :

```bash
pip install --pre forge-mvc-pivot
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-pivot
```

Aucun starter n'est généré : les fichiers du parcours se créent à la main au
fil des paliers.

## 3. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` détecte la dépendance Pivot.

## Après l'installation

Vous pouvez attaquer le premier palier, où vous découvrirez **pourquoi** un pivot
enrichi diffère d'un `many_to_many` ordinaire.

[Continuer avec Bonjour Forge Pivot](debutant/pivot-welcome.md)
