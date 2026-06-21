# Bilan — niveau débutant (Audio)

Récapitulatif du **niveau débutant** de la progression *Bonjour Forge Audio*. Ce
niveau couvre le cycle de base : **découvrir**, **téléverser**, **lire** — sans
`ffmpeg`.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Bonjour Forge Audio](audio-welcome.md) | Inspecter la configuration audio (`load_audio_config`), token masqué. |
| 2 — [Téléverser un audio](audio-upload.md) | Valider et stocker un audio en uuid-based (`ingest_audio`). |
| 3 — [Lire un audio](audio-play.md) | Brancher la lecture streaming officielle (`register_audio_routes`). |

Vous savez ingérer et servir un fichier audio, sans dépendre de `ffmpeg`.

## Et ensuite

Place au niveau **avancé** : sonder les métadonnées (`ffprobe`), transcoder en MP3
(`ffmpeg`) et diagnostiquer le module.

[Niveau avancé : Sonder un audio](../avance/audio-probe.md)
