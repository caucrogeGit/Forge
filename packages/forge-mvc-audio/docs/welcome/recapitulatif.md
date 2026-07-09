# Aide-mémoire de la progression Audio

Récapitulatif des paliers de la progression *Welcome Audio* et des API du module opt-in `forge-mvc-audio` introduites à chaque étape.

!!! note "Module opt-in : sans état"
    `forge-mvc-audio` est une chaîne audio **sans base de données** : opérations synchrones, fichiers repérés par **uuid**.
    `ffmpeg`/`ffprobe` sont des binaires système (pas des dépendances pip), requis au niveau avancé.
    Pas encore publié sur PyPI : install depuis les sources.

## Niveau débutant : découvrir, téléverser, lire (sans ffmpeg)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Welcome Audio](debutant/audio-welcome.md) | Inspecter la config, token masqué | `load_audio_config` |
| 2 | [Téléverser un audio](debutant/audio-upload.md) | Valider et stocker en uuid-based | `ingest_audio` |
| 3 | [Lire un audio](debutant/audio-play.md) | Brancher la lecture streaming officielle | `register_audio_routes` |

## Niveau avancé : traiter & diagnostiquer (ffprobe/ffmpeg)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Sonder un audio](avance/audio-probe.md) | Métadonnées via `ffprobe` | `probe_audio`, `AudioMetadata` |
| 2 | [Transcoder en MP3](avance/audio-transcode.md) | Conversion MP3 via `ffmpeg`, synchrone | `transcode_to_mp3` |
| 3 | [Diagnostiquer le module Audio](avance/audio-doctor.md) | Contrôles non invasifs en JSON | `forge audio:doctor`, `check_*` |
