# Bonjour Forge Vidéo

Objectif : premier contact avec le module **opt-in** `forge-mvc-video` et sa
configuration.

**Ce que vous allez apprendre :** vérifier que le module vidéo répond, et
**inspecter sa configuration** avec `load_video_config` — en **masquant le
token**. Aucun ffmpeg, aucune base : on découvre simplement comment Forge Vidéo
est branché.

Premier palier du **niveau débutant** de la progression vidéo
([vue d'ensemble des starters](../../index.md#progression-recommandee)).

!!! note "Module opt-in"
    Ce starter suppose le module installé : `forge opt-in:install video`
    (ou `pip install forge-mvc-video`). Le cœur de Forge reste autonome ; la
    vidéo est une brique que l'on ajoute à la demande.

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /video-welcome`) ;
- la lecture de la configuration vidéo avec `load_video_config` ;
- la sérialisation JSON de cette config avec le **token masqué**.

Aucun ffmpeg, aucune base de données.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_video.config.load_video_config` | Lire la configuration du module vidéo. | [Parcours vidéo](../../../video/parcours.md) |
| `Response.text` / `Response.json` | Renvoyer du texte puis du JSON. | [Response](../../../reference/api.md#corehttp) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/video-welcome` : la page affiche
**« Bonjour Forge Vidéo »**. Puis `https://localhost:8000/video-welcome/inspect`
renvoie la configuration en JSON, le token remplacé par `***`.

## Le contrôleur

```python
# mvc/controllers/video_welcome_controller.py
from forge_mvc_video.config import load_video_config


def _config_to_safe_dict(cfg) -> dict:
    return {
        "ffmpeg_bin": cfg.ffmpeg_bin,
        "ffprobe_bin": cfg.ffprobe_bin,
        "storage_root": str(cfg.storage_root),
        "max_upload_mb": cfg.max_upload_mb,
        "max_duration_seconds": cfg.max_duration_seconds,
        "api_token": "***" if cfg.api_token else None,
    }


class VideoWelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Vidéo")

    @staticmethod
    def inspect(request: Request) -> Response:
        cfg = load_video_config()
        return Response.json(_config_to_safe_dict(cfg))
```

### Comprendre ce code

- `load_video_config()` lit la configuration vidéo (binaires ffmpeg/ffprobe,
  racine de stockage, limites d'upload/durée) depuis l'environnement Forge —
  comme le reste de la config Forge, elle est **explicite**.
- On ne renvoie **jamais** le token : `"***" if cfg.api_token else None`. Une
  config exposée masque toujours ses secrets.

## À retenir

- Le module vidéo est **opt-in** : on l'installe à la demande, le cœur reste
  autonome.
- `load_video_config()` donne accès à la configuration de façon explicite.
- On **masque les secrets** dès qu'une config est sérialisée.

## Après ce starter

Premier contact établi. La suite : lister les vidéos déjà enregistrées.

[Lister les vidéos](video-list.md)
