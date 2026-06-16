# Valider un upload

Objectif : comprendre **pourquoi** un fichier est refusé — la taxonomie des
règles de validation.

**Ce que vous allez apprendre :** `save_upload` valide extension, type MIME et
taille avant d'écrire. Chaque refus lève une exception **précise** de la hiérarchie
`UploadError` (qui vit dans le core, réexportée par files). Ce palier nomme la règle
qui rejette.

Premier palier du **niveau intermédiaire** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé (palier « Installation »).

## Ce que ce starter montre

- un formulaire d'upload (CSRF) ;
- la capture des sous-types `UploadInvalidExtensionError`,
  `UploadInvalidMimeTypeError`, `UploadTooLargeError` ;
- l'affichage de la **règle** qui a rejeté le fichier.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.save_upload` | Tente l'upload (valide puis écrit). | [Médias](../../../features/media.md) |
| `UploadInvalidExtensionError` / `…MimeTypeError` / `UploadTooLargeError` | Refus précis selon la règle. | [Médias](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-validate` et tentez un `.exe` (extension), un
fichier mal typé, ou un fichier trop gros : chaque refus nomme sa règle.

## Le contrôleur

```python
# mvc/controllers/file_validate_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import (
    UploadError,
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadTooLargeError,
    save_upload,
)


class FileValidateController(BaseController):
    """Starter pédagogique : comprendre la taxonomie des refus d'upload."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_validate/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def check(request: Request) -> Response:
        uploaded = request.file("document")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render(
                "file_validate/index.html", context=context, request=request
            )
        try:
            saved = save_upload(uploaded, "documents")
        except UploadInvalidExtensionError as exc:
            context["rejected"] = {"rule": "extension", "message": str(exc)}
        except UploadInvalidMimeTypeError as exc:
            context["rejected"] = {"rule": "type MIME", "message": str(exc)}
        except UploadTooLargeError as exc:
            context["rejected"] = {"rule": "taille", "message": str(exc)}
        except UploadError as exc:
            context["rejected"] = {"rule": "autre", "message": str(exc)}
        else:
            context["accepted"] = saved.original_name
        return BaseController.render(
            "file_validate/index.html", context=context, request=request
        )
```

## La vue

```html
<!-- mvc/views/file_validate/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Valider un upload — Forge</title>
</head>
<body>
  <h1>Valider un upload</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if accepted %}
  <p data-level="success">✓ <strong>{{ accepted }}</strong> accepté (toutes les règles passent).</p>
  {% endif %}
  {% if rejected %}
  <p data-level="error">✗ Rejeté — règle <strong>{{ rejected.rule }}</strong> : {{ rejected.message }}</p>
  {% endif %}

  <form method="post" action="/file-validate" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="document" required>
    <button type="submit">Tester la validation</button>
  </form>

  <p>Essayez un <code>.exe</code> (extension), un fichier au mauvais type, ou un fichier
  trop volumineux : chaque refus nomme sa règle.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.file_validate_controller import FileValidateController

with router.group("", public=True) as public:
    public.add("GET", "/file-validate", FileValidateController.index, name="file_validate_index")
    public.add("POST", "/file-validate", FileValidateController.check, name="file_validate_check")
```

### Comprendre ce code

- La hiérarchie `UploadError` permet d'attraper du **plus précis** au **plus
  général** : on nomme la cause exacte, ou on retombe sur « autre ».
- La validation est **partagée** (elle vit dans le core) : même politique pour
  files, images, et tout consommateur.

## À retenir

- Un refus d'upload a une **cause précise** (extension / MIME / taille).
- La hiérarchie d'exceptions permet de la nommer à l'utilisateur.
- Valider, c'est refuser **avant** d'écrire.

## Après ce starter

Vous savez pourquoi un fichier est refusé. La suite : empêcher l'abus de la route.

[Limiter les uploads](file-rate-limit.md)
