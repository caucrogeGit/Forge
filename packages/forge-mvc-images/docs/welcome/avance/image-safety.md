# Garde de sécurité à l'upload

Objectif : comprendre **comment Forge refuse une image piégée** : un fichier déguisé en image, ou une image-bombe conçue pour saturer le serveur.

**Ce que vous allez apprendre :** avant toute écriture, `verify_image_content` ouvre réellement le fichier pour confirmer que c'est une image d'un format autorisé, et rejette les images dont la surface dépasse `upload_max_image_pixels` (défense anti-bombe de décompression).
Ce palier met la garde en scène **sans rien écrire** ni base de données.

Troisième palier du **niveau avancé** de la progression images.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation »).
    Comme images est une brique **bibliothèque** (pas de CLI `images:doctor`), ce palier joue le rôle de diagnostic de sécurité.

## Ce que ce starter montre

- la politique de sécurité affichée (formats acceptés, surface maximale) ;
- `verify_image_content` appliqué à un fichier reçu, **sans l'enregistrer** ;
- un verdict clair : image acceptée, ou rejetée avec la raison ;
- la même politique en JSON (`GET /image-safety/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.verify_image_content` | Vérifier qu'un contenu est une vraie image autorisée. | Médias |
| `forge_mvc_images.ALLOWED_IMAGE_EXTENSIONS` | Liste blanche des formats acceptés, affichée dans la politique. | Médias |
| `os.getenv("UPLOAD_MAX_IMAGE_PIXELS")` | Lire le budget anti-bombe (surface maximale en pixels). | Configuration |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-safety`, envoyez une vraie image (acceptée), puis un fichier texte renommé en `.jpg` (rejeté) : la garde fait la différence sur le **contenu**, pas sur l'extension.

## Le contrôleur

```python
# mvc/controllers/image_safety_controller.py
import os

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import ALLOWED_IMAGE_EXTENSIONS, verify_image_content


def _guard_policy() -> dict:
    """Décrit la politique de sécurité appliquée aux uploads d'image."""
    return {
        "allowed_extensions": sorted(ALLOWED_IMAGE_EXTENSIONS),
        "max_image_pixels": int(os.getenv("UPLOAD_MAX_IMAGE_PIXELS", "24000000")),
    }


class ImageSafetyController(BaseController):
    """Starter pédagogique : démontrer la garde de sécurité à l'upload."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "image_safety/index.html",
            context={"csrf_token": BaseController.csrf_token(request), "guard": _guard_policy()},
            request=request,
        )

    @staticmethod
    def check(request: Request) -> Response:
        uploaded = request.file("image")
        context = {"csrf_token": BaseController.csrf_token(request), "guard": _guard_policy()}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render("image_safety/index.html", context=context, request=request)
        try:
            verify_image_content(uploaded.content)
        except UploadError as exc:
            context["rejected"] = str(exc)
            return BaseController.render("image_safety/index.html", context=context, request=request)
        context["accepted"] = uploaded.filename or "image"
        return BaseController.render("image_safety/index.html", context=context, request=request)

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_guard_policy())
```

### Comprendre ce code

- La garde décide sur le **contenu binaire**, pas sur l'extension ni le `Content-Type` (tous deux falsifiables).
- Le budget `UPLOAD_MAX_IMAGE_PIXELS` (24 Mpx par défaut, lu depuis l'environnement) rejette une image démesurée **avant** tout décodage coûteux, c'est la défense anti-bombe.
- On ne fait que vérifier : aucun fichier n'est écrit.
  Idéal pour un diagnostic.

## La vue

Le contrôleur rend `image_safety/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_safety/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Garde de sécurité à l'upload - Forge</title>
</head>
<body>
  <h1>Garde de sécurité à l'upload</h1>

  <p>Politique appliquée par <code>verify_image_content</code> :</p>
  <ul>
    <li>Formats acceptés : <code>{{ guard.allowed_extensions | join(', ') }}</code></li>
    <li>Surface maximale (anti-bombe) : <code>{{ guard.max_image_pixels }}</code> pixels</li>
  </ul>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if accepted %}
  <p data-level="success">✓ <strong>{{ accepted }}</strong> est une image valide - acceptée.</p>
  {% endif %}
  {% if rejected %}
  <p data-level="error">✗ Fichier rejeté : {{ rejected }}</p>
  {% endif %}

  <form method="post" action="/image-safety" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="image" required>
    <button type="submit">Vérifier (sans enregistrer)</button>
  </form>
</body>
</html>
```

## La route

Déclarez les trois routes dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.image_safety_controller import ImageSafetyController

with router.group("", public=True) as public:
    public.add("GET", "/image-safety", ImageSafetyController.index, name="image_safety_index")
    public.add("POST", "/image-safety", ImageSafetyController.check, name="image_safety_check")
    public.add("GET", "/image-safety/inspect", ImageSafetyController.inspect, name="image_safety_inspect")
```

## À retenir

- `verify_image_content` valide le **contenu** avant toute écriture disque.
- L'anti-bombe rejette les images démesurées (`upload_max_image_pixels`).
- C'est cette garde que `save_image_upload` applique en interne à chaque upload.

## Après ce starter

Vous avez fait le tour du niveau avancé : couverture, suppression propre, sécurité.

[Bilan du niveau avancé](bilan.md)
