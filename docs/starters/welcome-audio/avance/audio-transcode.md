# Transcoder en MP3

Objectif : convertir un fichier audio source en **MP3 standard** avec
`transcode_to_mp3`, via `ffmpeg`.

**Ce que vous allez apprendre :** `transcode_to_mp3(input, output)` lance `ffmpeg`
de façon **synchrone**. Forge Audio reste **sobre** : pas de file de jobs, pas de
table — l'opération attend la fin de `ffmpeg` et lève `FfmpegError` en cas d'échec.

Deuxième palier du **niveau avancé** de la progression audio.

!!! note "Module opt-in — `ffmpeg` requis"
    Ce starter suppose `forge-mvc-audio` installé (palier « Installation ») et le
    binaire `ffmpeg` présent. Sans lui, la page reste **pédagogique**.

## Ce que ce starter montre

- `transcode_to_mp3(input, output)` sur un fichier stocké ;
- l'écriture du MP3 résultant ;
- un repli **pédagogique** si `ffmpeg` est absent.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_audio.transcode_to_mp3` | Transcoder un audio en MP3 via `ffmpeg`. | [Audio](../../../features/media.md) |
| `forge_mvc_audio.FfmpegError` | Erreur si `ffmpeg` échoue. | [Audio](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/audio-transcode`, indiquez l'`original_path` d'un
audio uploadé : un MP3 est écrit dans `transcoded/sortie.mp3`.

## Le contrôleur

```python
# mvc/controllers/audio_transcode_controller.py
import os
from forge_mvc_audio import FfmpegError, load_audio_config, transcode_to_mp3


class AudioTranscodeController(BaseController):

    @staticmethod
    def transcode(request: Request) -> Response:
        rel = request.form("path")
        context = {"csrf_token": BaseController.csrf_token(request)}
        cfg = load_audio_config()
        abs_in = os.path.join(cfg.storage_root, rel)
        abs_out = os.path.join(cfg.storage_root, "transcoded/sortie.mp3")
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        try:
            transcode_to_mp3(abs_in, abs_out, ffmpeg_bin=cfg.ffmpeg_bin)
        except FfmpegError as exc:
            context["error"] = str(exc)
            return BaseController.render("audio_transcode/index.html", context=context, request=request)
        context["output"] = "transcoded/sortie.mp3"
        return BaseController.render("audio_transcode/index.html", context=context, request=request)
```

### Comprendre ce code

- Le transcodage est **synchrone** : la requête HTTP attend `ffmpeg`. En production,
  on le **déporte** hors de la requête (tâche/worker) — le starter le dit
  explicitement.
- Forge Audio est **sans état** : aucun suivi de job, aucune table. Simplicité
  assumée.
- `FfmpegError` (ou binaire absent) → message clair.

## À retenir

- `transcode_to_mp3` convertit via `ffmpeg`, **synchrone** et **sans état**.
- En production, déporter le transcodage hors de la requête HTTP.
- Un échec `ffmpeg` est remonté proprement (`FfmpegError`).

## Après ce starter

Vous transcodez. Dernier palier : diagnostiquer le module.

[Diagnostiquer le module Audio](audio-doctor.md)
