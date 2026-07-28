# Diagnostiquer le module Audio

Objectif : exposer le **diagnostic** non invasif de Forge Audio en JSON, à partir des contrôles de `forge audio:doctor`.

**Ce que vous allez apprendre :** Forge Audio fournit `forge audio:doctor` ; ce palier en expose le **sous-ensemble non invasif** : paquet importable, configuration chargeable, présence de `ffprobe`/`ffmpeg`, routes enregistrables.

Troisième palier du **niveau avancé** de la progression audio.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-audio` installé.

## Ce que ce starter montre

- l'appel des contrôles `check_*` de `forge_mvc_audio.cli.doctor` ;
- leur sérialisation JSON (`status`, `name`, `detail`) ;
- un diagnostic **sans effet de bord** (ni fichier, ni réseau, ni base).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_audio.cli.doctor.check_*` | Contrôles : paquet, config, `ffprobe`, `ffmpeg`, routes. | Audio |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/audio-doctor` : la page renvoie le statut de chaque contrôle en JSON.
La présence de `ffprobe`/`ffmpeg` y apparaît.

## Le contrôleur

```python
# mvc/controllers/audio_doctor_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio.cli.doctor import (
    check_config_loadable,
    check_ffmpeg_present,
    check_ffprobe_present,
    check_package_importable,
    check_routes_registrable,
)

# Contrôles sûrs : aucun ne touche de fichier ni de réseau.
_SAFE_CHECKS = (
    check_package_importable,
    check_config_loadable,
    check_ffprobe_present,
    check_ffmpeg_present,
    check_routes_registrable,
)


class AudioDoctorController(BaseController):
    """Starter pédagogique : diagnostic Audio non invasif exposé en JSON."""

    @staticmethod
    def index(request: Request) -> Response:
        checks = []
        for check in _SAFE_CHECKS:
            result = check()
            checks.append({
                "status": result.status,
                "name": result.name,
                "detail": result.detail,
            })
        return Response.json({"checks": checks})
```

### Comprendre ce code

- Chaque `check_*()` renvoie un `CheckResult(status, name, detail)` : on les sérialise tels quels.
- Tous les contrôles retenus sont **sûrs** : aucun ne touche un fichier, le réseau ou une base.
  Un diagnostic ne doit jamais avoir d'effet de bord.
- La commande `forge audio:doctor` reste le diagnostic complet en ligne de commande.

## La route

Déclarez la route dans `mvc/routes/__init__.py`, à l'intérieur du groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.audio_doctor_controller import AudioDoctorController

with router.group("", public=True) as public:
    public.add("GET", "/audio-doctor", AudioDoctorController.index, name="audio_doctor_index")
```

## À retenir

- Un module exploitable se **diagnostique** : paquet, config, binaires, routes.
- `forge audio:doctor` en CLI ; ce starter l'expose en HTTP/JSON.
- Un diagnostic est **non invasif** par principe.

## Après ce starter

Vous avez parcouru toute la progression audio : découvrir, ingérer, lire, sonder, transcoder, diagnostiquer.

[Bilan du niveau avancé](bilan.md)
