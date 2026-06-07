# Miniatures et variantes

Objectif : comprendre **où** Forge range les variantes d'une image (`medium`,
`thumbnail`) et **comment construire leurs URL publiques** — sans rien
téléverser.

**Ce que vous allez apprendre :** `image_variant_relative_paths(path)` dérive,
par simple transformation de chemin, l'originale et ses variantes
(`parent/medium/nom`, `parent/thumbnail/nom`). `media_url(rel)` en fait une URL
publique `/media/...`. C'est une transformation de chaîne **pure** : aucune
écriture, aucune base de données, aucune image réelle requise.

Troisième palier du **niveau débutant** de la progression images.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation » de
    ce parcours).

## Ce que ce starter montre

- la dérivation des chemins de variantes avec `image_variant_relative_paths` ;
- la construction des URL publiques avec `media_url` ;
- l'affichage du tableau originale / `medium` / `thumbnail` pour un chemin donné
  (`GET /image-variants?path=...`) ;
- la même information en JSON (`GET /image-variants/inspect`).

Aucune base de données.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.image_variant_relative_paths` | Dériver les chemins relatifs des variantes. | [Médias](../../../features/media.md) |
| `forge_mvc_images.media_url` | Construire l'URL publique `/media/...`. | [Médias](../../../features/media.md) |
| `forge_mvc_images.IMAGE_VARIANT_SIZES` | Tailles max de chaque variante. | [Médias](../../../features/media.md) |
| `request.query(...)` | Lire le chemin d'image à inspecter. | [Request](../../../reference/http.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-variants` : la page affiche, pour un chemin
d'exemple, l'originale et ses variantes avec leurs URL. Changez de chemin avec
`?path=images/2026/autre.png`.

## Le contrôleur

```python
# mvc/controllers/image_variants_controller.py
from forge_mvc_images import (
    IMAGE_VARIANT_SIZES,
    image_variant_relative_paths,
    media_url,
)

_DEMO_PATH = "images/2026/photo.jpg"


def _variants_view(path: str) -> dict:
    relative = image_variant_relative_paths(path)
    return {
        "path": path,
        "sizes": {name: list(size) for name, size in IMAGE_VARIANT_SIZES.items()},
        "variants": {
            name: {"relative_path": rel, "url": media_url(rel)}
            for name, rel in relative.items()
        },
    }


class ImageVariantsController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        path = request.query("path") or _DEMO_PATH
        return BaseController.render(
            "image_variants/index.html",
            context=_variants_view(path),
            request=request,
        )

    @staticmethod
    def inspect(request: Request) -> Response:
        path = request.query("path") or _DEMO_PATH
        return Response.json(_variants_view(path))
```

### Comprendre ce code

- `image_variant_relative_paths("images/2026/photo.jpg")` retourne
  `{"original": "images/2026/photo.jpg", "medium": "images/2026/medium/photo.jpg",
  "thumbnail": "images/2026/thumbnail/photo.jpg"}` — les variantes vivent dans un
  sous-dossier frère, à côté de l'originale.
- C'est une **convention de nommage**, pas une lecture de disque : la fonction
  ne touche aucun fichier, elle transforme une chaîne. Pratique pour comprendre
  sans rien téléverser.
- `media_url(rel)` préfixe le chemin relatif par `/media/` pour obtenir l'URL
  servie publiquement.

## À retenir

- Les variantes suivent une **convention de chemin** prévisible
  (`parent/<taille>/nom`).
- Dériver un chemin de variante est une transformation **pure**, sans I/O.
- `media_url` fait le pont entre le chemin de stockage et l'URL publique.

## Après ce starter

Vous avez fait le tour du niveau débutant : inspecter le module, téléverser une
image, comprendre ses variantes.

[Bilan du niveau débutant](bilan.md)
