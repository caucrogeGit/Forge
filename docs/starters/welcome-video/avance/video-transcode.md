# Transcoder une vidéo

Objectif : transformer une vidéo uploadée en **MP4 lisible**, via le worker de
transcodage.

**Ce que vous allez apprendre :** le modèle **worker-CLI** de Forge Vidéo.
`forge video:process` lance `process_video`, qui sonde la source, génère un
poster et **transcode en MP4 avec ffmpeg**, faisant avancer le statut
`uploaded → processing → ready`. Le transcodage est lourd : il reste un **worker**,
**jamais** une requête HTTP.

Palier 2 du **niveau avancé** de la progression vidéo, après
[Sonder une vidéo](video-probe.md).

!!! note "ffmpeg requis"
    Le transcodage exécute **ffmpeg**. Installez-le et renseignez au besoin
    `FORGE_VIDEO_FFMPEG_BIN`. Le travail lourd se fait en ligne de commande, hors
    du cycle requête/réponse.

## Ce que ce starter montre

- le **worker** `forge video:process` (un identifiant, ou `--pending` pour tout) ;
- l'orchestration `process_video` : sonde + poster + transcodage MP4 ;
- l'avancée du statut `uploaded → processing → ready` (ou `failed`) ;
- une route qui **liste les vidéos en attente** et la config ffmpeg — sans rien
  transcoder elle-même.

La table `videos` est garantie par la migration livrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge video:process` (CLI) | Lancer le worker de transcodage. | [Parcours vidéo](../../../video/parcours.md) |
| `forge_mvc_video.process.process_video` | Orchestrer sonde + poster + transcodage MP4. | [Parcours vidéo](../../../video/parcours.md) |
| `VideoRepository.list_by_status` | Lister les vidéos `uploaded` à traiter. | [Parcours vidéo](../../../video/parcours.md) |

## Tester

```bash
forge db:init
forge run
```

Ouvrez `https://localhost:8000/video-transcode` : la page liste les vidéos au
statut `uploaded` et le binaire ffmpeg configuré. Puis, en ligne de commande
(ffmpeg installé) :

```bash
forge video:process <id>        # traite une vidéo
forge video:process --pending   # traite toutes les vidéos uploaded
```

Les vidéos passent à `ready` et se lisent via `GET /videos/{uuid}`.

## Le contrôleur

```python
# mvc/controllers/video_transcode_controller.py
from forge_mvc_video.config import load_video_config
from forge_mvc_video.storage.repository import VideoRepository


class VideoTranscodeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        cfg = load_video_config()
        try:
            pending = VideoRepository().list_by_status("uploaded", limit=50)
        except Exception:
            pending = []
        return BaseController.render(
            "video_transcode/index.html",
            context={"ffmpeg_bin": cfg.ffmpeg_bin, "pending": pending},
            request=request,
        )
```

### Comprendre ce code

- La route **ne transcode pas** : elle prépare le terrain (liste des vidéos à
  traiter + config). Lancer ffmpeg dans une requête web la bloquerait — c'est
  exactement ce que le modèle worker-CLI **évite**.
- `process_video` (appelé par `forge video:process`) fait le travail lourd
  **hors HTTP** et écrit le résultat (`mp4_path`, `poster_path`, statut `ready`).
- En cas d'échec ffmpeg, la vidéo passe à `failed` avec un `error_message`
  lisible — le diagnostic est le palier suivant.

## À retenir

- Le transcodage est un **worker** (`forge video:process`), jamais une requête web.
- `process_video` orchestre sonde + poster + MP4 et avance le statut.
- Une route web peut **préparer** et **observer**, pas exécuter le travail lourd.

## Après ce starter

Vous savez transcoder. Faites le point dans le bilan du niveau.

[Bilan du niveau avancé](bilan.md)
