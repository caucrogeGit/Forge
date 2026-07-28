# Limiter les uploads

Objectif : protéger une route d'upload contre les abus avec un **rate-limit par IP**.

**Ce que vous allez apprendre :** `is_upload_rate_limited(ip)` indique si une IP a atteint le quota (fenêtre glissante en mémoire), `record_upload_attempt(ip)` enregistre une tentative.
Au-delà du quota, la route répond `429`.

Deuxième palier du **niveau intermédiaire** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé.

## Ce que ce starter montre

- la vérification du quota avec `is_upload_rate_limited(request.ip)` ;
- l'enregistrement d'une tentative avec `record_upload_attempt(request.ip)` ;
- une réponse `429` au-delà de la limite.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.is_upload_rate_limited` | Tester le quota d'uploads de l'IP. | Médias |
| `forge_mvc_files.record_upload_attempt` | Enregistrer une tentative. | Médias |
| `request.ip` | IP cliente résolue (proxies de confiance pris en compte). | Request |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-rate-limit` et envoyez plus de 10 fois en moins d'une minute : la route bascule en `429`.

## Le contrôleur

```python
# mvc/controllers/file_rate_limit_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import (
    UploadError,
    is_upload_rate_limited,
    record_upload_attempt,
    save_upload,
)


class FileRateLimitController(BaseController):
    """Starter pédagogique : protéger une route d'upload par rate-limit."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_rate_limit/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        context = {"csrf_token": BaseController.csrf_token(request)}
        if is_upload_rate_limited(request.ip):
            context["rate_limited"] = True
            return BaseController.render(
                "file_rate_limit/index.html", context=context, request=request, status=429
            )
        record_upload_attempt(request.ip)
        uploaded = request.file("document")
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render(
                "file_rate_limit/index.html", context=context, request=request
            )
        try:
            saved = save_upload(uploaded, "documents")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "file_rate_limit/index.html", context=context, request=request
            )
        context["saved"] = saved
        return BaseController.render(
            "file_rate_limit/index.html", context=context, request=request
        )
```

## La vue

```html
<!-- mvc/views/file_rate_limit/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Limiter les uploads - Forge</title>
</head>
<body>
  <h1>Limiter les uploads</h1>

  <p>Quota : <strong>10 uploads par minute et par IP</strong> (fenêtre glissante, en mémoire).</p>

  {% if rate_limited %}
  <p data-level="error"><strong>429 - Trop d'uploads.</strong> Réessayez dans un instant.</p>
  {% endif %}
  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if saved %}
  <p data-level="success">Fichier stocké : <code>{{ saved.path }}</code></p>
  {% endif %}

  <form method="post" action="/file-rate-limit" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="document" required>
    <button type="submit">Envoyer</button>
  </form>

  <p>Envoyez plus de 10 fois en moins d'une minute : la route bascule en <code>429</code>.</p>
</body>
</html>
```

## La route

```python
# mvc/routes/__init__.py
from mvc.controllers.file_rate_limit_controller import FileRateLimitController

with router.group("", public=True) as public:
    public.add("GET", "/file-rate-limit", FileRateLimitController.index, name="file_rate_limit_index")
    public.add("POST", "/file-rate-limit", FileRateLimitController.upload, name="file_rate_limit_upload")
```

### Comprendre ce code

- On teste **avant** d'enregistrer la tentative, et on n'enregistre que les requêtes effectivement traitées.
- Le compteur est **en mémoire** (fenêtre glissante) : simple, sans base, isolé des compteurs de connexion.
- `request.ip` est l'IP **résolue** (un proxy de confiance ne masque pas le client).

## À retenir

- Une route d'upload publique se **protège** par rate-limit.
- `is_upload_rate_limited` / `record_upload_attempt` : tester puis enregistrer.
- Au-delà du quota → `429`, sans toucher au disque.

## Après ce starter

La route est protégée.
La suite : supprimer un fichier proprement.

[Supprimer un fichier](file-delete.md)
