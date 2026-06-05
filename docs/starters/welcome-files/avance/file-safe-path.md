# Chemin anti-traversal

Objectif : juger si un **chemin** reste à l'intérieur de la racine d'upload — la
défense contre la traversée de répertoire.

**Ce que vous allez apprendre :** `is_safe_media_path(path)` répond oui/non,
`normalize_media_path(path)` renvoie un chemin relatif sûr ou **refuse**
(`UploadStorageError`). Ce sont les primitives que `serve_media_file` et
`delete_media_file` utilisent en interne.

Deuxième palier du **niveau avancé** de la progression files.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-files` installé (palier « Installation »).

## Ce que ce starter montre

- `is_safe_media_path(path)` : verdict de sûreté ;
- `normalize_media_path(path)` : chemin normalisé ou refus ;
- une transformation **pure** (aucune lecture/écriture).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.is_safe_media_path` | Dire si un chemin reste dans la racine d'upload. | [Médias](../../../features/media.md) |
| `forge_mvc_files.normalize_media_path` | Normaliser un chemin sûr (ou refuser). | [Médias](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/file-safe-path` et comparez `documents/a.pdf` (sûr)
et `../../etc/passwd` (refusé).

## Le contrôleur

```python
# mvc/controllers/file_safe_path_controller.py
from forge_mvc_files import UploadError, is_safe_media_path, normalize_media_path


def _path_view(path: str) -> dict:
    try:
        normalized = normalize_media_path(path)
    except UploadError:
        normalized = None
    return {"input": path, "is_safe": bool(is_safe_media_path(path)), "normalized": normalized}


class FileSafePathController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        path = request.param("path") or "../../etc/passwd"
        return BaseController.render("file_safe_path/index.html", context=_path_view(path), request=request)
```

### Comprendre ce code

- `../../etc/passwd` est jugé **non sûr** et **refusé** à la normalisation : c'est
  exactement ce qui empêche de servir ou supprimer un fichier hors zone.
- Ces deux fonctions sont les **primitives** sous `serve_media_file` /
  `delete_media_file` : la garde est écrite **une fois**, réutilisée partout.

## À retenir

- L'anti-traversal repose sur `is_safe_media_path` + `normalize_media_path`.
- Un chemin piégé est **refusé**, pas « corrigé » silencieusement.
- Sécurité écrite **une fois**, composée par tout le module (et les opt-ins média).

## Après ce starter

Vous comprenez la garde de chemin. Dernier palier : écrire des octets générés.

[Écrire des octets générés](file-bytes.md)
