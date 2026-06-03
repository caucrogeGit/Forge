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
| 2 | [Lister les vidéos](debutant/video-list.md) | Lire les dernières vidéos, rester pédagogique si la table manque | `VideoRepository.list_recent` |
| 3 | [Le détail d'une vidéo](debutant/video-detail.md) | Cibler une vidéo par UUID (trouvée / `404` / `503`) | `get_by_uuid` |

## Niveau intermédiaire — alimenter & exposer (sans transcodage)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Téléverser une vidéo](intermediaire/video-upload.md) | Ingérer un fichier sans ffmpeg (statut `uploaded`) | `ingest_video`, `insert_uploaded` |

## Configuration (`forge_mvc_video.config`)

| Élément | Usage |
|---------|-------|
| `load_video_config()` | Lire la configuration vidéo (binaires ffmpeg/ffprobe, racine de stockage, limites, token API) |

Un secret (token) est **toujours masqué** quand la config est sérialisée.

## Stockage (`forge_mvc_video.storage.repository`)

| Élément | Usage |
|---------|-------|
| `VideoRepository()` | Accès aux vidéos enregistrées (utilise `core.database.db` par défaut) |
| `repo.list_recent(limit=…)` | Dernières vidéos, ordre du plus récent |
| `repo.get_by_uuid(uuid)` | Une vidéo précise (ou `None`) |
| `ingest_video(data, filename, title=…)` | Valider, stocker (UUID) et enregistrer une vidéo (sans ffmpeg) |
