# Afficher la galerie

Objectif : lire toutes les images rattachées à une entité et les **afficher
ensemble**, miniatures comprises.

**Ce que vous allez apprendre :** `get_media_gallery` renvoie, pour chaque image
de rôle `gallery` d'une entité, l'URL de l'original **et** celles de ses
variantes (`medium`, `thumbnail`), prêtes à poser dans des balises `<img>`.

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
| `forge_mvc_images.get_media_gallery` | Lire les médias `gallery` d'une entité, variantes incluses. | Médias |
| `BaseController.render` | Rendre la vue de la galerie. | BaseController |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-gallery` : la page affiche les images
rattachées à l'entité de démo, chacune avec sa miniature.

## Le contrôleur

```python
# mvc/controllers/image_gallery_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import get_media_gallery

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageGalleryController(BaseController):
    """Starter pédagogique : afficher la galerie d'images d'une entité."""

    @staticmethod
    def index(request: Request) -> Response:
        try:
            items = get_media_gallery(_ENTITY_NAME, _ENTITY_ID, role="gallery")
        except Exception:
            return BaseController.render(
                "image_gallery/index.html",
                context={"error": _TABLE_NOT_READY},
                request=request,
            )
        return BaseController.render(
            "image_gallery/index.html",
            context={"items": items},
            request=request,
        )
```

### Comprendre ce code

- `get_media_gallery` filtre sur le rôle `gallery` et trie par `Position` : la
  galerie respecte l'ordre que vous fixerez au palier suivant.
- Chaque élément expose `url`, `medium_url`, `thumbnail_url` et `alt_text` : la
  vue n'a plus qu'à choisir la bonne taille selon le contexte.
- On entoure la lecture d'un `try/except` : un starter de découverte ne plante
  pas si la table manque, il **explique**.

## La vue

Le contrôleur rend `image_gallery/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_gallery/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Galerie d'images - Forge</title>
</head>
<body>
  <h1>Galerie d'images</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  {% if items %}
  <ul>
    {% for item in items %}
    <li>
      <img src="{{ item.thumbnail_url or item.url }}" alt="{{ item.alt_text or '' }}">
      <code>{{ item.path }}</code>
      {% if item.alt_text %}<em>{{ item.alt_text }}</em>{% endif %}
    </li>
    {% endfor %}
  </ul>
  {% elif not error %}
  <p>Aucune image dans la galerie pour l'instant. Téléversez-en une via le palier
  « Rattacher une image à une entité ».</p>
  {% endif %}
</body>
</html>
```

## La migration

Ce palier lit la table `media`. Si vous ne l'avez pas encore créée au palier
précédent, créez le fichier de migration suivant sous `mvc/migrations/`, puis
appliquez-le avec `forge migration:apply`.

```sql
-- mvc/migrations/20260605101000_create_media.sql
CREATE TABLE IF NOT EXISTS media (
    Id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    EntityName VARCHAR(100) NOT NULL,
    EntityId INT NOT NULL,
    Path VARCHAR(500) NOT NULL,
    OriginalName VARCHAR(255) NOT NULL,
    MimeType VARCHAR(120) NOT NULL,
    Size INT NOT NULL,
    Role VARCHAR(50) NOT NULL DEFAULT 'default',
    Position INT NOT NULL DEFAULT 0,
    AltText VARCHAR(255) NULL,
    CreatedAt DATETIME NOT NULL,
    PRIMARY KEY (Id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## La route

Déclarez la route dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.image_gallery_controller import ImageGalleryController

with router.group("", public=True) as public:
    public.add("GET", "/image-gallery", ImageGalleryController.index, name="image_gallery_index")
```

## À retenir

- `get_media_gallery` renvoie les images d'une entité **avec** leurs variantes.
- L'ordre d'affichage suit la colonne `Position`.
- Afficher une miniature plutôt que l'original économise de la bande passante.

## Après ce starter

La galerie s'affiche. La suite : la rendre accessible et ordonnée.

[Texte alternatif et ordre](image-alt-order.md)
