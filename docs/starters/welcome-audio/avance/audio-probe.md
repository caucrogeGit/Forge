# Sonder un audio

Objectif : extraire les **métadonnées** d'un fichier audio (durée, codec, bitrate…)
avec `probe_audio`, via `ffprobe`.

**Ce que vous allez apprendre :** `probe_audio(path)` lance `ffprobe` (lecture
seule) et retourne un `AudioMetadata` (durée, codec, bitrate, fréquence, canaux,
conteneur). Il valide aussi que la durée reste sous la limite configurée.

Premier palier du **niveau avancé** de la progression audio.

!!! note "Module opt-in — `ffprobe` requis"
    Ce starter suppose `forge-mvc-audio` installé (palier « Installation ») et le
    binaire `ffprobe` présent. Sans lui, la page reste **pédagogique** (message
    d'erreur clair).

## Ce que ce starter montre

- `probe_audio(path)` sur un fichier stocké ;
- l'affichage des métadonnées (`AudioMetadata`) ;
- un repli **pédagogique** si `ffprobe` est absent ou le flux invalide.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_audio.probe_audio` | Sonder un audio via `ffprobe`, valider durée. | [Audio](../../../features/media.md) |
| `forge_mvc_audio.AudioMetadata` | Métadonnées retournées (durée, codec, bitrate…). | [Audio](../../../features/media.md) |
| `forge_mvc_audio.AudioProbeError` | Erreur si durée trop longue ou flux invalide. | [Audio](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/audio-probe?path=<original_path>` (le chemin renvoyé
à l'upload) : la page affiche durée, codec, bitrate…

## Le contrôleur

```python
# mvc/controllers/audio_probe_controller.py
import os

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio import AudioProbeError, load_audio_config, probe_audio


def _probe_view(rel_path: str) -> dict:
    if not rel_path:
        return {"path": ""}
    cfg = load_audio_config()
    abs_path = os.path.join(cfg.storage_root, rel_path)
    try:
        meta = probe_audio(abs_path)
    except AudioProbeError as exc:
        return {"path": rel_path, "error": str(exc)}
    except Exception as exc:  # ffprobe absent, fichier introuvable…
        return {"path": rel_path, "error": f"Sondage impossible : {exc}"}
    return {
        "path": rel_path,
        "meta": {
            "duration_seconds": meta.duration_seconds,
            "audio_codec": meta.audio_codec,
            "bitrate_kbps": meta.bitrate_kbps,
            "sample_rate_hz": meta.sample_rate_hz,
            "channels": meta.channels,
            "container": meta.container,
        },
    }


class AudioProbeController(BaseController):
    """Starter pédagogique : extraire les métadonnées d'un audio via ffprobe."""

    @staticmethod
    def index(request: Request) -> Response:
        rel = request.query("path") or ""
        return BaseController.render(
            "audio_probe/index.html", context=_probe_view(rel), request=request
        )
```

### Comprendre ce code

- On reconstruit le **chemin absolu** à partir de `storage_root` et du chemin
  relatif renvoyé à l'upload : `probe_audio` lit le fichier réel.
- `ffprobe` est **lecture seule** : aucune transformation, aucune écriture.
- On reste **pédagogique** si `ffprobe` manque (binaire système absent).

## La vue

```html
<!-- mvc/views/audio_probe/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Sonder un audio — Forge</title>
</head>
<body>
  <h1>Sonder un audio</h1>

  <form method="get" action="/audio-probe">
    <input type="text" name="path" value="{{ path }}" placeholder="originals/AAAA/MM/uuid/source.mp3" size="50" required>
    <button type="submit">Sonder</button>
  </form>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  {% if meta %}
  <ul>
    <li>Durée : {{ meta.duration_seconds }} s</li>
    <li>Codec : <code>{{ meta.audio_codec }}</code></li>
    <li>Bitrate : {{ meta.bitrate_kbps }} kbps</li>
    <li>Fréquence : {{ meta.sample_rate_hz }} Hz</li>
    <li>Canaux : {{ meta.channels }}</li>
    <li>Conteneur : <code>{{ meta.container }}</code></li>
  </ul>
  {% endif %}

  <p>Le chemin est celui renvoyé par le palier « Téléverser un audio »
  (<code>original_path</code>), relatif au stockage audio.</p>
</body>
</html>
```

## La route

Déclarez la route dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.audio_probe_controller import AudioProbeController

with router.group("", public=True) as public:
    public.add("GET", "/audio-probe", AudioProbeController.index, name="audio_probe_index")
```

## À retenir

- `probe_audio` extrait les métadonnées via `ffprobe`, sans rien modifier.
- La durée est validée contre la limite configurée.
- Un binaire système absent → message clair, pas un plantage.

## Après ce starter

Vous lisez les métadonnées. La suite : transcoder en MP3.

[Transcoder en MP3](audio-transcode.md)
