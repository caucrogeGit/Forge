# Installation — Progression « Bonjour Forge Images »

Ce préambule installe le module **opt-in** `forge-mvc-images` et génère le projet
de départ de la progression images. C'est la **seule page du parcours** qui
contient des commandes de création : tous les paliers suivants supposent le
projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir
    [Installer Forge](../../install/index.md).

!!! info "Module publié sur PyPI"
    `forge-mvc-images` est publié sur PyPI depuis `1.0.0-beta.13`. On l'installe
    avec `pip install --pre forge-mvc-images` (sa dépendance `forge-mvc-files`
    est tirée automatiquement). L'installation depuis les sources reste possible
    pour le développement.

## Prérequis

- **Forge installé** (core `forge-mvc`). Si ce n'est pas encore fait, suivre
  d'abord [Installer Forge](../../install/index.md).
- **Python 3.12+**.
- Les premiers paliers (premier contact, dérivation des variantes) fonctionnent
  **sans base de données**. La couche médias en base n'intervient qu'au niveau
  intermédiaire.

## 1. Installer le module opt-in Images

Le cœur de Forge ne dépend pas de l'image : c'est une brique que l'on ajoute à la
demande. `forge-mvc-images` dépend de `forge-mvc-files` (l'upload générique),
tiré automatiquement à l'installation depuis PyPI :

```bash
pip install --pre forge-mvc-images
```

Pour le développement depuis les sources du dépôt :

```bash
pip install -e packages/forge-mvc-files/
pip install -e packages/forge-mvc-images/
```

## 2. Générer le projet de départ

La progression démarre sur le starter `images-welcome` (Bonjour Forge Images) :

```bash
forge starter:build images-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/images-welcome` : la page affiche
**« Bonjour Forge Images »**. La route `/images-welcome/inspect` renvoie en JSON
les formats acceptés et les tailles de variantes.

## 4. Vérifier l'installation

`forge-mvc-images` est une brique **bibliothèque** (pas de CLI dédiée). On
vérifie qu'elle est bien vue par Forge avec :

```bash
forge opt-in:list
```

Le module `images` doit apparaître comme installé.

## Après l'installation

Le module répond : vous pouvez attaquer le premier palier de code.

[Continuer avec Bonjour Forge Images](debutant/images-welcome.md)
