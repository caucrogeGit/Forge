# La configuration vidéo dans Forge

Ce document décrit la configuration du module vidéo, lue depuis l'environnement.

Le fichier de code correspondant est `forge_mvc_video/config.py`.

## 1. À quoi sert ce module ?

Le module vidéo a besoin de savoir où trouver `ffmpeg`, où ranger les fichiers et quelles limites appliquer.
`VideoConfig` rassemble ces réglages ; il est **pur** (ne lit aucun fichier, ne lance aucun `ffmpeg`).

## 2. L'objet `VideoConfig`

| Attribut | Type | Défaut | Rôle |
|---|---|---|---|
| `ffmpeg_bin` | `str` | `ffmpeg` | binaire de transcodage |
| `ffprobe_bin` | `str` | `ffprobe` | binaire de sondage |
| `storage_root` | `str` | `storage/video` | dossier de stockage |
| `max_upload_mb` | `int` | `1000` | taille maximale d'un upload (Mo) |
| `max_duration_seconds` | `int` | `3600` | durée maximale acceptée (s) |
| `api_token` | `str \| None` | `None` | jeton facultatif protégeant la lecture |

## 3. Charger la configuration

```python
from forge_mvc_video.config import load_video_config

config = load_video_config()
```

`load_video_config(source=None)` lit `os.environ` par défaut ; on peut injecter un mapping pour les tests.
Les réglages se surchargent via les variables `FORGE_VIDEO_*`.

## 4. Le jeton d'API

Si `api_token` est défini, la route de lecture exige `Authorization: Bearer <token>` ; sinon elle est ouverte (mode local).

## 5. Voir aussi

- [L'ingestion](ingest.md) et [le sondage](probe.md) : premiers consommateurs de la configuration.
- [Le transcodage](transcode.md) : utilise `ffmpeg_bin`.
- [Progression pédagogique Vidéo](../welcome/installation.md).
