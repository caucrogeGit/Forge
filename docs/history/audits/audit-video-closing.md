# Audit de clôture Forge Video

Ticket : `VIDEO-CLOSING-AUDIT-001`. Document **uniquement** : aucun code
fonctionnel ajouté.

## Verdict

Phase **clôturable / clôturée**. L'opt-in `forge-mvc-video` est
fonctionnellement complet pour sa v1 : installer/activer, créer la table,
uploader/stocker, sonder, transcoder en MP4 et lire en streaming (HTTP Range).
La chaîne de bout en bout existe et est testée sans dépendre d'un ffmpeg réel.

## Résumé exécutif

`forge-mvc-video` est un module **opt-in** (charte §8) pour la vidéo
applicative. Il suit le modèle **worker CLI → base → web lit** (comme
`forge-mvc-iot`) : le travail lourd (transcodage) se fait via `forge
video:process`, jamais pendant une requête HTTP.

Le seul ajout au **core** est la primitive HTTP générique
`CORE-HTTP-FILE-RANGE-001` (`Response.file` + HTTP Range), utile au-delà de la
vidéo (exports, pièces jointes).

## Tickets livrés

| Ticket | Commit | Objet |
|---|---|---|
| `CORE-HTTP-FILE-RANGE-001` | `10079b1` | Prérequis core : `Response.file` + Range + corps WSGI itérable (mergé dans `main`) |
| `VIDEO-ROADMAP-OPEN-001` | `4ead6fd` | Squelette du package + `video:doctor` |
| `VIDEO-OPTIN-INTEGRATION-001` | `d1fcc25` | Intégration `opt-in:*` (registry projet multi-opt-in généralisée) |
| `VIDEO-CONFIG-001` | `7e39773` | Table `videos` (migration SQL packagée) |
| `VIDEO-INIT-001` | `7ab35d7` | `forge video:init` (copie la migration) |
| `VIDEO-UPLOAD-STORE-001` | `0015b0d` | Persistance + stockage uuid-based + ingest |
| `VIDEO-PROBE-METADATA-001` | `6231f80` | Extraction métadonnées via ffprobe |
| `VIDEO-PLAYBACK-RANGE-001` | `7f432c2` | Route de lecture `GET /videos/{uuid}` (Range) |
| `VIDEO-FFMPEG-RUNNER-001` | `e4864ce` | Runner ffmpeg sûr (MP4 +faststart, poster) |
| `VIDEO-PROCESS-MP4-001` | `9193125` | Orchestration worker (probe → poster → MP4) |
| `VIDEO-CLI-001` | `807c8df` | `forge video:process <id> \| --pending` |

## Architecture obtenue

- **Opt-in strict** : Forge Core ne dépend pas de `forge-mvc-video` ;
  l'inverse oui (`forge-mvc` → `core.database`, `core.http`). Branchement
  projet explicite via la couche `optins/video/` (aucune découverte).
- **Worker CLI** : `video:process` fait le travail lourd ; le web ne fait que
  lire le résultat (`GET /videos/{uuid}` via `Response.file`).
- **Paliers de dépendance** : Python pur (upload, stockage, lecture) ; ffprobe
  (métadonnées, validation) ; ffmpeg (poster, transcodage). FFmpeg/ffprobe
  sont des **binaires système** (pas des dépendances pip), signalés par
  `video:doctor`.
- **Stockage uuid-based** : le nom de fichier utilisateur n'apparaît jamais
  dans un chemin (anti-traversal par construction).

## Commandes disponibles

- `forge video:doctor` — diagnostic statique (package, config, migration,
  présence ffmpeg/ffprobe, routes).
- `forge video:init` — copie la migration `*_create_videos.sql` vers
  `mvc/migrations/`.
- `forge video:process <id>` / `--pending` — worker de traitement.

Cycle de vie commun aux opt-ins : `forge opt-in:install|enable|disable|list video`.

## Route HTTP disponible

- `GET /videos/{uuid}` — lecture en streaming avec support **HTTP Range**
  (206 Partial Content). Le chemin servi vient de la base (`mp4_path` si
  transcodé, sinon `original_path`), jamais de l'URL. Auth **Bearer
  optionnelle** : si `FORGE_VIDEO_API_TOKEN` est défini, un en-tête
  `Authorization: Bearer <token>` est exigé ; sinon ouvert (mode local).

## Stockage et migrations

- Table `videos` (migration packagée, `CREATE TABLE IF NOT EXISTS`) : `uuid`,
  chemins `original_path`/`mp4_path`/`poster_path`, métadonnées (durée,
  largeur, hauteur, mime, taille), `status`, `error_message`, timestamps.
- Statuts : `uploaded` → `processing` → `ready` / `failed`.
- Disposition disque (sous `FORGE_VIDEO_STORAGE_ROOT`) :
  `originals/<AAAA>/<MM>/<uuid>/source<ext>`, `mp4/.../video.mp4`,
  `posters/.../poster.jpg`.
- SQL appliqué explicitement (`forge video:init` puis `forge migration:apply`).

## ffmpeg, ffprobe et sécurité

- Profil MP4 standard : `libx264 -crf 23` + `aac -b:a 128k -ac 2` +
  `-vf scale='min(1920,iw)':-2` (downscale > 1080p, jamais d'upscale) +
  **`-movflags +faststart`** (MP4 seekable en streaming progressif) +
  `-map_metadata -1`.
- Invocation **sûre** : arguments en liste (jamais `shell=True`), chemins
  uuid-based, `timeout` obligatoire.
- Validation : extension (liste blanche) + taille à l'upload, puis **conteneur
  réel** par ffprobe (rejet si pas de flux vidéo, durée bornée).

## Tests et validations

Toutes les briques externes (DB, ffprobe, ffmpeg, router) sont **injectables**
→ la logique est testée **sans base, sans ffmpeg réel**. Un test
d'intégration ffmpeg réel (skippé si absent) reste à ajouter quand un
environnement avec ffmpeg sera disponible.

## Limites assumées (hors périmètre v1)

Pas de HLS/DASH, pas de live, pas de WebRTC, pas de DRM, pas de 4K imposée,
pas d'AV1, pas de sous-titres avancés, pas de transcodage pendant une requête
HTTP, pas de file de jobs (déclenchement par `video:process`).

## Tickets reportés

- `VIDEO-CLEANUP-001` — `forge video:cleanup` (orphelins / fichiers partiels).
  Reporté : pas encore de suppression ni d'orphelins tant qu'aucune opération
  de delete n'existe.
- Route d'**upload HTTP** (l'ingestion est pour l'instant une fonction Python
  `ingest_video`).
- Test d'**intégration ffmpeg réel** sur clip fixture, gated comme le dogfood
  MariaDB.

## Décision de clôture

La phase Forge Video v1 est **close** : opt-in complet (install/enable/disable),
table, init, upload/stockage, probe, transcodage MP4 (+faststart) et lecture
en streaming Range, le tout fidèle à la charte (opt-in, SQL visible, pas de
magie, sécurité par défaut). Prochaine étape recommandée : test d'intégration
ffmpeg réel, puis `VIDEO-CLEANUP-001`.
