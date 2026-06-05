# Installation — Progression « Bonjour Forge Audio »

Ce préambule installe le module **opt-in** `forge-mvc-audio` et génère le projet
de départ de la progression audio. C'est la **seule page du parcours** qui
contient des commandes de création : tous les paliers suivants supposent le
projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core, voir
    [Installer Forge](../../install/index.md).

!!! warning "Module pas encore publié sur PyPI"
    `forge-mvc-audio` n'est pas encore publié sur PyPI (cible : release beta.13).
    On l'installe donc **depuis les sources**. Une fois publié, la commande
    deviendra `pip install --pre forge-mvc-audio`.

## Prérequis

- **Forge installé** (core `forge-mvc`). Sinon, suivre d'abord
  [Installer Forge](../../install/index.md).
- **Python 3.12+**.
- **`ffprobe` / `ffmpeg`** (binaires système, **pas** des dépendances pip) :
  nécessaires au niveau **avancé** (sonder, transcoder). Les paliers débutant
  (premier contact, upload, lecture) fonctionnent **sans** eux.
- Aucune base de données : `forge-mvc-audio` est **sans état**.

## 1. Installer le module opt-in Audio

```bash
pip install -e packages/forge-mvc-audio/
```

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
