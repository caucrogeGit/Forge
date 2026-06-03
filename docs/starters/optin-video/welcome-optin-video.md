# Bonjour Vidéo

Premier contact avec **Forge Video**, le module opt-in `forge-mvc-video`.

Le starter affiche une page d'accueil texte, expose la configuration
vidéo lue (token masqué), liste les dernières vidéos (pédagogique même
quand la table n'existe pas encore) et branche la route de lecture
officielle `GET /videos/{uuid}`.

Identifiant : `welcome-optin-video` (alias `bonjour-video` / `video` / `17`).

## Ce que ce starter installe

- une route `/welcome-optin-video` (texte)
- une route `/welcome-optin-video/inspect` (JSON, token masqué)
- une route `/welcome-optin-video/list` (JSON, lecture si table prête)
- la route de lecture vidéo officielle `GET /videos/{uuid}` (streaming
  HTTP Range), branchée via la couche **`optins/`**
- un contrôleur `WelcomeVideoController` (3 méthodes)
- une couche `optins/` (registre explicite + branchement vidéo local)
- aucune vue HTML
- aucune base de données requise pour la page d'accueil
- aucun `ffmpeg` lancé

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par chaque méthode. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Construire les réponses texte et JSON. | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../reference/api.md#coremvccontroller) |
| `VideoConfig` | Lue via `load_video_config()` pour `inspect`. | [Parcours vidéo](../../video/parcours.md) |
| `VideoRepository` | Liste les vidéos pour `list`. | [Parcours vidéo](../../video/parcours.md) |

## Avant de tester — `forge video:doctor`

```bash
forge video:doctor
```

Diagnostic statique (package, configuration, migration, `ffmpeg`/`ffprobe`,
routes). `ffmpeg`/`ffprobe` ne sont nécessaires que pour le **traitement**
(`forge video:process`), pas pour la page d'accueil de ce starter.

## Tester dans le navigateur

| URL | Résultat |
|-----|----------|
| `http://localhost:8000/welcome-optin-video` | `Bonjour Forge Video` |
| `http://localhost:8000/welcome-optin-video/inspect` | JSON de la configuration (token masqué) |
| `http://localhost:8000/welcome-optin-video/list` | JSON des dernières vidéos (ou message pédagogique) |
| `http://localhost:8000/videos/{uuid}` | Lecture vidéo en streaming (Range), si la vidéo est `ready` |

### Inspection de la configuration — `/welcome-optin-video/inspect`

```json
{
  "ffmpeg_bin": "ffmpeg",
  "ffprobe_bin": "ffprobe",
  "storage_root": "storage/video",
  "max_upload_mb": 1000,
  "max_duration_seconds": 3600,
  "api_token": null
}
```

Le token de lecture est **toujours** affiché comme `"***"` quand il est
défini (`FORGE_VIDEO_API_TOKEN`), et `null` sinon — jamais en clair.

### Liste des vidéos — `/welcome-optin-video/list`

Si la table `videos` est disponible, renvoie les 20 dernières vidéos.
Sinon — table absente, base non configurée — réponse **pédagogique**
(HTTP 503) :

```json
{
  "error": "video_storage_not_ready",
  "message": "La table videos n'est pas encore disponible. Applique la migration Forge Video avant de lister les vidéos (forge video:init && forge migration:apply)."
}
```

Pour activer le stockage puis traiter une vidéo :

```bash
forge video:init                 # copie la migration (idempotent)
forge migration:apply            # crée la table videos
forge video:upload film.mp4 --title "Ma vidéo"
forge video:process --pending    # transcodage MP4 + poster
```

## Branchement opt-in (`optins/`)

Le paquet `forge-mvc-video` reste distribué ; le projet le **branche
localement** via un dossier `optins/`, sans découverte automatique :

```text
optins/
├── __init__.py
├── registry.py          # register_optins(router) — registre explicite
└── video/
    ├── __init__.py
    ├── routes.py        # register(router) -> register_video_routes(router)
    └── README.md        # mode d'emploi local court
```

```python
# mvc/routes.py
from optins.registry import register_optins
register_optins(router)

# optins/registry.py
def register_optins(router):
    from optins.video.routes import register as register_video
    register_video(router)

# optins/video/routes.py
from forge_mvc_video import register_video_routes
def register(router):
    register_video_routes(router)   # GET /videos/{uuid}
```

## À retenir

- Le starter fonctionne **sans ffmpeg** et **sans table**. La page
  `/welcome-optin-video` répond immédiatement.
- `inspect` vérifie la configuration en un coup d'œil, sans fuiter le
  token de lecture.
- La route `list` signale gentiment l'absence de table — bon signal
  « tu n'as pas encore appliqué la migration ».
- La lecture officielle `GET /videos/{uuid}` est branchée via la couche
  `optins/` (`register_optins` → `optins/video/routes.py` →
  `register_video_routes`).

## Après ce starter

Voir [Forge Video — parcours complet](../../video/parcours.md) pour la
chaîne `upload → process → lecture → cleanup` de bout en bout.
