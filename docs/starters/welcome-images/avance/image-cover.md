# Image de couverture

Objectif : désigner **une** image mise en avant pour une entité — sa couverture
— et l'afficher.

**Ce que vous allez apprendre :** Forge distingue les médias par leur **rôle**.
Une couverture est un média de rôle `cover` (≠ `gallery`). `get_cover_media` la
lit, avec repli optionnel sur la première image de la galerie si aucune
couverture explicite n'existe.

Premier palier du **niveau avancé** de la progression images.

!!! note "Module opt-in et table `media`"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation ») et
    la table `media` appliquée (`forge migration:apply`). Si elle manque, la
    page reste **pédagogique**.

## Ce que ce starter montre

- la lecture de la couverture avec `get_cover_media` (rôle `cover`) ;
- le repli sur la galerie (`fallback_to_gallery=True`) ;
- la désignation d'une couverture (upload + `attach_media_to_entity` rôle `cover`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.get_cover_media` | Lire la couverture d'une entité (repli galerie). | [Médias](../../../features/media.md) |
| `forge_mvc_images.attach_media_to_entity` | Rattacher une image en rôle `cover`. | [Médias](../../../features/media.md) |
| `forge_mvc_images.save_image_upload` | Vérifier, écrire, générer les variantes. | [Médias](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-cover` : la page affiche la couverture
courante et permet d'en définir une nouvelle.

## Le contrôleur

```python
# mvc/controllers/image_cover_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import attach_media_to_entity, get_cover_media, save_image_upload

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageCoverController(BaseController):
    """Starter pédagogique : désigner et afficher l'image de couverture."""

    @staticmethod
    def _render(request: Request, **extra) -> Response:
        context = {"csrf_token": BaseController.csrf_token(request)}
        context.update(extra)
        if "error" not in context:
            try:
                context["cover"] = get_cover_media(
                    _ENTITY_NAME, _ENTITY_ID, role="cover", fallback_to_gallery=True
                )
            except Exception:
                context["error"] = _TABLE_NOT_READY
        return BaseController.render(
            "image_cover/index.html", context=context, request=request
        )

    @staticmethod
    def index(request: Request) -> Response:
        return ImageCoverController._render(request)

    @staticmethod
    def set_cover(request: Request) -> Response:
        uploaded = request.file("image")
        if uploaded is None:
            return ImageCoverController._render(request, error="Aucune image sélectionnée.")
        try:
            saved = save_image_upload(uploaded, "images")
        except UploadError as exc:
            return ImageCoverController._render(request, error=str(exc))
        try:
            attach_media_to_entity(
                saved, entity_name=_ENTITY_NAME, entity_id=_ENTITY_ID, role="cover"
            )
        except Exception:
            return ImageCoverController._render(request, error=_TABLE_NOT_READY)
        return ImageCoverController._render(request, updated="Couverture mise à jour.")
```

### Comprendre ce code

- Le **rôle** est la clé : une même entité peut avoir une galerie (`gallery`) et
  une couverture (`cover`), distinguées par cette seule colonne.
- `fallback_to_gallery=True` rend l'affichage robuste : pas de couverture
  explicite ? On montre la première image de la galerie.
- Désigner une couverture, c'est simplement rattacher un média avec le bon rôle.

## La vue

Le contrôleur rend `image_cover/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_cover/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Image de couverture — Forge</title>
</head>
<body>
  <h1>Image de couverture</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if updated %}
  <p data-level="success">{{ updated }}</p>
  {% endif %}

  {% if cover %}
  <figure>
    <img src="{{ cover.medium_url or cover.url }}" alt="{{ cover.alt_text or '' }}">
    <figcaption><code>{{ cover.path }}</code> (rôle <code>{{ cover.role }}</code>)</figcaption>
  </figure>
  {% elif not error %}
  <p>Aucune couverture pour l'instant.</p>
  {% endif %}

  <form method="post" action="/image-cover" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="image" accept="image/*" required>
    <button type="submit">Définir comme couverture</button>
  </form>
</body>
</html>
```

## La migration

Ce palier utilise la table `media`. Si vous ne l'avez pas encore créée, créez le
fichier de migration suivant sous `mvc/migrations/`, puis appliquez-le avec
`forge migration:apply`.

```sql
-- mvc/migrations/20260605110000_create_media.sql
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
from mvc.controllers.image_cover_controller import ImageCoverController

with router.group("", public=True) as public:
    public.add("GET", "/image-cover", ImageCoverController.index, name="image_cover_index")
    public.add("POST", "/image-cover", ImageCoverController.set_cover, name="image_cover_set")
```

## À retenir

- La couverture est un média de **rôle** `cover`, lu par `get_cover_media`.
- Le repli sur la galerie évite une page vide quand aucune couverture n'est posée.
- Le rôle classe les médias sans table supplémentaire.

## Après ce starter

La couverture est en place. La suite : supprimer une image proprement.

[Supprimer proprement](image-delete.md)
