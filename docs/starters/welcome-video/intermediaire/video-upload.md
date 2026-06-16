# Téléverser une vidéo

Objectif : **alimenter** le module en enregistrant une vidéo uploadée, sans
transcodage.

**Ce que vous allez apprendre :** `ingest_video`. Le formulaire envoie un
fichier ; la fonction le **valide** (taille, conteneur déclaré), le **stocke**
sous un UUID (jamais le nom de fichier utilisateur) et **insère** une ligne
`videos` au statut `uploaded` — **sans ffmpeg**. Le transcodage est un worker
séparé (niveau avancé) : jamais pendant une requête HTTP.

Premier palier du **niveau intermédiaire** de la progression vidéo, après le
[niveau débutant](../debutant/bilan.md).

## Ce que ce starter montre

- un formulaire `multipart/form-data` pour envoyer un fichier vidéo ;
- l'ingestion validée via `ingest_video` (stockage + insertion `videos`) ;
- le statut initial `uploaded` ;
- la liste des vidéos enregistrées, avec leur statut.

La table `videos` est créée par la migration fournie plus bas. **Aucun ffmpeg.**

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `request.file` | Récupérer le fichier vidéo reçu. | [Request](../../../reference/api.md#corehttprequest) |
| `forge_mvc_video.ingest.ingest_video` | Valider, stocker et enregistrer la vidéo (statut `uploaded`). | [Parcours vidéo](../../../video/parcours.md) |
| `VideoIngestError` | Upload refusé (vide, trop gros, conteneur non autorisé). | [Parcours vidéo](../../../video/parcours.md) |

## Tester

```bash
forge db:init
forge run
```

Ouvrez `https://localhost:8000/video-upload`, choisissez un fichier vidéo et
cliquez **Téléverser** : il apparaît dans la liste au statut `uploaded`. Vous
venez d'alimenter la table `videos` **sans lancer aucun transcodage**.

## Le contrôleur

```python
# mvc/controllers/video_upload_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.ingest import VideoIngestError, ingest_video
from forge_mvc_video.storage.repository import VideoRepository


class VideoUploadController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return VideoUploadController._page(request)

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("video")
        if uploaded is None:
            return VideoUploadController._page(
                request, error="Aucun fichier sélectionné."
            )
        title = (request.form("title") or "").strip() or None
        try:
            ingest_video(uploaded.read(), uploaded.filename, title=title)
        except VideoIngestError as exc:
            return VideoUploadController._page(request, error=str(exc))
        return BaseController.redirect("/video-upload")

    @staticmethod
    def _page(request: Request, error: str | None = None) -> Response:
        try:
            videos = VideoRepository().list_recent(limit=20)
        except Exception:
            videos = []
        context = {
            "videos": videos,
            "csrf_token": BaseController.csrf_token(request),
        }
        if error:
            context["error"] = error
        return BaseController.render(
            "video_upload/index.html", context=context, request=request
        )
```

### Comprendre ce code

- `ingest_video(data, filename, title=...)` fait tout le travail sûr : validation,
  stockage sous UUID, insertion de la ligne `videos` au statut `uploaded`. Une
  `VideoIngestError` (fichier vide, trop gros, type refusé) est attrapée pour
  afficher un message clair.
- **Aucun ffmpeg n'est lancé ici** : l'upload est rapide et synchrone, le
  transcodage lourd est délégué à un worker CLI (modèle worker-CLI de Forge).
- En cas de succès, on **redirige** (POST-Redirect-GET).

## La vue

```html
<!-- mvc/views/video_upload/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Téléverser une vidéo — Forge</title>
</head>
<body>
  <h1>Téléverser une vidéo</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  <form method="post" action="/video-upload" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <label>Titre <input type="text" name="title"></label>
    <label>Fichier vidéo <input type="file" name="video" required></label>
    <button type="submit">Téléverser</button>
  </form>

  <h2>Vidéos enregistrées</h2>
  {% if videos %}
  <ul>
    {% for v in videos %}
    <li>{{ v.title or v.uuid }} — <em>{{ v.status }}</em></li>
    {% endfor %}
  </ul>
  {% else %}
  <p>Aucune vidéo pour l'instant.</p>
  {% endif %}
</body>
</html>
```

### Comprendre ce code

- `enctype="multipart/form-data"` est **obligatoire** pour transmettre un
  fichier.
- Le formulaire reste protégé par **CSRF**, comme tout POST.

## La migration

Créez la migration qui crée la table `videos` (cycle de vie
`uploaded → processing → ready → failed`). `CREATE TABLE IF NOT EXISTS` la
rend idempotente.

```sql
-- mvc/migrations/20260601200000_create_videos.sql
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

Ajoutez les deux routes dans le groupe public de `mvc/routes.py`.

```python
# mvc/routes.py
from mvc.controllers.video_upload_controller import VideoUploadController

with router.group("", public=True) as public:
    public.add("GET", "/video-upload", VideoUploadController.index, name="video_upload_index")
    public.add("POST", "/video-upload", VideoUploadController.upload, name="video_upload_store")
```

## À retenir

- `ingest_video` valide, stocke (sous UUID) et enregistre — **sans ffmpeg**.
- L'upload est synchrone ; le transcodage lourd est un **worker séparé**.
- Le statut démarre à `uploaded` ; il évoluera au niveau avancé.

## Après ce starter

Vous savez enregistrer une vidéo. La suite : la **servir** en streaming.

[Lire une vidéo](video-playback.md)
