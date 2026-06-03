# Sonder une vidéo

Objectif : extraire les **métadonnées** d'une vidéo uploadée avec ffprobe.

**Ce que vous allez apprendre :** `probe_video`. La fonction lance **ffprobe**
(lecture seule) sur le fichier d'origine d'une vidéo et en extrait durée,
dimensions, codecs et conteneur. C'est l'étape qui **précède le transcodage** :
on inspecte la source avant de la convertir.

Premier palier du **niveau avancé** de la progression vidéo — la bascule vers le
**transcodage réel**. Après le [niveau intermédiaire](../intermediaire/bilan.md).

!!! note "ffprobe requis"
    Ce palier exécute **ffprobe**. Installez ffmpeg/ffprobe et renseignez au
    besoin `FORGE_VIDEO_FFPROBE_BIN`. ffprobe **lit** la source ; il ne
    transcode pas.

## Ce que ce starter montre

- la sonde d'un fichier via `probe_video` (ffprobe, lecture seule) ;
- l'extraction de `duration_seconds`, `width`, `height`, `video_codec`,
  `audio_codec`, `container` ;
- des réponses pédagogiques : `404` (UUID inconnu), `502` (sonde échouée).

La table `videos` est garantie par la migration livrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `VideoRepository.get_by_uuid` | Retrouver le chemin du fichier d'origine. | [Parcours vidéo](../../../video/parcours.md) |
| `forge_mvc_video.probe.probe_video` | Lancer ffprobe et extraire les métadonnées. | [Parcours vidéo](../../../video/parcours.md) |
| `VideoProbeError` | Sonde échouée (source illisible / non vidéo). | [Parcours vidéo](../../../video/parcours.md) |

## Tester

```bash
forge db:init
forge run
```

Avec une vidéo uploadée (niveau intermédiaire) et ffprobe installé, ouvrez
`https://localhost:8000/video-probe/<uuid>` : la réponse JSON donne les
métadonnées extraites du fichier.

## Le contrôleur

```python
# mvc/controllers/video_probe_controller.py
from pathlib import Path
from forge_mvc_video.config import load_video_config
from forge_mvc_video.probe import VideoProbeError, probe_video
from forge_mvc_video.storage.repository import VideoRepository


class VideoProbeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        uuid = request.route_param("uuid")
        video = VideoRepository().get_by_uuid(uuid)
        if video is None:
            return Response.json({"error": "video_not_found", "uuid": uuid}, status=404)
        cfg = load_video_config()
        path = str(Path(cfg.storage_root) / video["original_path"])
        try:
            meta = probe_video(path, config=cfg)
        except VideoProbeError as exc:
            return Response.json({"error": "probe_failed", "message": str(exc)}, status=502)
        return Response.json({"uuid": uuid, "metadata": {
            "duration_seconds": meta.duration_seconds, "width": meta.width, "height": meta.height,
            "video_codec": meta.video_codec, "audio_codec": meta.audio_codec, "container": meta.container,
        }})
```

### Comprendre ce code

- On retrouve le **chemin** du fichier via la ligne `videos` (`original_path`,
  relatif à `storage_root`) — jamais un chemin fourni par le client.
- `probe_video(path, config=cfg)` exécute ffprobe en **lecture seule** : il
  n'altère pas le fichier. Une `VideoProbeError` (source illisible, pas une vidéo)
  devient un `502` clair.
- C'est l'inspection préalable : le transcodage proprement dit vient au palier
  suivant.

## À retenir

- `probe_video` lance ffprobe (lecture seule) et extrait les métadonnées.
- On sonde la source à partir de son chemin **stocké**, pas d'une entrée client.
- La sonde précède le transcodage : on inspecte avant de convertir.

## Après ce starter

Vous savez inspecter une source. La suite : la **transcoder** en MP4.

[Transcoder une vidéo](video-transcode.md)
