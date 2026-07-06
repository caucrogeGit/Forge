# Installation : Progression « Welcome Audio »

Ce préambule installe le module **opt-in** `forge-mvc-audio` dans un projet Forge existant.
La progression audio se réalise ensuite **à la main** : chaque palier décrit les fichiers à créer et la route à câbler.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir Installer Forge.

!!! info "Module publié sur PyPI"
    `forge-mvc-audio` est publié sur PyPI depuis `1.0.0-beta.13`.
    On l'installe avec `pip install --pre forge-mvc-audio`.
    L'installation depuis les sources reste possible pour le développement.

## Prérequis

- **Forge installé** (core `forge-mvc`).
  Sinon, suivre d'abord Installer Forge.
- **Python 3.12+**.
- **`ffprobe` / `ffmpeg`** (binaires système, **pas** des dépendances pip) : nécessaires au niveau **avancé** (sonder, transcoder).
  Les paliers débutant (premier contact, upload, lecture) fonctionnent **sans** eux.
- Aucune base de données : `forge-mvc-audio` est **sans état**.

## 1. Installer le module opt-in Audio

```bash
pip install --pre forge-mvc-audio
```

Pour le développement depuis les sources : `pip install -e packages/forge-mvc-audio/`.

## 2. Disposer d'un projet Forge

La progression suppose un projet Forge déjà créé.
Si ce n'est pas le cas, créez-en un avec :

```bash
forge new mon-projet-audio
```

Le détail de la création d'un projet est décrit dans Installer Forge.
Aucun starter n'est généré : les fichiers du parcours se créent à la main au fil des paliers.

## 3. Vérifier l'installation

Contrairement à files/images, Audio fournit une **commande de diagnostic** :

```bash
forge audio:doctor
```

Elle contrôle le paquet, la configuration et la présence de `ffprobe`/`ffmpeg`.

## Après l'installation

Vous pouvez attaquer le premier palier de code, où vous créerez vous-même le contrôleur, la vue et la route `/audio-welcome`.

[Continuer sur le starter Welcome Audio](debutant/audio-welcome.md)
