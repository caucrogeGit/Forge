# Servir un fichier

Objectif : **relire** un fichier stocké via `serve_media_file`, sans jamais
laisser sortir de la racine d'upload.

**Ce que vous allez apprendre :** `serve_media_file` prend un **chemin relatif**,
vérifie qu'il reste dans la racine d'upload (anti-traversal), et renvoie le fichier
— ou `404` s'il est absent ou le chemin invalide.

Troisième palier du **niveau débutant** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé (palier « Installation »).

## Ce que ce starter montre

- une page d'explication + un champ pour un chemin de fichier ;
- `serve_media_file(path)` qui renvoie le fichier (ou `404`) ;
- la protection **anti-traversal** intégrée (un `../` est refusé).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.serve_media_file` | Servir un fichier par son chemin relatif, anti-traversal + 404. | [Médias](../../../features/media.md) |
| `request.query(...)` | Lire le chemin demandé. | [Request](../../../reference/http.md) |

## Tester

```bash
forge run
```

Stockez un fichier au palier précédent, notez son chemin, puis ouvrez
`https://localhost:8000/file-serve` et demandez-le. Un chemin `../secret` est
refusé (`404`).

## Le contrôleur

```python
# mvc/controllers/file_serve_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import serve_media_file


class FileServeController(BaseController):
    """Starter pédagogique : servir un fichier stocké, sans faille de chemin."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_serve/index.html", context={}, request=request
        )

    @staticmethod
    def download(request: Request) -> Response:
        path = request.query("path") or ""
        if not path:
            return Response.text("Paramètre « path » requis.", status=400)
        # serve_media_file gère lui-même l'anti-traversal et le 404.
        return serve_media_file(path)
```

## La vue

```html
<!-- mvc/views/file_serve/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Servir un fichier — Forge</title>
</head>
<body>
  <h1>Servir un fichier</h1>

  <p>
    Indiquez le <strong>chemin relatif</strong> d'un fichier stocké (celui
    renvoyé par le palier « Stocker un document », p. ex.
    <code>documents/mon-fichier-abcd.pdf</code>).
  </p>

  <form method="get" action="/file-serve/download">
    <input type="text" name="path" placeholder="documents/..." required>
    <button type="submit">Télécharger</button>
  </form>

  <p>
    Un chemin qui tente de sortir de la racine d'upload (p. ex.
    <code>../secret</code>) est <strong>refusé</strong> : <code>serve_media_file</code>
    protège contre la traversée de répertoire et répond <code>404</code>.
  </p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.file_serve_controller import FileServeController

with router.group("", public=True) as public:
    public.add("GET", "/file-serve", FileServeController.index, name="file_serve_index")
    public.add("GET", "/file-serve/download", FileServeController.download, name="file_serve_download")
```

### Comprendre ce code

- On passe un **chemin relatif** (celui du `SavedUpload.path`), jamais un chemin
  absolu : `serve_media_file` résout par rapport à la racine d'upload.
- L'anti-traversal est **dans la primitive**, pas dans le contrôleur : impossible
  d'oublier la garde.
- Fichier absent ou chemin piégé → `404`, jamais une fuite hors zone.

## À retenir

- Servir un fichier = donner son **chemin relatif** à `serve_media_file`.
- La protection anti-traversal est **portée par la primitive**.
- Stocker (`save_upload`) et servir (`serve_media_file`) sont les deux faces du
  cycle de vie d'un fichier.

## Après ce starter

Vous savez stocker et servir. La suite : comprendre **pourquoi** un fichier est
parfois refusé.

[Bilan du niveau débutant](bilan.md)
