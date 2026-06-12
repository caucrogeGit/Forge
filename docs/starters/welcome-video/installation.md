# Installation — Progression « Bonjour Forge Vidéo »

Ce préambule installe le module **opt-in** `forge-mvc-video` et génère le projet
de départ de la progression vidéo. C'est la **seule page du parcours** qui
contient des commandes de création : tous les paliers suivants supposent le
projet **déjà créé**.

!!! info "Référence complète"
    Pour l'installation détaillée du core et des autres parcours, voir
    [Installer Forge](../../install/poste-linux.md).

## Prérequis

- **Forge installé** (core `forge-mvc`). Si ce n'est pas encore fait, suivre
  d'abord [Installer Forge](../../install/poste-linux.md).
- **Python 3.12+**.
- **`ffmpeg` / `ffprobe` ne sont pas nécessaires au début** : les premiers
  paliers (premier contact, liste, détail, upload) fonctionnent sans eux.
  Ils ne sont requis qu'au niveau avancé (sonder et transcoder une vidéo).

## 1. Installer le module opt-in Vidéo

Le cœur de Forge ne dépend pas de la vidéo : c'est une brique que l'on ajoute à
la demande. Installation directe depuis PyPI (`forge-mvc-video` est publié
depuis `1.0.0-beta.13`) :

```bash
pip install --pre forge-mvc-video
```

Équivalent via la CLI Forge depuis un projet existant :

```bash
forge opt-in:install video
```

## 2. Générer le projet de départ

La progression démarre sur le starter `video-welcome` (Bonjour Forge Vidéo) :

```bash
forge starter:build video-welcome
```

## 3. Lancer le projet

```bash
source .venv/bin/activate
forge run
```

Ouvrez `https://localhost:8000/video-welcome` : la page affiche
**« Bonjour Forge Vidéo »**. La route `/video-welcome/inspect` renvoie la
configuration vidéo en JSON, token masqué.

## 4. Vérifier l'installation

```bash
forge video:doctor
```

`forge video:doctor` contrôle de façon non invasive le module (paquet,
configuration, migration, présence de `ffprobe`/`ffmpeg`), sans rien transcoder.

## Après l'installation

Le module répond : vous pouvez attaquer le premier palier de code.

[Continuer avec Bonjour Forge Vidéo](debutant/video-welcome.md)
