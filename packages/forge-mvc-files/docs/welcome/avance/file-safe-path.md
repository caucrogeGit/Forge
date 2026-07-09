# Chemin anti-traversal

Objectif : juger si un **chemin** reste à l'intérieur de la racine d'upload : la défense contre la traversée de répertoire.

**Ce que vous allez apprendre :** `is_safe_media_path(path)` répond oui/non, `normalize_media_path(path)` renvoie un chemin relatif sûr ou **refuse** (`UploadStorageError`).
Ce sont les primitives que `serve_media_file` et `delete_media_file` utilisent en interne.

Deuxième palier du **niveau avancé** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé.

## Ce que ce starter montre

- `is_safe_media_path(path)` : verdict de sûreté ;
- `normalize_media_path(path)` : chemin normalisé ou refus ;
- une transformation **pure** (aucune lecture/écriture).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.is_safe_media_path` | Dire si un chemin reste dans la racine d'upload. | Médias |
| `forge_mvc_files.normalize_media_path` | Normaliser un chemin sûr (ou refuser). | Médias |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-safe-path` et comparez `documents/a.pdf` (sûr) et `../../etc/passwd` (refusé).

## Le contrôleur

```python
# mvc/controllers/file_safe_path_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError, is_safe_media_path, normalize_media_path

_DEMO_PATH = "../../etc/passwd"


def _path_view(path: str) -> dict:
    try:
        normalized = normalize_media_path(path)
    except UploadError:
        normalized = None
    return {
        "input": path,
        "is_safe": bool(is_safe_media_path(path)),
        "normalized": normalized,
    }


class FileSafePathController(BaseController):
    """Starter pédagogique : juger la sûreté d'un chemin de fichier."""

    @staticmethod
    def index(request: Request) -> Response:
        path = request.query("path") or _DEMO_PATH
        return BaseController.render(
            "file_safe_path/index.html", context=_path_view(path), request=request
        )

    @staticmethod
    def inspect(request: Request) -> Response:
        path = request.query("path") or _DEMO_PATH
        return Response.json(_path_view(path))
```

## La vue

```html
<!-- mvc/views/file_safe_path/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Chemin anti-traversal - Forge</title>
</head>
<body>
  <h1>Chemin anti-traversal</h1>

  <form method="get" action="/file-safe-path">
    <input type="text" name="path" value="{{ input }}" size="50">
    <button type="submit">Vérifier</button>
  </form>

  <p>Chemin : <code>{{ input }}</code></p>
  <ul>
    <li>Sûr (reste dans la racine d'upload) : <strong>{% if is_safe %}oui{% else %}non{% endif %}</strong></li>
    <li>Normalisé : {% if normalized %}<code>{{ normalized }}</code>{% else %}<em>refusé</em>{% endif %}</li>
  </ul>

  <p>Essayez <code>documents/a.pdf</code> (sûr) puis <code>../../etc/passwd</code>
  (refusé) : c'est cette garde qui empêche de servir ou supprimer un fichier hors
  de la zone d'upload.</p>
</body>
</html>
```

## La route

```python
# mvc/routes.py
from mvc.controllers.file_safe_path_controller import FileSafePathController

with router.group("", public=True) as public:
    public.add("GET", "/file-safe-path", FileSafePathController.index, name="file_safe_path_index")
    public.add("GET", "/file-safe-path/inspect", FileSafePathController.inspect, name="file_safe_path_inspect")
```

### Comprendre ce code

- `../../etc/passwd` est jugé **non sûr** et **refusé** à la normalisation : c'est exactement ce qui empêche de servir ou supprimer un fichier hors zone.
- Ces deux fonctions sont les **primitives** sous `serve_media_file` / `delete_media_file` : la garde est écrite **une fois**, réutilisée partout.

## À retenir

- L'anti-traversal repose sur `is_safe_media_path` + `normalize_media_path`.
- Un chemin piégé est **refusé**, pas « corrigé »
  silencieusement.
- Sécurité écrite **une fois**, composée par tout le module (et les opt-ins média).

## Après ce starter

Vous comprenez la garde de chemin.
Dernier palier : écrire des octets générés.

[Écrire des octets générés](file-bytes.md)
