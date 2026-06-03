# Forge Video — parcours complet

L'opt-in **`forge-mvc-video`** (Beta) couvre la chaîne vidéo de bout en bout :
**upload → traitement (transcodage MP4) → lecture en streaming HTTP Range**,
plus une purge sûre. Le travail lourd (`ffmpeg`) se fait dans un **worker CLI**,
jamais pendant une requête HTTP.

## Prérequis

- `forge-mvc-video` installé (`pip install --pre forge-mvc-video`) ;
- `ffmpeg` et `ffprobe` disponibles (binaires **système**, pas des dépendances
  pip) — vérifiables avec `forge video:doctor` ;
- une base configurée (`DB_APP_*` dans `env/dev`).

## 1. Diagnostic

```bash
forge video:doctor          # package, config, migration, ffmpeg/ffprobe, routes
```

## 2. Migration `videos`

```bash
forge video:init            # copie la migration vers mvc/migrations/ (idempotent)
forge migration:apply       # crée la table videos
```

`forge migration:apply --dry-run` affiche le SQL sans l'appliquer.

## 3. Upload d'une vidéo

```bash
forge video:upload film.mp4 --title "Conférence 2026"
```

L'upload **valide** (taille ≤ `FORGE_VIDEO_MAX_UPLOAD_MB`, extension dans
`.mp4/.mov/.webm/.mkv`), **stocke** la source à un emplacement *uuid-based*
(anti-traversal : le nom de fichier utilisateur n'est jamais réutilisé comme
chemin) et **insère** une ligne `videos` au statut `uploaded`. Aucun `ffmpeg`
n'est lancé à cette étape. La commande affiche l'`id` et l'`uuid`.

## 4. Traitement (worker)

```bash
forge video:process <id>        # traite une vidéo
forge video:process --pending   # traite toutes les vidéos `uploaded`
```

Le worker sonde la source (`ffprobe` : durée, dimensions, codecs), génère un
**poster** JPG et transcode en **MP4 H.264/AAC** (`ffmpeg`, `+faststart`,
métadonnées supprimées), puis passe la vidéo en `ready`. Une vidéo dont le
traitement échoue passe en `failed` (avec message) sans bloquer les autres.

## 5. Lecture

Branchez la route de lecture via l'opt-in projet :

```bash
forge opt-in:enable video --apply
```

La route `GET /videos/{uuid}` sert le MP4 en **streaming avec support HTTP
Range** (seek), via la primitive core `Response.file`. Le chemin provient de la
base, jamais de l'URL. Si `FORGE_VIDEO_API_TOKEN` est défini, la route exige un
en-tête `Authorization: Bearer <token>`.

## 6. Purge (cleanup)

```bash
forge video:cleanup --failed                 # dry-run : vidéos failed
forge video:cleanup --orphan-files           # dry-run : fichiers non référencés
forge video:cleanup --failed --apply         # supprime réellement
```

`video:cleanup` est **dry-run par défaut** : il liste ce qui *serait* supprimé
sans rien toucher ; `--apply` exécute. Aucune suppression hors de
`storage_root` (anti-traversal).

## Configuration

| Variable | Défaut | Rôle |
|---|---|---|
| `FORGE_VIDEO_FFMPEG_BIN` | `ffmpeg` | Binaire ffmpeg |
| `FORGE_VIDEO_FFPROBE_BIN` | `ffprobe` | Binaire ffprobe |
| `FORGE_VIDEO_STORAGE_ROOT` | `storage/video` | Racine de stockage |
| `FORGE_VIDEO_MAX_UPLOAD_MB` | `1000` | Taille max d'un upload |
| `FORGE_VIDEO_MAX_DURATION_SECONDS` | `3600` | Durée max acceptée |
| `FORGE_VIDEO_API_TOKEN` | *(vide)* | Bearer token de lecture (optionnel) |

## Résumé de la chaîne

```text
video:upload → (uploaded) → video:process → (ready) → GET /videos/{uuid}
                                   │
                                (failed) → video:cleanup --failed
```
