# Le traitement d'une vidéo dans Forge

Ce document décrit l'orchestration du traitement d'une vidéo : sondage, poster, transcodage.

Le fichier de code correspondant est `forge_mvc_video/process.py`.

## 1. À quoi sert ce module ?

L'ingestion stocke la source ; le **traitement** la transforme.
`process_video` orchestre les étapes : sonder la source, générer le poster, transcoder en MP4, et mettre à jour le statut de la vidéo dans le dépôt.

C'est un **worker** : il est conçu pour tourner en tâche de fond, car le transcodage peut être long.

## 2. Traiter une vidéo

```python
from forge_mvc_video.process import process_video, VideoProcessError

try:
    result = process_video(video_id)
    # {"id": ..., "status": "ready", ...}
except VideoProcessError as err:
    ...
```

## 3. La signature

```python
def process_video(
    video_id: int,
    *,
    config: VideoConfig | None = None,
    repository: VideoRepository | None = None,
    probe_fn=None,
    poster_fn=None,
    transcode_fn=None,
    now: datetime | None = None,
) -> dict[str, Any]
```

Les fonctions `probe_fn`, `poster_fn`, `transcode_fn` sont **injectables** : le worker est testable sans `ffmpeg` réel, en simulant chaque étape.

## 4. Les erreurs

`VideoProcessError` signale une erreur d'**orchestration** (vidéo introuvable, sans source), distincte d'un échec `ffmpeg` (`FfmpegError`).

## 5. Contextes d'utilisation

- **Après ingestion** : déclencher `process_video(video_id)` en tâche de fond.
- **Tests** : injecter `probe_fn` / `transcode_fn` pour piloter chaque étape.

## 6. Voir aussi

- [L'ingestion](ingest.md) : produit la vidéo à traiter.
- [Le transcodage](transcode.md) et [le sondage](probe.md) : les étapes orchestrées.
- [La lecture HTTP](http.md) : sert la vidéo une fois prête.
