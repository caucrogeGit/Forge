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
| `request.param(...)` | Lire le chemin demandé. | [Request](../../../reference/http.md) |

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
from forge_mvc_files import serve_media_file


class FileServeController(BaseController):

    @staticmethod
    def download(request: Request) -> Response:
        path = request.param("path") or ""
        if not path:
            return Response.text("Paramètre « path » requis.", status=400)
        # serve_media_file gère lui-même l'anti-traversal et le 404.
        return serve_media_file(path)
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
