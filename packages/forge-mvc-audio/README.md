# forge-mvc-audio

Module **opt-in** Forge pour la gestion audio : upload, sondage de métadonnées,
transcodage MP3 et lecture en streaming. **Sans état** (aucune base de données).

## Un opt-in officiel

Cet opt-in **suit la version du cœur** de Forge et n'a pas de cycle de maturité
propre : sa version est celle du `pyproject.toml` racine (`OPTINS-MATURITY-FOLLOWS-CORE-001`).

`forge-mvc-audio` fournit une chaîne audio complète et **sobre**, calquée sur
`forge-mvc-video` mais **sans la machinerie à état** (pas de table SQL, pas de
suivi de jobs, pas de file de transcodage). C'est un choix délibéré : les
opérations audio sont synchrones et la lecture retrouve les fichiers par `uuid`
sur le disque.

> **ffmpeg / ffprobe** sont des binaires **système** (pas des dépendances pip).
> Le module se branche sans eux (le service de lecture fonctionne), mais le
> sondage exige `ffprobe` et le transcodage exige `ffmpeg`.
> `forge audio:doctor` signale leur absence.

Installation (mode éditable depuis les sources) :

```bash
pip install -e packages/forge-mvc-audio/
```

## Ce que contient le module

- `config` — `AudioConfig` + `load_audio_config()` (configuration depuis
  `FORGE_AUDIO_*`, valeurs par défaut sûres).
- `storage` — disposition **uuid-based** des fichiers (le nom utilisateur
  n'apparaît jamais dans le chemin → anti-traversal par construction).
- `probe` — `probe_audio()` via `ffprobe` : durée, codec, bitrate, sample rate,
  nombre de canaux, conteneur. Sert aussi de validation profonde (rejet d'un
  fichier sans flux audio).
- `ingest` — `ingest_audio(data, filename)` : valide (taille, extension), stocke
  la source, retourne un enregistrement (`uuid`, chemin, taille, MIME).
- `transcode` — `transcode_to_mp3()` via `ffmpeg` (profil MP3 192 kbps, stéréo,
  métadonnées d'origine retirées). Constructeurs de commande **purs**, runner
  injectable (testable sans ffmpeg).
- `http` — `register_audio_routes(router)` : route `GET /audio/{uuid}` servie en
  **streaming HTTP Range** (seek), Bearer token optionnel
  (`FORGE_AUDIO_API_TOKEN`).
- `cli.doctor` — `forge audio:doctor` : diagnostic statique (package, config,
  ffprobe, ffmpeg, routes).

## Formats acceptés à l'upload

`mp3`, `wav`, `ogg`, `flac`, `m4a`, `aac`. La sortie de transcodage est MP3.

## Sécurité

- Invocation `ffmpeg`/`ffprobe` en **liste d'arguments** (jamais `shell=True`).
- Chemins **uuid-based** : le `uuid` de l'URL n'est qu'une clé de lookup, validée
  comme un UUID — aucun *path traversal*.
- Token Bearer optionnel sur la route de lecture (mode local ouvert par défaut).
- L'auth vit dans ce module, **jamais** dans Forge Core.

## Configuration (`FORGE_AUDIO_*`)

| Variable | Défaut | Rôle |
|---|---|---|
| `FORGE_AUDIO_FFMPEG_BIN` | `ffmpeg` | binaire ffmpeg |
| `FORGE_AUDIO_FFPROBE_BIN` | `ffprobe` | binaire ffprobe |
| `FORGE_AUDIO_STORAGE_ROOT` | `storage/audio` | racine de stockage |
| `FORGE_AUDIO_MAX_UPLOAD_MB` | `200` | taille max d'upload |
| `FORGE_AUDIO_MAX_DURATION_SECONDS` | `7200` | durée max (2 h) |
| `FORGE_AUDIO_API_TOKEN` | *(absent)* | Bearer token de lecture (optionnel) |
