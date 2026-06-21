# Stocker un document

Objectif : recevoir un fichier et le **stocker** proprement avec `save_upload`.

**Ce que vous allez apprendre :** `save_upload` est la **façade document** de
`forge-mvc-files` — elle valide (extension/MIME/taille), écrit le fichier sur le
disque et retourne un `SavedUpload` décrivant ce qui a été stocké. C'est exactement
la primitive qu'`forge-mvc-images` réutilise pour son chemin document.

Deuxième palier du **niveau débutant** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé (palier « Installation »).

## Ce que ce starter montre

- un formulaire `multipart/form-data` (avec CSRF) ;
- `save_upload(uploaded, "documents")` : valide, écrit, retourne un `SavedUpload` ;
- l'affichage du nom, du chemin, de la taille et du type MIME.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.save_upload` | Valider, écrire, retourner un `SavedUpload`. | [Médias](../../../features/media.md) |
| `forge_mvc_files.UploadError` | Erreur levée si le fichier est refusé. | [Médias](../../../features/media.md) |
| `request.file(...)` | Récupérer le fichier envoyé. | [Request](../../../reference/http.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-store`, envoyez un fichier autorisé (`.pdf`,
`.png`…) : la page affiche le `SavedUpload` (nom, chemin, taille, type).

## Le contrôleur

```python
# mvc/controllers/file_store_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError, save_upload


class FileStoreController(BaseController):
    """Starter pédagogique : stocker un document générique."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_store/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def store(request: Request) -> Response:
        uploaded = request.file("document")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render(
                "file_store/index.html", context=context, request=request
            )
        try:
            saved = save_upload(uploaded, "documents")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "file_store/index.html", context=context, request=request
            )
        context["saved"] = saved
        return BaseController.render(
            "file_store/index.html", context=context, request=request
        )
```

## La vue

```html
<!-- mvc/views/file_store/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Stocker un document — Forge</title>
</head>
<body>
  <h1>Stocker un document</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  {% if saved %}
  <p data-level="success">Document stocké :</p>
  <ul>
    <li>Nom d'origine : <strong>{{ saved.original_name }}</strong></li>
    <li>Chemin : <code>{{ saved.path }}</code></li>
    <li>Taille : {{ saved.size }} octets</li>
    <li>Type MIME : <code>{{ saved.mime_type }}</code></li>
  </ul>
  {% endif %}

  <form method="post" action="/file-store" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="document" required>
    <button type="submit">Stocker</button>
  </form>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.file_store_controller import FileStoreController

with router.group("", public=True) as public:
    public.add("GET", "/file-store", FileStoreController.index, name="file_store_index")
    public.add("POST", "/file-store", FileStoreController.store, name="file_store_save")
```

### Comprendre ce code

- La **catégorie** (`"documents"`) range le fichier dans un sous-dossier dédié de
  la racine d'upload.
- `SavedUpload` expose `original_name`, `path`, `size`, `mime_type` — tout ce qu'il
  faut pour, plus tard, le servir ou l'enregistrer en base (côté application).
- La validation est **dans le core** (réexportée par files) : un fichier refusé
  lève `UploadError` avant toute écriture.

## À retenir

- `save_upload` = valider **puis** écrire, jamais l'inverse.
- Le `SavedUpload` décrit le fichier stocké (nom, chemin, taille, type).
- C'est la façade « document » ; le chemin image-aware vit dans `forge-mvc-images`.

## Après ce starter

Le document est stocké. La suite : le **relire** sans faille de chemin.

[Servir un fichier](file-serve.md)
