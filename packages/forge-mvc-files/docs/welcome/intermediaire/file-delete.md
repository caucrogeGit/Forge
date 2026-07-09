# Supprimer un fichier

Objectif : supprimer un fichier stocké avec `delete_media_file`, sans jamais sortir de la racine d'upload.

**Ce que vous allez apprendre :** `delete_media_file` prend un **chemin relatif**, reste à l'intérieur de la zone d'upload (anti-traversal) et retourne un compte rendu de ce qui a été supprimé.

Troisième palier du **niveau intermédiaire** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé.

## Ce que ce starter montre

- un formulaire avec le chemin du fichier à supprimer ;
- `delete_media_file(path)` et son compte rendu (`{"original": True/False}`) ;
- la même garde anti-traversal que pour servir.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.delete_media_file` | Supprimer un fichier par son chemin relatif. | Médias |
| `request.form(...)` | Lire le chemin soumis. | Request |

## Tester

```bash
forge run
```

Stockez un fichier, puis supprimez-le via son chemin sur `https://localhost:8000/file-delete`.
Un chemin hors zone est refusé.

## Le contrôleur

```python
# mvc/controllers/file_delete_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import delete_media_file


class FileDeleteController(BaseController):
    """Starter pédagogique : supprimer un fichier stocké, sans faille de chemin."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_delete/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def delete(request: Request) -> Response:
        path = request.form("path")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if not path:
            context["error"] = "Indiquez le chemin du fichier à supprimer."
            return BaseController.render(
                "file_delete/index.html", context=context, request=request
            )
        try:
            result = delete_media_file(path)
        except Exception:
            context["error"] = "Chemin invalide ou hors de la racine d'upload."
            return BaseController.render(
                "file_delete/index.html", context=context, request=request
            )
        if result.get("original"):
            context["deleted"] = path
        else:
            context["not_found"] = path
        return BaseController.render(
            "file_delete/index.html", context=context, request=request
        )
```

## La vue

```html
<!-- mvc/views/file_delete/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Supprimer un fichier - Forge</title>
</head>
<body>
  <h1>Supprimer un fichier</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if deleted %}
  <p data-level="success">Supprimé : <code>{{ deleted }}</code></p>
  {% endif %}
  {% if not_found %}
  <p data-level="error">Aucun fichier à <code>{{ not_found }}</code> (déjà absent ?).</p>
  {% endif %}

  <form method="post" action="/file-delete">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="text" name="path" placeholder="documents/..." required>
    <button type="submit">Supprimer</button>
  </form>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.file_delete_controller import FileDeleteController

with router.group("", public=True) as public:
    public.add("GET", "/file-delete", FileDeleteController.index, name="file_delete_index")
    public.add("POST", "/file-delete", FileDeleteController.delete, name="file_delete_remove")
```

### Comprendre ce code

- Le compte rendu (`{"original": ...}`) dit si le fichier existait : la suppression est **idempotente**, supprimer un absent ne plante pas.
- La garde anti-traversal est la **même primitive** que pour servir : on ne supprime jamais hors de la racine d'upload.

## À retenir

- Supprimer = donner le **chemin relatif** à `delete_media_file`.
- Opération **idempotente** et **anti-traversal**.
- Stocker, servir, supprimer : le cycle de vie complet d'un fichier.

## Après ce starter

Vous maîtrisez le cycle de vie.
La suite : les **primitives** de sécurité qui le sous-tendent.

[Bilan du niveau intermédiaire](bilan.md)
