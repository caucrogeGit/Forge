# Lister les vidéos

Objectif : lire les vidéos déjà **enregistrées** par le module et les renvoyer en
JSON.

**Ce que vous allez apprendre :** le `VideoRepository` et sa méthode
`list_recent`, qui renvoie les dernières vidéos de la table `videos` (ordre du
plus récent). Et un réflexe Forge : rester **pédagogique** quand la table
n'existe pas encore, au lieu de planter.

Palier 2 du **niveau débutant** de la progression vidéo, après
[Bonjour Forge Vidéo](video-welcome.md).

## Ce que ce starter montre

- la lecture des dernières vidéos via `VideoRepository.list_recent` ;
- une réponse JSON `{ "videos": [...] }` ;
- une **réponse `503` explicite** quand la table `videos` n'est pas encore
  disponible (aucun `video:init` lancé), au lieu d'une erreur brute.

Aucun ffmpeg, aucune écriture.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_video.storage.repository.VideoRepository` | Lire les vidéos enregistrées. | [Parcours vidéo](../../parcours.md) |
| `VideoRepository.list_recent` | Dernières vidéos (ordre décroissant). | [Parcours vidéo](../../parcours.md) |
| `Response.json` | Renvoyer les vidéos (ou l'erreur) en JSON. | [Response](../../../reference/api.md#corehttpresponse) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/video-list`. Sans table créée, la route répond
`503` avec un message qui invite à lancer `forge video:init`. Une fois des vidéos
enregistrées (niveau intermédiaire), elle renvoie la liste.

## Le contrôleur

```python
# mvc/controllers/video_list_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.storage.repository import VideoRepository


_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Vidéo (forge video:init) avant de "
        "lister les vidéos."
    ),
}


class VideoListController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        try:
            videos = VideoRepository().list_recent(limit=20)
        except Exception:
            # Table absente, base inaccessible… — on reste pédagogique.
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"videos": videos})
```

### Comprendre ce code

- `VideoRepository()` utilise par défaut l'accès base de Forge
  (`core.database.db`) — aucun branchement manuel.
- `list_recent(limit=20)` renvoie les 20 dernières vidéos sous forme de
  dictionnaires, directement sérialisables en JSON.
- Le `try/except` **ne masque pas un bug** : il traduit l'absence de table en
  réponse `503` pédagogique. Un starter de découverte ne doit jamais planter
  parce que l'infrastructure n'est pas encore montée.

## La route

Ajoutez la route dans le groupe public de `mvc/routes.py`.

```python
# mvc/routes.py
from mvc.controllers.video_list_controller import VideoListController

with router.group("", public=True) as public:
    public.add("GET", "/video-list", VideoListController.index, name="video_list_index")
```

## À retenir

- `VideoRepository.list_recent` lit les dernières vidéos enregistrées.
- Le repository s'appuie sur l'accès base standard de Forge.
- Un starter de découverte **reste pédagogique** quand la table manque (`503`).

## Après ce starter

Vous savez lister les vidéos. La suite : afficher le détail d'une vidéo.

[Le détail d'une vidéo](video-detail.md)
