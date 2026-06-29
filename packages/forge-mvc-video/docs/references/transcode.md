# Le transcodage MP4 dans Forge

Ce document décrit le transcodage d'une vidéo en MP4 standard et la génération d'un poster.

Le fichier de code correspondant est `forge_mvc_video/transcode.py`.

## 1. À quoi sert ce module ?

Les sources téléversées ont des formats variés (`mov`, `avi`…), pas toujours lisibles par un navigateur.
Le **transcodage** produit un MP4 standard (H.264/AAC, `faststart`) jouable partout, et extrait un **poster** (image de prévisualisation).

Les constructeurs de commande sont **purs** (testables sans `ffmpeg`) ; seule l'exécution appelle `ffmpeg`.

## 2. Transcoder et extraire un poster

```python
from forge_mvc_video.transcode import transcode_to_mp4, generate_poster, FfmpegError

try:
    transcode_to_mp4("in.mov", "out.mp4")
    generate_poster("in.mov", "poster.jpg", at_seconds=1)
except FfmpegError as err:
    return Response.text(str(err), status=500)
```

## 3. L'API

| Fonction | Comportement |
|---|---|
| `transcode_to_mp4(input_path, output_path, *, ffmpeg_bin="ffmpeg", runner=None, timeout=3600)` | transcode en MP4 H.264/AAC standard |
| `generate_poster(input_path, output_path, *, ffmpeg_bin="ffmpeg", at_seconds=1, runner=None, timeout=60)` | extrait une frame en poster JPG |
| `build_transcode_command(ffmpeg_bin, input_path, output_path)` | la liste d'arguments du transcodage (pure) |
| `build_poster_command(ffmpeg_bin, input_path, output_path, *, at_seconds=1)` | la liste d'arguments du poster (pure) |

## 4. La sécurité d'invocation

Comme pour l'audio : arguments en **liste** (jamais `shell=True`), chemins préfixés `./` s'ils commencent par `-`, `timeout` obligatoire.
`FfmpegError` est levée si `ffmpeg` est absent, dépasse le délai, ou échoue.

## 5. Contextes d'utilisation

- **Worker** : appelé par [le traitement](process.md), souvent en tâche de fond.
- **Tests** : injecter un `runner` simulant le code retour de `ffmpeg`.

## 6. Voir aussi

- [Le traitement](process.md) : orchestre transcodage et poster.
- [Le sondage](probe.md) : la validation qui précède.
- [La configuration](config.md) : `ffmpeg_bin`.
