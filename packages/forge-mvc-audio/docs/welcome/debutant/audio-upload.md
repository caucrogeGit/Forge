# Téléverser un audio

Objectif : ingérer un fichier audio avec `ingest_audio` : valider et stocker, sans lancer `ffprobe` ni `ffmpeg`.

**Ce que vous allez apprendre :** `ingest_audio` valide (extension, taille) et **stocke** le fichier source à un emplacement **uuid-based** (le nom utilisateur n'apparaît jamais dans le chemin, anti-traversal par construction).
Il retourne un dict `{uuid, title, original_path, size_bytes, mime_type}`.

Deuxième palier du **niveau débutant** de la progression audio.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-audio` installé (palier « Installation »).
    Aucun `ffmpeg`/`ffprobe` n'est requis ici.

## Ce que ce starter montre

- un formulaire `multipart/form-data` (avec CSRF) ;
- `ingest_audio(bytes, filename)` : valide, stocke en uuid-based ;
- l'affichage de l'uuid, du chemin source, de la taille et du type.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_audio.ingest_audio` | Valider et stocker un audio source (uuid-based). | Audio |
| `forge_mvc_audio.AudioIngestError` | Erreur si l'upload est refusé (extension, taille, vide). | Audio |
| `request.file(...)` | Récupérer le fichier envoyé. | Request |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/audio-upload`, envoyez un fichier audio autorisé : la page affiche l'uuid attribué et le chemin source.
Notez l'`original_path` pour les paliers avancés (sonder, transcoder).

## Le contrôleur

```python
# mvc/controllers/audio_upload_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio import AudioIngestError, ingest_audio


class AudioUploadController(BaseController):
    """Starter pédagogique : ingérer un fichier audio source."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "audio_upload/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("audio")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier audio sélectionné."
            return BaseController.render(
                "audio_upload/index.html", context=context, request=request
            )
        try:
            result = ingest_audio(uploaded.content, uploaded.filename or "audio")
        except AudioIngestError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "audio_upload/index.html", context=context, request=request
            )
        context["result"] = result
        return BaseController.render(
            "audio_upload/index.html", context=context, request=request
        )
```

### Comprendre ce code

- `ingest_audio` prend des **octets** (`uploaded.content`) et un nom : il valide **avant** d'écrire, puis range le fichier sous un chemin uuid.
- Le **nom utilisateur n'entre jamais dans le chemin** : c'est l'anti-traversal par construction (modèle propre à audio/video, distinct du modèle « nom assaini »
  de `forge-mvc-files`).
- Aucun `ffprobe`/`ffmpeg` : l'ingestion ne fait que valider et stocker.

## La vue

```html
<!-- mvc/views/audio_upload/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Téléverser un audio - Forge</title>
</head>
<body>
  <h1>Téléverser un audio</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  {% if result %}
  <p data-level="success">Audio ingéré :</p>
  <ul>
    <li>UUID : <code>{{ result.uuid }}</code></li>
    <li>Chemin source : <code>{{ result.original_path }}</code></li>
    <li>Taille : {{ result.size_bytes }} octets</li>
    <li>Type MIME : <code>{{ result.mime_type }}</code></li>
  </ul>
  <p>Écoute possible (une fois la lecture branchée) : <code>/audio/{{ result.uuid }}</code></p>
  {% endif %}

  <form method="post" action="/audio-upload" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="audio" accept="audio/*" required>
    <button type="submit">Téléverser</button>
  </form>
</body>
</html>
```

## La route

Déclarez les deux routes dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.audio_upload_controller import AudioUploadController

with router.group("", public=True) as public:
    public.add("GET", "/audio-upload", AudioUploadController.index, name="audio_upload_index")
    public.add("POST", "/audio-upload", AudioUploadController.upload, name="audio_upload_store")
```

## À retenir

- `ingest_audio` = valider **puis** stocker, repéré par **uuid**.
- Le chemin source est sûr par construction (uuid, pas de nom utilisateur).
- L'ingestion est légère : pas de sondage ni de transcodage ici.

## Après ce starter

L'audio est stocké.
La suite : le **lire** en streaming.

[Lire un audio](audio-play.md)
