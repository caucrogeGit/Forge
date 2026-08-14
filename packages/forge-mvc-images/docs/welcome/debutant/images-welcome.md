# Welcome Images

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-images` avant de commencer : voir sa [référence](../../reference.md).

    ```bash
    pip install --pre forge-mvc-images    # installe le paquet
    forge opt-in:enable images          # le branche au projet
    ```

    Sans le paquet, l'application refuse de démarrer sur un `ModuleNotFoundError` au chargement des routes.

    `forge opt-in:install images` **affiche** la commande d'installation adaptée à votre environnement, pipx compris ; il n'installe rien lui-même (ADR-016).

Objectif : premier contact avec le module **opt-in** `forge-mvc-images` et ce qu'il sait traiter.

**Ce que vous allez apprendre :** vérifier que le module Images répond, et **inspecter ses capacités** : les formats d'image autorisés (`ALLOWED_IMAGE_EXTENSIONS`) et les tailles des variantes générées (`IMAGE_VARIANT_SIZES`).
Aucune base de données, aucun fichier : on découvre simplement comment Forge Images est branché.

Premier palier du **niveau débutant** de la progression images (vue d'ensemble des starters).

!!! note "Module opt-in"
    Ce starter suppose le module installé.
    `forge-mvc-images` dépend de `forge-mvc-files` et il est publié sur PyPI depuis `1.0.0-beta.13` (`pip install --pre forge-mvc-images`
    de ce parcours, en tête de progression).
    Le cœur de Forge reste autonome ; l'image est une brique que l'on ajoute à la demande.

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /images-welcome`) ;
- la lecture des constantes du module (`ALLOWED_IMAGE_EXTENSIONS`, `ALLOWED_IMAGE_MIME_TYPES`, `IMAGE_VARIANT_SIZES`) ;
- la sérialisation JSON de ces capacités (`GET /images-welcome/inspect`).

Aucune écriture, aucune base de données.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.ALLOWED_IMAGE_EXTENSIONS` | Formats d'image acceptés à l'upload. | Médias |
| `forge_mvc_images.IMAGE_VARIANT_SIZES` | Tailles des variantes générées (`medium`, `thumbnail`). | Médias |
| `Response.text` / `Response.json` | Renvoyer du texte puis du JSON. | Response |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/images-welcome` : la page affiche **« Welcome Images »**.
Puis `https://localhost:8000/images-welcome/inspect` renvoie les formats acceptés et les tailles de variantes en JSON.

## Le contrôleur

```python
# mvc/controllers/images_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIME_TYPES,
    IMAGE_VARIANT_SIZES,
)


def _capabilities() -> dict:
    """Décrit ce que forge-mvc-images sait accepter et produire."""
    return {
        "allowed_extensions": sorted(ALLOWED_IMAGE_EXTENSIONS),
        "allowed_mime_types": sorted(ALLOWED_IMAGE_MIME_TYPES),
        "variant_sizes": {
            name: list(size) for name, size in IMAGE_VARIANT_SIZES.items()
        },
    }


class ImagesWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Images."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Welcome Images")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_capabilities())
```

### Comprendre ce code

- Les constantes `ALLOWED_IMAGE_*` sont la **liste blanche** du module : tout ce qui n'y figure pas est refusé à l'upload.
  On les expose ici pour découvrir ce que Forge Images accepte.
- `IMAGE_VARIANT_SIZES` décrit les déclinaisons que le module génère automatiquement à l'upload : `medium` (1280×1280) et `thumbnail` (300×300).
- Les `frozenset` sont triés (`sorted(...)`) pour une sortie JSON stable.

## La route

Déclarez les deux routes dans `mvc/routes/__init__.py`, à l'intérieur du groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.images_welcome_controller import ImagesWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/images-welcome", ImagesWelcomeController.index, name="images_welcome_index")
    public.add("GET", "/images-welcome/inspect", ImagesWelcomeController.inspect, name="images_welcome_inspect")
```

## À retenir

- Le module Images est **opt-in** : on l'installe à la demande, le cœur reste autonome.
- Les formats acceptés et les tailles de variantes sont **explicites**, lisibles via des constantes du module.
- Inspecter les capacités d'une brique avant de l'utiliser est un bon réflexe.

## Après ce starter

Premier contact établi.
La suite : téléverser une vraie image.

[Téléverser une image](image-upload.md)
