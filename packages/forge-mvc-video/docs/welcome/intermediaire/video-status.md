# Suivre l'état d'une vidéo

Objectif : observer le **cycle de vie** des vidéos en les regroupant par statut.

**Ce que vous allez apprendre :** `VideoRepository.list_by_status`.
Une vidéo passe par `uploaded` → `processing` → `ready` (ou `failed`).
Ce palier liste les vidéos par statut et renvoie le tout en JSON.
C'est le statut que le **worker de transcodage** (niveau avancé) fera avancer ; ici, on l'**observe**.

Dernier palier du **niveau intermédiaire** de la progression vidéo, après [Lire une vidéo](video-playback.md).

## Ce que ce starter montre

- le **cycle de vie** : `uploaded`, `processing`, `ready`, `failed` ;
- le regroupement par statut via `list_by_status` ;
- une réponse JSON `{ "by_status": { … } }` ;
- la **réponse `503` pédagogique** si la table n'existe pas encore.

Lecture seule.
La table `videos` est garantie par la migration fournie plus bas.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `VideoRepository.list_by_status` | Lister les vidéos d'un statut donné. | [Parcours vidéo](../../parcours.md) |
| `Response.json` | Renvoyer les vidéos rangées par statut. | Response |

## Tester

```bash
forge db:config    # amorce DB_NAME dans env/ (une seule fois)
forge db:init
forge video:init    # copie la migration de l'opt-in
forge migration:apply    # l'applique en base
forge run
```

Ouvrez `https://localhost:8000/video-status` : les vidéos sont rangées sous `uploaded`, `processing`, `ready`, `failed`.
Tant qu'aucun transcodage n'a tourné, elles restent au statut `uploaded`.

## Le contrôleur

```python
# mvc/controllers/video_status_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.storage.repository import VideoRepository


# Cycle de vie d'une vidéo dans le module Forge Vidéo.
_STATUSES = ("uploaded", "processing", "ready", "failed")

_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Vidéo (forge video:init) avant de "
        "suivre les statuts."
    ),
}


class VideoStatusController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        repo = VideoRepository()
        try:
            by_status = {
                status: repo.list_by_status(status, limit=20)
                for status in _STATUSES
            }
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"by_status": by_status})
```

### Comprendre ce code

- `list_by_status(status, limit=…)` lit les vidéos d'**un** statut ; on boucle sur les quatre statuts du cycle de vie pour une vue d'ensemble.
- Le statut n'est **pas** modifié ici : faire avancer une vidéo de `uploaded` à `ready` est le rôle du worker de transcodage (`forge video:process`, niveau avancé), jamais d'une requête HTTP.
- L'absence de table reste un `503` pédagogique.

## La migration

Créez la table `videos` si elle n'existe pas déjà, pour observer le cycle de vie par statut.
`CREATE TABLE IF NOT EXISTS` reste idempotent.

```sql
-- mvc/migrations/20260601220000_create_videos.sql
CREATE TABLE IF NOT EXISTS videos (
    id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    uuid             CHAR(36)        NOT NULL,
    title            VARCHAR(255)    NULL,
    original_path    VARCHAR(500)    NOT NULL,
    mp4_path         VARCHAR(500)    NULL,
    poster_path      VARCHAR(500)    NULL,
    mime_type        VARCHAR(120)    NULL,
    size_bytes       BIGINT UNSIGNED NOT NULL,
    duration_seconds INT UNSIGNED    NULL,
    width            INT UNSIGNED    NULL,
    height           INT UNSIGNED    NULL,
    status           VARCHAR(30)     NOT NULL,
    error_message    TEXT            NULL,
    created_at       DATETIME(6)     NOT NULL,
    updated_at       DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_videos_uuid (uuid),
    INDEX idx_videos_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## La route

Ajoutez la route dans le groupe public de `mvc/routes/__init__.py`.

```python
# mvc/routes/__init__.py
from mvc.controllers.video_status_controller import VideoStatusController

with router.group("", public=True) as public:
    public.add("GET", "/video-status", VideoStatusController.index, name="video_status_index")
```

## À retenir

- Une vidéo suit un cycle : `uploaded → processing → ready` (ou `failed`).
- `list_by_status` observe ce cycle ; il ne le modifie pas.
- Faire **avancer** le statut est un travail de **worker**, pas de requête HTTP.

## Après ce starter

Vous avez terminé le **niveau intermédiaire** : upload, lecture, suivi d'état.
Faites le point dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
