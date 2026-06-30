# Aide-mémoire de la progression Vidéo

Récapitulatif des paliers de la progression *Welcome Vidéo* et des API du
module opt-in `forge-mvc-video` introduites à chaque étape.

!!! note "Module opt-in"
    Toute cette progression suppose `forge-mvc-video` installé
    (`forge opt-in:install video`). Le cœur de Forge reste autonome.

## Niveau débutant : découvrir (lecture, sans ffmpeg)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Welcome Vidéo](debutant/video-welcome.md) | Vérifier le module, inspecter la config (secret masqué) | `load_video_config` |
| 2 | [Lister les vidéos](debutant/video-list.md) | Lire les dernières vidéos, rester pédagogique si la table manque | `VideoRepository.list_recent` |
| 3 | [Le détail d'une vidéo](debutant/video-detail.md) | Cibler une vidéo par UUID (trouvée / `404` / `503`) | `get_by_uuid` |

## Niveau intermédiaire : alimenter & exposer (sans transcodage)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Téléverser une vidéo](intermediaire/video-upload.md) | Ingérer un fichier sans ffmpeg (statut `uploaded`) | `ingest_video`, `insert_uploaded` |
| 2 | [Lire une vidéo](intermediaire/video-playback.md) | Servir une vidéo en streaming Range | `register_video_routes` |
| 3 | [Suivre l'état d'une vidéo](intermediaire/video-status.md) | Observer le cycle de vie par statut | `list_by_status` |

## Niveau avancé : transcodage réel (ffmpeg requis)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Sonder une vidéo](avance/video-probe.md) | Extraire les métadonnées d'une source (ffprobe) | `probe_video` |
| 2 | [Transcoder une vidéo](avance/video-transcode.md) | Worker de transcodage MP4 (ffmpeg) | `forge video:process`, `process_video` |
| 3 | [Diagnostiquer le module Vidéo](avance/video-doctor.md) | Vérifier la santé du module (dont ffprobe/ffmpeg) | `forge video:doctor`, contrôles non invasifs |

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
| `repo.list_by_status(status, limit=…)` | Vidéos d'un statut du cycle de vie |
| `ingest_video(data, filename, title=…)` | Valider, stocker (UUID) et enregistrer une vidéo (sans ffmpeg) |

## Lecture HTTP officielle (`forge_mvc_video`)

| Élément | Usage |
|---------|-------|
| `register_video_routes(router)` | Brancher `GET /videos/{uuid}` (streaming Range) |

## Transcodage & diagnostic (ffmpeg)

| Élément | Usage |
|---------|-------|
| `probe_video(path, config=…)` | Sonder une source (ffprobe) → métadonnées |
| `forge video:process <id>` / `--pending` (`process_video`) | Worker : transcoder en MP4 (ffmpeg), avancer le statut |
| `forge video:doctor` | Diagnostic complet (paquet, config, migration, ffprobe, ffmpeg) |
| `check_package_importable` / `check_config_loadable` / `check_migration_present` / `check_ffprobe_present` / `check_ffmpeg_present` | Contrôles de diagnostic non invasifs, réutilisables en app |
