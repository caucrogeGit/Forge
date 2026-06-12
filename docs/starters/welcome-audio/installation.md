# Installation — Progression « Bonjour Forge Audio »

Ce préambule installe le module **opt-in** `forge-mvc-audio` et génère le projet
de départ de la progression audio. C'est la **seule page du parcours** qui
contient des commandes de création : tous les paliers suivants supposent le
projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir
    [Installer Forge](../../install/poste-linux.md).

!!! info "Module publié sur PyPI"
    `forge-mvc-audio` est publié sur PyPI depuis `1.0.0-beta.13`. On l'installe
    avec `pip install --pre forge-mvc-audio`. L'installation depuis les sources
    reste possible pour le développement.

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/poste-linux.md).
- **Python 3.12+**.
- **`ffprobe` / `ffmpeg`** (binaires système, **pas** des dépendances pip) :
  nécessaires au niveau **avancé** (sonder, transcoder). Les paliers débutant
  (premier contact, upload, lecture) fonctionnent **sans** eux.
- Aucune base de données : `forge-mvc-audio` est **sans état**.

## 1. Installer le module opt-in Audio

```bash
pip install --pre forge-mvc-audio
```

Pour le développement depuis les sources : `pip install -e packages/forge-mvc-audio/`.

## 2. Générer le projet de départ

La progression démarre sur le starter `audio-welcome` (Bonjour Forge Audio) :

```bash
forge starter:build audio-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/audio-welcome` : la page affiche
**« Bonjour Forge Audio »**. La route `/audio-welcome/inspect` renvoie la
configuration audio en JSON (token masqué).

## 4. Vérifier l'installation

Contrairement à files/images, Audio fournit une **commande de diagnostic** :

```bash
forge audio:doctor
```

Elle contrôle le paquet, la configuration et la présence de `ffprobe`/`ffmpeg`.

## Après l'installation

[Continuer avec Bonjour Forge Audio](debutant/audio-welcome.md)
