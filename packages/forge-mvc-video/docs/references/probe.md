# Le sondage d'une vidéo dans Forge

Ce document décrit l'extraction des métadonnées vidéo via `ffprobe`.

Le fichier de code correspondant est `forge_mvc_video/probe.py`.

## 1. À quoi sert ce module ?

Le **sondage** lance `ffprobe` (lecture seule) sur une source et en lit les caractéristiques : durée, dimensions, codecs, conteneur.
Il sert aussi de **validation profonde** : un fichier sans flux vidéo, ou que `ffprobe` refuse, est rejeté.

## 2. Sonder une vidéo

```python
from forge_mvc_video.probe import probe_video, VideoProbeError

try:
    meta = probe_video("storage/video/<uuid>.mov")
except VideoProbeError as err:
    return Response.text(str(err), status=400)
```

## 3. Les métadonnées (`VideoMetadata`)

| Attribut | Contenu |
|---|---|
| `duration_seconds` | durée en secondes |
| `width`, `height` | dimensions de l'image |
| `video_codec` | codec vidéo (`h264`…) |
| `audio_codec` | codec audio (`aac`…) |
| `container` | format conteneur (`mp4`, `mov`…) |

Chaque champ vaut `None` si `ffprobe` ne l'a pas fourni.

## 4. La signature

```python
def probe_video(path, *, config=None, runner=None) -> VideoMetadata
```

L'exécution de `ffprobe` est déléguée à un **runner injectable** : le parsing est testable sans `ffprobe` réel.
`parse_probe_json(payload)` transforme une sortie `ffprobe -print_format json` en `VideoMetadata`, sans rien exécuter.

## 5. La validation profonde

`probe_video` rejette une source sans flux vidéo, ou dont la durée dépasse `max_duration_seconds`, en levant `VideoProbeError`.

## 6. Contextes d'utilisation

- **Après ingestion** : valider la source avant de transcoder.
- **Tests** : injecter un `runner` renvoyant une sortie figée.

## 7. Voir aussi

- [L'ingestion](ingest.md) : l'étape précédente.
- [Le transcodage](transcode.md) : l'étape suivante.
- [La configuration](config.md) : `ffprobe_bin`, `max_duration_seconds`.
