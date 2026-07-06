# Le détail d'une vidéo

Objectif : lire **une vidéo précise** par son UUID et la renvoyer en JSON.

**Ce que vous allez apprendre :** cibler une vidéo avec `VideoRepository.get_by_uuid`, et distinguer trois cas : trouvée (`200`), inconnue (`404`), table absente (`503`).
C'est la lecture unitaire, après la liste.

Dernier palier du **niveau débutant** de la progression vidéo, après [Lister les vidéos](video-list.md).

## Ce que ce starter montre

- une route **paramétrée** `/video-detail/{uuid}` ;
- la lecture d'une vidéo via `get_by_uuid` ;
- une réponse `404` claire si l'UUID est inconnu ;
- la même **réponse `503` pédagogique** si la table n'existe pas encore.

Lecture seule, aucun ffmpeg.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `request.route` | Lire l'`uuid` dans l'URL. | Request |
| `VideoRepository.get_by_uuid` | Lire une vidéo précise (ou `None`). | [Parcours vidéo](../../parcours.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/video-detail/<uuid>` avec l'UUID d'une vidéo enregistrée : la réponse JSON donne ses métadonnées.
Un UUID inconnu renvoie `404` ; sans table, `503`.

## Le contrôleur

```python
# mvc/controllers/video_detail_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.storage.repository import VideoRepository


_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Vidéo (forge video:init) avant de lire "
        "une vidéo."
    ),
}


class VideoDetailController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        uuid = request.route("uuid")
        try:
            video = VideoRepository().get_by_uuid(uuid)
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        if video is None:
            return Response.json(
                {"error": "video_not_found", "uuid": uuid}, status=404
            )
        return Response.json({"video": video})
```

### Comprendre ce code

- `uuid` vient de l'**URL** (`route`) : on cible la vidéo sans query string.
- `get_by_uuid(uuid)` renvoie un dictionnaire **ou `None`** : on traduit `None` en `404`, jamais une page d'erreur brute.
- L'absence de table reste un `503` pédagogique, comme au palier précédent.

## La route

Ajoutez la route paramétrée dans le groupe public de `mvc/routes.py`.

```python
# mvc/routes.py
from mvc.controllers.video_detail_controller import VideoDetailController

with router.group("", public=True) as public:
    public.add("GET", "/video-detail/{uuid}", VideoDetailController.index, name="video_detail_index")
```

## À retenir

- `get_by_uuid(uuid)` lit une vidéo précise.
- Distinguer **trouvée / inconnue / indisponible** = `200` / `404` / `503`.
- Une route **paramétrée** cible une ressource via `route`.

## Après ce starter

Vous avez terminé le **niveau débutant** : configuration, liste, détail.
Faites le point dans le bilan du niveau.

[Bilan du niveau débutant](bilan.md)
