# Installation — Progression « Bonjour Forge Files »

Ce préambule installe le module **opt-in** `forge-mvc-files` et génère le projet
de départ de la progression files. C'est la **seule page du parcours** qui
contient des commandes de création : tous les paliers suivants supposent le
projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir
    [Installer Forge](../../install/poste-linux.md).

!!! info "Module publié sur PyPI"
    `forge-mvc-files` est publié sur PyPI depuis `1.0.0-beta.13`. On l'installe
    avec `pip install --pre forge-mvc-files`. L'installation depuis les sources
    reste possible pour le développement.

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/poste-linux.md).
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

## 2. Générer le projet de départ

La progression démarre sur le starter `files-welcome` (Bonjour Forge Files) :

```bash
forge starter:build files-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/files-welcome` : la page affiche
**« Bonjour Forge Files »**. La route `/files-welcome/inspect` renvoie la racine
de stockage et la politique d'upload en JSON.

## 4. Vérifier l'installation

`forge-mvc-files` est une brique **bibliothèque** (pas de CLI dédiée). On vérifie
qu'elle est bien vue par Forge avec :

```bash
forge opt-in:list
```

Le module `files` doit apparaître comme installé.

## Après l'installation

[Continuer avec Bonjour Forge Files](debutant/files-welcome.md)
