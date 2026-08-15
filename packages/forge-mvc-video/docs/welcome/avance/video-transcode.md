# Transcoder une vidéo

Objectif : transformer une vidéo uploadée en **MP4 lisible**, via le worker de transcodage.

**Ce que vous allez apprendre :** le modèle **worker-CLI** de Forge Vidéo.
`forge video:process` lance `process_video`, qui sonde la source, génère un poster et **transcode en MP4 avec ffmpeg**, faisant avancer le statut `uploaded → processing → ready`.
Le transcodage est lourd : il reste un **worker**, **jamais** une requête HTTP.

Palier 2 du **niveau avancé** de la progression vidéo, après [Sonder une vidéo](video-probe.md).

!!! note "ffmpeg requis"
    Le transcodage exécute **ffmpeg**.
    Installez-le et renseignez au besoin `FORGE_VIDEO_FFMPEG_BIN`.
    Le travail lourd se fait en ligne de commande, hors du cycle requête/réponse.

## Ce que ce starter montre

- le **worker** `forge video:process` (un identifiant, ou `--pending` pour tout) ;
- l'orchestration `process_video` : sonde + poster + transcodage MP4 ;
- l'avancée du statut `uploaded → processing → ready` (ou `failed`) ;
- une route qui **liste les vidéos en attente** et la config ffmpeg, sans rien transcoder elle-même.

La table `videos` est garantie par la migration fournie plus bas.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge video:process` (CLI) | Lancer le worker de transcodage. | [Parcours vidéo](../../parcours.md) |
| `forge_mvc_video.process.process_video` | Orchestrer sonde + poster + transcodage MP4. | [Parcours vidéo](../../parcours.md) |
| `VideoRepository.list_by_status` | Lister les vidéos `uploaded` à traiter. | [Parcours vidéo](../../parcours.md) |

## Tester

```bash
forge db:config    # amorce DB_NAME dans env/ (une seule fois)
forge db:init
forge video:init    # copie la migration de l'opt-in
forge migration:apply    # l'applique en base
forge run
```

Ouvrez `https://localhost:8000/video-transcode` : la page liste les vidéos au statut `uploaded` et le binaire ffmpeg configuré.
Puis, en ligne de commande (ffmpeg installé) :

```bash
forge video:process <id>        # traite une vidéo
forge video:process --pending   # traite toutes les vidéos uploaded
```

Les vidéos passent à `ready` et se lisent via `GET /videos/{uuid}`.

## Le contrôleur

```python
# mvc/controllers/video_transcode_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.config import load_video_config
from forge_mvc_video.storage.repository import VideoRepository


class VideoTranscodeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        cfg = load_video_config()
        try:
            pending = VideoRepository().list_by_status("uploaded", limit=50)
        except Exception:
            pending = []
        return BaseController.render(
            "video_transcode/index.html",
            context={"ffmpeg_bin": cfg.ffmpeg_bin, "pending": pending},
            request=request,
        )
```

### Comprendre ce code

- La route **ne transcode pas** : elle prépare le terrain (liste des vidéos à traiter + config).
  Lancer ffmpeg dans une requête web la bloquerait : c'est exactement ce que le modèle worker-CLI **évite**.
- `process_video` (appelé par `forge video:process`) fait le travail lourd **hors HTTP** et écrit le résultat (`mp4_path`, `poster_path`, statut `ready`).
- En cas d'échec ffmpeg, la vidéo passe à `failed` avec un `error_message` lisible ; le diagnostic est le palier suivant.

## La vue

```html
<!-- mvc/views/video_transcode/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Transcoder une vidéo - Forge</title>
</head>
<body>
  <h1>Transcoder une vidéo</h1>

  <p>Binaire ffmpeg configuré : <code>{{ ffmpeg_bin }}</code></p>

  <h2>Vidéos en attente de transcodage</h2>
  {% if pending %}
  <ul>
    {% for v in pending %}
    <li>#{{ v.id }} - {{ v.title or v.uuid }} <em>({{ v.status }})</em></li>
    {% endfor %}
  </ul>
  {% else %}
  <p>Aucune vidéo au statut <code>uploaded</code>.</p>
  {% endif %}

  <h2>Lancer le transcodage</h2>
  <p>Le transcodage est un <strong>worker CLI</strong> (jamais une requête HTTP) :</p>
  <pre>forge video:process &lt;id&gt;        # une vidéo
forge video:process --pending   # toutes les vidéos uploaded</pre>
  <p>
    Le worker fait avancer le statut <code>uploaded → processing → ready</code>.
    Les vidéos prêtes se lisent via <code>GET /videos/{uuid}</code>.
  </p>
</body>
</html>
```

## La migration

Créez la table `videos` si elle n'existe pas déjà : le worker fait avancer son `status` de `uploaded` à `ready`.
`CREATE TABLE IF NOT EXISTS` reste idempotent.

```sql
-- mvc/migrations/20260601240000_create_videos.sql
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
from mvc.controllers.video_transcode_controller import VideoTranscodeController

with router.group("", public=True) as public:
    public.add("GET", "/video-transcode", VideoTranscodeController.index, name="video_transcode_index")
```

## À retenir

- Le transcodage est un **worker** (`forge video:process`), jamais une requête web.
- `process_video` orchestre sonde + poster + MP4 et avance le statut.
- Une route web peut **préparer** et **observer**, pas exécuter le travail lourd.

## Après ce starter

Vous savez transcoder.
Dernier palier : diagnostiquer le module quand quelque chose cloche.

[Diagnostiquer le module Vidéo](video-doctor.md)
