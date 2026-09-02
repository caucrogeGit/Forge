# Miniatures et variantes

Objectif : comprendre **où** Forge range les variantes d'une image (`medium`, `thumbnail`) et **comment construire leurs URL publiques**, sans rien téléverser.

**Ce que vous allez apprendre :** `image_variant_relative_paths(path)` dérive, par simple transformation de chemin, l'originale et ses variantes (`parent/medium/nom`, `parent/thumbnail/nom`).
`media_url(rel)` en fait une URL publique `/media/...`.
C'est une transformation de chaîne **pure** : aucune écriture, aucune base de données, aucune image réelle requise.

Troisième palier du **niveau débutant** de la progression images.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-images` installé.

## Ce que ce starter montre

- la dérivation des chemins de variantes avec `image_variant_relative_paths` ;
- la construction des URL publiques avec `media_url` ;
- l'affichage du tableau originale / `medium` / `thumbnail` pour un chemin donné (`GET /image-variants?path=...`) ;
- la même information en JSON (`GET /image-variants/inspect`).

Aucune base de données.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.image_variant_relative_paths` | Dériver les chemins relatifs des variantes. | Médias |
| `forge_mvc_images.media_url` | Construire l'URL publique `/media/...`. | Médias |
| `forge_mvc_images.variant_presets` | Préréglages de variantes, lus de la configuration. | Médias |
| `request.query(...)` | Lire le chemin d'image à inspecter. | Request |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-variants` : la page affiche, pour un chemin d'exemple, l'originale et ses variantes avec leurs URL.
Changez de chemin avec `?path=images/2026/autre.png`.

## Le contrôleur

```python
# mvc/controllers/image_variants_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import (
    variant_presets,
    image_variant_relative_paths,
    media_url,
)

# Chemin d'exemple : aucune image réelle n'est requise, on illustre la convention.
_DEMO_PATH = "images/2026/photo.jpg"


def _variants_view(path: str) -> dict:
    """Décrit l'originale et ses variantes (chemin relatif + URL publique)."""
    relative = image_variant_relative_paths(path)
    return {
        "path": path,
        "sizes": {p.name: list(p.size) for p in variant_presets()},
        "variants": {
            name: {"relative_path": rel, "url": media_url(rel)}
            for name, rel in relative.items()
        },
    }


class ImageVariantsController(BaseController):
    """Starter pédagogique : comprendre la dérivation des variantes d'image."""

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

- `image_variant_relative_paths("images/2026/photo.jpg")` retourne `{"original": "images/2026/photo.jpg", "medium": "images/2026/medium/photo.jpg", "thumbnail": "images/2026/thumbnail/photo.jpg"}` ; les variantes vivent dans un sous-dossier frère, à côté de l'originale.
- C'est une **convention de nommage**, pas une lecture de disque : la fonction ne touche aucun fichier, elle transforme une chaîne.
  Pratique pour comprendre sans rien téléverser.
- `media_url(rel)` préfixe le chemin relatif par `/media/` pour obtenir l'URL servie publiquement.

## La vue

Le contrôleur rend `image_variants/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_variants/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Miniatures et variantes - Forge</title>
</head>
<body>
  <h1>Miniatures et variantes</h1>

  <p>Image de référence : <code>{{ path }}</code></p>

  <table>
    <thead>
      <tr><th>Variante</th><th>Taille max</th><th>Chemin relatif</th><th>URL publique</th></tr>
    </thead>
    <tbody>
      {% for name, info in variants.items() %}
      <tr>
        <td>{{ name }}</td>
        <td>
          {% if name in sizes %}{{ sizes[name][0] }}×{{ sizes[name][1] }}{% else %}originale{% endif %}
        </td>
        <td><code>{{ info.relative_path }}</code></td>
        <td><code>{{ info.url }}</code></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <p>
    Changez l'image de référence en passant un paramètre :
    <code>/image-variants?path=images/2026/autre.png</code>
  </p>
</body>
</html>
```

## La route

Déclarez les deux routes dans `mvc/routes/__init__.py`, à l'intérieur du groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.image_variants_controller import ImageVariantsController

with router.group("", public=True) as public:
    public.add("GET", "/image-variants", ImageVariantsController.index, name="image_variants_index")
    public.add("GET", "/image-variants/inspect", ImageVariantsController.inspect, name="image_variants_inspect")
```

## À retenir

- Les variantes suivent une **convention de chemin** prévisible (`parent/<taille>/nom`).
- Dériver un chemin de variante est une transformation **pure**, sans I/O.
- `media_url` fait le pont entre le chemin de stockage et l'URL publique.

## Après ce starter

Vous avez fait le tour du niveau débutant : inspecter le module, téléverser une image, comprendre ses variantes.

[Bilan du niveau débutant](bilan.md)
