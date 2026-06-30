# Welcome Files

Objectif : premier contact avec le module **opt-in** `forge-mvc-files`, le
pipeline d'upload générique de Forge.

**Ce que vous allez apprendre :** vérifier que le module répond et **inspecter sa
politique** : racine de stockage (`upload_root`), extensions, types MIME et taille
max autorisés. Aucune base de données : `forge-mvc-files` est sans état.

Premier palier du **niveau débutant** de la progression files
(vue d'ensemble des starters).

!!! note "Module opt-in et fondation"
    `forge-mvc-files` est l'upload générique extrait du core (ADR-019) ; c'est la
    **fondation** sur laquelle `forge-mvc-images` est bâti. Ce parcours en montre
    la façade `save_upload` (documents) puis, au niveau avancé, les **primitives**
    que les opt-ins média composent (ADR-020). Installé depuis les sources (palier
    « Installation »).

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /files-welcome`) ;
- la lecture de la politique d'upload (`upload_root`, extensions, MIME, taille) ;
- sa sérialisation JSON (`GET /files-welcome/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_files.upload_root` | Racine de stockage des fichiers. | Médias |
| `core.forge.get` | Lire la politique d'upload (extensions, MIME, taille). | Configuration |
| `Response.text` / `Response.json` | Renvoyer du texte puis du JSON. | Response |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/files-welcome` (« Welcome Files »), puis
`/files-welcome/inspect` pour la politique d'upload en JSON.

## Le contrôleur

```python
# mvc/controllers/files_welcome_controller.py
from core.forge import get as get_config
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import upload_root


def _capabilities() -> dict:
    """Décrit où et quoi forge-mvc-files accepte de stocker."""
    return {
        "upload_root": str(upload_root()),
        "allowed_extensions": sorted(get_config("upload_allowed_extensions")),
        "allowed_mime_types": sorted(get_config("upload_allowed_mime_types")),
        "max_size_bytes": int(get_config("upload_max_size")),
    }


class FilesWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Files."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Welcome Files")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_capabilities())
```

## La route

```python
# mvc/routes.py
from mvc.controllers.files_welcome_controller import FilesWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/files-welcome", FilesWelcomeController.index, name="files_welcome_index")
    public.add("GET", "/files-welcome/inspect", FilesWelcomeController.inspect, name="files_welcome_inspect")
```

### Comprendre ce code

- La politique d'upload (extensions, MIME, taille) vit dans la **config Forge**
  (`core.forge.get`) : elle est explicite et modifiable, pas codée en dur.
- `upload_root()` donne la racine sous laquelle tout fichier est stocké : tout le
  reste du parcours s'y rapporte.

## À retenir

- `forge-mvc-files` est **opt-in** et **sans état** : il gère des fichiers sur
  disque, rien en base.
- C'est la **fondation** générique ; image en est le premier client.
- La politique d'upload est explicite (config).

## Après ce starter

Premier contact établi. La suite : stocker un vrai document.

[Stocker un document](file-store.md)
