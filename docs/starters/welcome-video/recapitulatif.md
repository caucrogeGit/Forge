# Aide-mémoire de la progression Vidéo

Récapitulatif des paliers de la progression *Bonjour Forge Vidéo* et des API du
module opt-in `forge-mvc-video` introduites à chaque étape.

!!! note "Module opt-in"
    Toute cette progression suppose `forge-mvc-video` installé
    (`forge opt-in:install video`). Le cœur de Forge reste autonome.

## Niveau débutant — découvrir (lecture, sans ffmpeg)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge Vidéo](debutant/video-welcome.md) | Vérifier le module, inspecter la config (secret masqué) | `load_video_config` |

## Configuration (`forge_mvc_video.config`)

| Élément | Usage |
|---------|-------|
| `load_video_config()` | Lire la configuration vidéo (binaires ffmpeg/ffprobe, racine de stockage, limites, token API) |

Un secret (token) est **toujours masqué** quand la config est sérialisée.
