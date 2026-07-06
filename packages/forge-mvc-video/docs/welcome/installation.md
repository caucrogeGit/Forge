# Installation : Progression « Welcome Vidéo »

Ce préambule installe le module **opt-in** `forge-mvc-video` dans un projet Forge existant.
La progression vidéo se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir Installer Forge.

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Si ce n'est pas encore fait, suivre d'abord Installer Forge.
- **Python 3.12+**.
- **`ffmpeg` / `ffprobe` ne sont pas nécessaires au début** : les premiers paliers (premier contact, liste, détail, upload) fonctionnent sans eux.
  Ils ne sont requis qu'au niveau avancé (sonder et transcoder une vidéo).

## 1. Installer le module opt-in Vidéo

Le cœur de Forge ne dépend pas de la vidéo : c'est une brique que l'on ajoute à la demande.
Installation directe depuis PyPI (`forge-mvc-video` est publié depuis `1.0.0-beta.13`) :

```bash
pip install --pre forge-mvc-video
```

Équivalent via la CLI Forge depuis un projet existant :

```bash
forge opt-in:install video
```

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-video
```

Le détail de la création d'un projet est décrit dans Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au fil des paliers.

## 3. Vérifier l'installation

```bash
forge video:doctor
```

`forge video:doctor` contrôle de façon non invasive le module (paquet, configuration, migration, présence de `ffprobe`/`ffmpeg`), sans rien transcoder.

## Après l'installation

Le module répond : vous pouvez attaquer le premier palier de code, où vous créerez vous-même le contrôleur, la vue et la route `/video-welcome`.

[Continuer sur le starter Welcome Vidéo](debutant/video-welcome.md)
