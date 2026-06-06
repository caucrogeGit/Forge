# Suivre l'état d'une vidéo

Objectif : observer le **cycle de vie** des vidéos en les regroupant par statut.

**Ce que vous allez apprendre :** `VideoRepository.list_by_status`. Une vidéo
passe par `uploaded` → `processing` → `ready` (ou `failed`). Ce palier liste les
vidéos par statut et renvoie le tout en JSON. C'est le statut que le **worker de
transcodage** (niveau avancé) fera avancer ; ici, on l'**observe**.

Dernier palier du **niveau intermédiaire** de la progression vidéo, après
[Lire une vidéo](video-playback.md).

## Ce que ce starter montre

- le **cycle de vie** : `uploaded`, `processing`, `ready`, `failed` ;
- le regroupement par statut via `list_by_status` ;
- une réponse JSON `{ "by_status": { … } }` ;
- la **réponse `503` pédagogique** si la table n'existe pas encore.

Lecture seule. La table `videos` est garantie par la migration livrée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `VideoRepository.list_by_status` | Lister les vidéos d'un statut donné. | [Parcours vidéo](../../../video/parcours.md) |
| `Response.json` | Renvoyer les vidéos rangées par statut. | [Response](../../../reference/api.md#corehttpresponse) |

## Tester

```bash
forge db:init
forge run
```

Ouvrez `https://localhost:8000/video-status` : les vidéos sont rangées sous
`uploaded`, `processing`, `ready`, `failed`. Tant qu'aucun transcodage n'a tourné,
elles restent au statut `uploaded`.

## Le contrôleur

```python
# mvc/controllers/video_status_controller.py
from forge_mvc_video.storage.repository import VideoRepository


_STATUSES = ("uploaded", "processing", "ready", "failed")


class VideoStatusController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        repo = VideoRepository()
        try:
            by_status = {s: repo.list_by_status(s, limit=20) for s in _STATUSES}
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"by_status": by_status})
```

### Comprendre ce code

- `list_by_status(status, limit=…)` lit les vidéos d'**un** statut ; on boucle sur
  les quatre statuts du cycle de vie pour une vue d'ensemble.
- Le statut n'est **pas** modifié ici : faire avancer une vidéo de `uploaded` à
  `ready` est le rôle du worker de transcodage (`forge video:process`, niveau
  avancé), jamais d'une requête HTTP.
- L'absence de table reste un `503` pédagogique.

## À retenir

- Une vidéo suit un cycle : `uploaded → processing → ready` (ou `failed`).
- `list_by_status` observe ce cycle ; il ne le modifie pas.
- Faire **avancer** le statut est un travail de **worker**, pas de requête HTTP.

## Après ce starter

Vous avez terminé le **niveau intermédiaire** : upload, lecture, suivi d'état.
Faites le point dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
