# Texte alternatif et ordre

Objectif : rendre la galerie **accessible** et **ordonnée** en éditant deux champs d'une image : son texte alternatif et sa position.

**Ce que vous allez apprendre :** `update_media_alt_text` renseigne le texte lu par les lecteurs d'écran (`alt_text`), `update_media_position` fixe l'ordre d'affichage (`position`).
Deux écritures ciblées sur une ligne `media`.

Troisième palier du **niveau intermédiaire** de la progression images.

!!! note "Module opt-in et table `media`"
    Ce starter suppose `forge-mvc-images` installé
    et la table `media` appliquée (`forge migration:apply`).
    Si elle manque, la page reste **pédagogique**.

## Ce que ce starter montre

- la liste des images d'une entité avec un formulaire d'édition par image ;
- `update_media_alt_text` pour l'accessibilité ;
- `update_media_position` pour l'ordre d'affichage.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.list_media_for_entity` | Lister les images à éditer. | Médias |
| `forge_mvc_images.update_media_alt_text` | Renseigner le texte alternatif. | Médias |
| `forge_mvc_images.update_media_position` | Fixer l'ordre d'affichage. | Médias |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-alt-order`, renseignez un texte alternatif et une position, enregistrez : la galerie reflète l'ordre et l'accessibilité.

## Le contrôleur

```python
# mvc/controllers/image_alt_order_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import (
    list_media_for_entity,
    update_media_alt_text,
    update_media_position,
)

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageAltOrderController(BaseController):
    """Starter pédagogique : éditer accessibilité et ordre des médias."""

    @staticmethod
    def _render(request: Request, **extra) -> Response:
        context = {"csrf_token": BaseController.csrf_token(request)}
        context.update(extra)
        try:
            context["items"] = list_media_for_entity(
                _ENTITY_NAME, _ENTITY_ID, role="gallery"
            )
        except Exception:
            context["error"] = _TABLE_NOT_READY
        return BaseController.render(
            "image_alt_order/index.html", context=context, request=request
        )

    @staticmethod
    def index(request: Request) -> Response:
        return ImageAltOrderController._render(request)

    @staticmethod
    def update(request: Request) -> Response:
        media_id = request.form("media_id")
        alt_text = request.form("alt_text")
        position = request.form("position")
        if not media_id:
            return ImageAltOrderController._render(
                request, error="Aucune image sélectionnée."
            )
        try:
            update_media_alt_text(int(media_id), alt_text or None)
            update_media_position(int(media_id), int(position or 0))
        except Exception:
            return ImageAltOrderController._render(request, error=_TABLE_NOT_READY)
        return ImageAltOrderController._render(
            request, updated=f"Image #{media_id} mise à jour."
        )
```

### Comprendre ce code

- `alt_text` est un enjeu d'**accessibilité** : un lecteur d'écran l'annonce à la place de l'image.
  Le module le limite à 255 caractères.
- `position` pilote l'ordre : `get_media_gallery` trie dessus, l'effet est donc immédiat à l'affichage.
- Les deux écritures ciblent une ligne précise par son identifiant `media_id`.

## La vue

Le contrôleur rend `image_alt_order/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_alt_order/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Texte alternatif et ordre - Forge</title>
</head>
<body>
  <h1>Texte alternatif et ordre</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if updated %}
  <p data-level="success">{{ updated }}</p>
  {% endif %}

  {% if items %}
  {% for item in items %}
  <form method="post" action="/image-alt-order">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="hidden" name="media_id" value="{{ item.id }}">
    <code>#{{ item.id }} - {{ item.path }}</code>
    <label>Texte alternatif
      <input type="text" name="alt_text" value="{{ item.alt_text or '' }}" maxlength="255">
    </label>
    <label>Position
      <input type="number" name="position" value="{{ item.position or 0 }}" min="0">
    </label>
    <button type="submit">Enregistrer</button>
  </form>
  {% endfor %}
  {% elif not error %}
  <p>Aucune image à éditer. Téléversez-en une via le palier « Rattacher une image
  à une entité ».</p>
  {% endif %}
</body>
</html>
```

## La migration

Ce palier édite la table `media`.
Si vous ne l'avez pas encore créée, créez le fichier de migration suivant sous `mvc/migrations/`, puis appliquez-le avec `forge migration:apply`.

```sql
-- mvc/migrations/20260605102000_create_media.sql
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

Déclarez les deux routes dans `mvc/routes.py`, à l'intérieur du groupe public.

```python
# mvc/routes.py
from mvc.controllers.image_alt_order_controller import ImageAltOrderController

with router.group("", public=True) as public:
    public.add("GET", "/image-alt-order", ImageAltOrderController.index, name="image_alt_order_index")
    public.add("POST", "/image-alt-order", ImageAltOrderController.update, name="image_alt_order_update")
```

## À retenir

- Une galerie sérieuse est **accessible** (`alt_text`) et **ordonnée** (`position`).
- `update_media_alt_text` et `update_media_position` modifient une ligne `media` ciblée.
- L'ordre fixé ici est respecté par `get_media_gallery`.

## Après ce starter

Vous avez fait le tour du niveau intermédiaire : rattacher, afficher, ordonner.

[Bilan du niveau intermédiaire](bilan.md)
