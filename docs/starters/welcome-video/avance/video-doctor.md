# Diagnostiquer le module Vidéo

Objectif : vérifier que le module vidéo est **sain** — y compris la présence des
binaires de transcodage.

**Ce que vous allez apprendre :** le diagnostic Forge Vidéo. La commande
`forge video:doctor` vérifie l'ensemble (paquet, config, migration, **ffprobe**,
**ffmpeg**, base). Ce starter expose en JSON son **sous-ensemble non invasif** —
les contrôles qui ne touchent pas la base — directement dans l'application.

Dernier palier du **niveau avancé** de la progression vidéo, après
[Transcoder une vidéo](video-transcode.md).

## Ce que ce starter montre

- l'appel des vérifications non invasives du diagnostic :
    - `check_package_importable` — le paquet est installé,
    - `check_config_loadable` — la configuration se charge,
    - `check_migration_present` — la migration `videos` est disponible,
    - `check_ffprobe_present` / `check_ffmpeg_present` — les **binaires de
      transcodage** sont localisés ;
- un statut global `healthy` + le détail de chaque contrôle, en JSON.

Le diagnostic **complet** (table en base) reste la commande `forge video:doctor`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `check_package_importable` / `check_config_loadable` / `check_migration_present` | Vérifications non invasives. | [Parcours vidéo](../../../video/parcours.md) |
| `check_ffprobe_present` / `check_ffmpeg_present` | Localiser les binaires de transcodage. | [Parcours vidéo](../../../video/parcours.md) |
| `forge video:doctor` (CLI) | Diagnostic complet (dont la base). | [Parcours vidéo](../../../video/parcours.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/video-doctor` : la réponse JSON donne `healthy` et
la liste des contrôles avec leur statut. Si ffmpeg/ffprobe ne sont pas installés,
les contrôles correspondants le signalent — utile avant de transcoder.

Pour le diagnostic complet, en ligne de commande :

```bash
forge video:doctor          # paquet + config + migration + ffprobe + ffmpeg
forge video:doctor --db     # + vérifie la table videos
```

## Le contrôleur

```python
# mvc/controllers/video_doctor_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.cli.doctor import (
    check_config_loadable,
    check_ffmpeg_present,
    check_ffprobe_present,
    check_migration_present,
    check_package_importable,
)


# Vérifications sûres : aucune ne touche la base. Les contrôles ffprobe/ffmpeg
# se contentent de localiser les binaires (essentiels au transcodage).
_SAFE_CHECKS = (
    check_package_importable,
    check_config_loadable,
    check_migration_present,
    check_ffprobe_present,
    check_ffmpeg_present,
)


class VideoDoctorController(BaseController):

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
        healthy = all(c["status"] == "ok" for c in checks)
        return Response.json({"healthy": healthy, "checks": checks})
```

### Comprendre ce code

- On n'appelle que les contrôles **sûrs** : aucun ne touche la base, et les checks
  ffprobe/ffmpeg se contentent de **localiser les binaires** (pas de transcodage).
- Chaque contrôle renvoie un `status`, un `name` et un `detail` — on les expose
  tels quels.
- Pour le contrôle **invasif** (table `videos`), on délègue à la CLI
  `forge video:doctor --db`.

## La route

Ajoutez la route dans le groupe public de `mvc/routes.py`.

```python
# mvc/routes.py
from mvc.controllers.video_doctor_controller import VideoDoctorController

with router.group("", public=True) as public:
    public.add("GET", "/video-doctor", VideoDoctorController.index, name="video_doctor_index")
```

## À retenir

- `forge video:doctor` diagnostique le module ; ses contrôles non invasifs sont
  réutilisables en application.
- Vérifier la **présence de ffmpeg/ffprobe** évite les surprises au transcodage.
- Un diagnostic sépare le **sûr** (paquet, config, binaires) de l'**invasif**
  (base) — on n'effleure la base que sur demande.

## Après ce starter

Vous avez terminé le **niveau avancé** et toute la progression vidéo : sonde,
transcodage, diagnostic. Faites le point dans le bilan du niveau.

[Bilan du niveau avancé](bilan.md)
