# Welcome Audio

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-audio` avant de commencer : voir sa [référence](../../reference.md).

Objectif : premier contact avec le module **opt-in** `forge-mvc-audio`, une chaîne audio **sans état**.

**Ce que vous allez apprendre :** vérifier que le module répond et **inspecter sa configuration** (`load_audio_config`), à savoir stockage, limites, binaires `ffprobe`/`ffmpeg`, avec le **token masqué**.
Aucune base de données.

Premier palier du **niveau débutant** de la progression audio (vue d'ensemble des starters).

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-audio` installé.
    `ffmpeg`/`ffprobe` sont des binaires système, requis seulement au niveau avancé.
    Le cœur de Forge reste autonome.

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /audio-welcome`) ;
- la lecture de la configuration audio (`load_audio_config`) ;
- sa sérialisation JSON, **token masqué** (`GET /audio-welcome/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_audio.load_audio_config` | Lire la configuration audio (stockage, limites, binaires). | Audio |
| `Response.text` / `Response.json` | Renvoyer du texte puis du JSON. | Response |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/audio-welcome` (« Welcome Audio »), puis `/audio-welcome/inspect` pour la configuration en JSON.

## Le contrôleur

```python
# mvc/controllers/audio_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio import load_audio_config


def _config_to_safe_dict(cfg) -> dict:
    """Sérialise la config audio, token masqué."""
    return {
        "storage_root": cfg.storage_root,
        "max_upload_mb": cfg.max_upload_mb,
        "max_duration_seconds": cfg.max_duration_seconds,
        "ffprobe_bin": cfg.ffprobe_bin,
        "ffmpeg_bin": cfg.ffmpeg_bin,
        "api_token": "***" if cfg.api_token else None,
    }


class AudioWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Audio."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Welcome Audio")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_config_to_safe_dict(load_audio_config()))
```

### Comprendre ce code

- La configuration est **explicite** (variables d'environnement Forge) : stockage, taille et durée maximales, binaires utilisés.
- On **masque** toujours le token (`"***"`) : une config exposée ne révèle jamais ses secrets.

## La route

Déclarez les deux routes dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.audio_welcome_controller import AudioWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/audio-welcome", AudioWelcomeController.index, name="audio_welcome_index")
    public.add("GET", "/audio-welcome/inspect", AudioWelcomeController.inspect, name="audio_welcome_inspect")
```

## À retenir

- `forge-mvc-audio` est **opt-in** et **sans état** : pas de table, opérations synchrones.
- La configuration audio est inspectable et masque ses secrets.
- `ffprobe`/`ffmpeg` n'interviennent qu'au niveau avancé.

## Après ce starter

Premier contact établi.
La suite : téléverser un fichier audio.

[Téléverser un audio](audio-upload.md)
