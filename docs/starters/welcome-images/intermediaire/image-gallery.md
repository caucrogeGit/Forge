# Afficher la galerie

Objectif : lire toutes les images rattachées à une entité et les **afficher
ensemble**, miniatures comprises.

**Ce que vous allez apprendre :** `get_media_gallery` renvoie, pour chaque image
de rôle `gallery` d'une entité, l'URL de l'original **et** celles de ses
variantes (`medium`, `thumbnail`) — prêtes à poser dans des balises `<img>`.

Deuxième palier du **niveau intermédiaire** de la progression images.

!!! note "Module opt-in et table `media`"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation ») et
    la table `media` appliquée (`forge migration:apply`). Si elle manque, la
    page reste **pédagogique**.

## Ce que ce starter montre

- la lecture de la galerie d'une entité avec `get_media_gallery` ;
- l'affichage de chaque image et de sa miniature ;
- une page **pédagogique** si la table `media` n'existe pas encore.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.get_media_gallery` | Lire les médias `gallery` d'une entité, variantes incluses. | [Médias](../../../features/media.md) |
| `BaseController.render` | Rendre la vue de la galerie. | [BaseController](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-gallery` : la page affiche les images
rattachées à l'entité de démo, chacune avec sa miniature.

## Le contrôleur

```python
# mvc/controllers/image_gallery_controller.py
from forge_mvc_images import get_media_gallery

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1


class ImageGalleryController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        try:
            items = get_media_gallery(_ENTITY_NAME, _ENTITY_ID, role="gallery")
        except Exception:
            return BaseController.render(
                "image_gallery/index.html",
                context={"error": "La table media n'est pas encore disponible…"},
                request=request,
            )
        return BaseController.render(
            "image_gallery/index.html", context={"items": items}, request=request
        )
```

### Comprendre ce code

- `get_media_gallery` filtre sur le rôle `gallery` et trie par `Position` : la
  galerie respecte l'ordre que vous fixerez au palier suivant.
- Chaque élément expose `url`, `medium_url`, `thumbnail_url` et `alt_text` : la
  vue n'a plus qu'à choisir la bonne taille selon le contexte.
- On entoure la lecture d'un `try/except` : un starter de découverte ne plante
  pas si la table manque, il **explique**.

## À retenir

- `get_media_gallery` renvoie les images d'une entité **avec** leurs variantes.
- L'ordre d'affichage suit la colonne `Position`.
- Afficher une miniature plutôt que l'original économise de la bande passante.

## Après ce starter

La galerie s'affiche. La suite : la rendre accessible et ordonnée.

[Texte alternatif et ordre](image-alt-order.md)
