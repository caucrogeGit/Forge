# Installation : Progression « Welcome Files »

Ce préambule installe le module **opt-in** `forge-mvc-files` dans un projet
Forge existant. La progression files se réalise ensuite **à la main** : chaque
palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir
    Installer Forge.

!!! info "Module publié sur PyPI"
    `forge-mvc-files` est publié sur PyPI depuis `1.0.0-beta.13`. On l'installe
    avec `pip install --pre forge-mvc-files`. L'installation depuis les sources
    reste possible pour le développement.

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  Installer Forge.
- **Python 3.12+**.
- Aucune base de données : `forge-mvc-files` est **sans état** (stockage disque).

## 1. Installer le module opt-in Files

`forge-mvc-files` est le pipeline d'upload générique extrait du core (ADR-019),
la **fondation** sur laquelle `forge-mvc-images` est bâti. Installation depuis
PyPI :

```bash
pip install --pre forge-mvc-files
```

Pour le développement depuis les sources : `pip install -e packages/forge-mvc-files/`.

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-files
```

Le détail de la création d'un projet est décrit dans
Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au
fil des paliers.

## 3. Vérifier l'installation

`forge-mvc-files` est une brique **bibliothèque** (pas de CLI dédiée). On vérifie
qu'elle est bien vue par Forge avec :

```bash
forge opt-in:list
```

Le module `files` doit apparaître comme installé.

## Après l'installation

Vous pouvez attaquer le premier palier de code, où vous créerez vous-même le
contrôleur, la vue et la route `/files-welcome`.

[Continuer sur le starter Welcome Files](debutant/files-welcome.md)
