# Installation : Progression « Welcome Images »

Ce préambule installe le module **opt-in** `forge-mvc-images` dans un projet Forge existant.
La progression images se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir Installer Forge.

!!! info "Module publié sur PyPI"
    `forge-mvc-images` est publié sur PyPI depuis `1.0.0-beta.13`.
    On l'installe avec `pip install --pre forge-mvc-images` (sa dépendance `forge-mvc-files` est tirée automatiquement).
    L'installation depuis les sources reste possible pour le développement.

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Si ce n'est pas encore fait, suivre d'abord Installer Forge.
- **Python 3.12+**.
- Les premiers paliers (premier contact, dérivation des variantes) fonctionnent **sans base de données**.
  La couche médias en base n'intervient qu'au niveau intermédiaire.

## 1. Installer le module opt-in Images

Le cœur de Forge ne dépend pas de l'image : c'est une brique que l'on ajoute à la demande.
`forge-mvc-images` dépend de `forge-mvc-files` (l'upload générique), tiré automatiquement à l'installation depuis PyPI :

```bash
pip install --pre forge-mvc-images
```

Pour le développement depuis les sources du dépôt :

```bash
pip install -e packages/forge-mvc-files/
pip install -e packages/forge-mvc-images/
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-images
```

Le détail de la création d'un projet est décrit dans Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au fil des paliers.

## 3. Vérifier l'installation

`forge-mvc-images` est une brique **bibliothèque** (pas de CLI dédiée).
On vérifie qu'elle est bien vue par Forge avec :

```bash
forge opt-in:list
```

Le module `images` doit apparaître comme installé.

## Après l'installation

Le module répond : vous pouvez attaquer le premier palier de code, où vous créerez vous-même le contrôleur, la vue et la route `/images-welcome`.

[Continuer sur le starter Welcome Images](debutant/images-welcome.md)
