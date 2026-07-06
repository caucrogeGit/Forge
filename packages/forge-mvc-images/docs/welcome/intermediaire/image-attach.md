# Rattacher une image à une entité

Objectif : faire entrer l'image **en base**.
Jusqu'ici elle vivait sur le disque ; on crée maintenant une ligne `media` qui la relie à une entité.

**Ce que vous allez apprendre :** après l'upload (`save_image_upload`), `attach_media_to_entity` crée une ligne dans la table `media` reliée à une entité par `(EntityName, EntityId)` et un `role`.
Une image appartient toujours à « quelque chose ».

Premier palier du **niveau intermédiaire** de la progression images.

!!! note "Module opt-in et table `media`"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation »).
    La table `media` est créée par la **migration livrée avec le starter** : appliquez-la avec `forge migration:apply`.
    Si la table manque, la route reste **pédagogique** au lieu de planter.

## Ce que ce starter montre

- un formulaire d'upload (CSRF) ;
- `save_image_upload` pour vérifier + écrire + générer les variantes ;
- `attach_media_to_entity` pour créer la ligne `media` (rôle `gallery`) ;
- l'affichage de l'identifiant média attribué, ou d'un message pédagogique si la table n'existe pas encore.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.save_image_upload` | Vérifier, écrire, générer les variantes. | Médias |
| `forge_mvc_images.attach_media_to_entity` | Créer la ligne `media` reliée à l'entité. | Médias |
| `request.file(...)` | Récupérer l'image envoyée. | Request |

## Tester

Appliquez d'abord la migration (`forge migration:apply`), puis :

```bash
forge run
```

Ouvrez `https://localhost:8000/image-attach`, envoyez une image : la page confirme la création de la ligne `media` avec son identifiant.

## Le contrôleur

```python
# mvc/controllers/image_attach_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import attach_media_to_entity, save_image_upload

# Entité de démo neutre : la table `media` n'impose aucune clé étrangère, on
# illustre le rattachement sans dépendre d'une entité métier réelle.
_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageAttachController(BaseController):
    """Starter pédagogique : relier une image uploadée à une entité en base."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "image_attach/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def attach(request: Request) -> Response:
        uploaded = request.file("image")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucune image sélectionnée."
            return BaseController.render(
                "image_attach/index.html", context=context, request=request
            )
        try:
            saved = save_image_upload(uploaded, "images")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "image_attach/index.html", context=context, request=request
            )
        try:
            media_id = attach_media_to_entity(
                saved,
                entity_name=_ENTITY_NAME,
                entity_id=_ENTITY_ID,
                role="gallery",
            )
        except Exception:
            # Table absente, base inaccessible… - on reste pédagogique.
            context["error"] = _TABLE_NOT_READY
            return BaseController.render(
                "image_attach/index.html", context=context, request=request
            )
        context["saved"] = saved
        context["media_id"] = media_id
        return BaseController.render(
            "image_attach/index.html", context=context, request=request
        )
```

### Comprendre ce code

- `(EntityName, EntityId)` relie l'image à une entité.
  La table `media` n'impose **aucune clé étrangère** : on illustre ici avec une entité de démo neutre (`gallery-demo`, `1`), sans dépendre d'une entité métier.
- Le `role` (`gallery`, `cover`…) classe le média : une même entité peut avoir une galerie et une couverture.
- L'upload précède toujours le rattachement : on n'enregistre en base qu'un fichier déjà vérifié et écrit.

## La vue

Le contrôleur rend `image_attach/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_attach/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Rattacher une image à une entité - Forge</title>
</head>
<body>
  <h1>Rattacher une image à une entité</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}

  {% if media_id %}
  <p data-level="success">
    Image <strong>{{ saved.original_name }}</strong> rattachée à l'entité de démo
    sous l'identifiant média <code>#{{ media_id }}</code> (rôle <code>gallery</code>).
  </p>
  {% endif %}

  <form method="post" action="/image-attach" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="image" accept="image/*" required>
    <button type="submit">Téléverser et rattacher</button>
  </form>
</body>
</html>
```

## La migration

Ce palier introduit la table `media`.
Créez le fichier de migration suivant sous `mvc/migrations/`, puis appliquez-le avec `forge migration:apply`.

```sql
-- mvc/migrations/20260605100000_create_media.sql
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
from mvc.controllers.image_attach_controller import ImageAttachController

with router.group("", public=True) as public:
    public.add("GET", "/image-attach", ImageAttachController.index, name="image_attach_index")
    public.add("POST", "/image-attach", ImageAttachController.attach, name="image_attach_store")
```

## À retenir

- Une image en base est une ligne `media` reliée à une entité par `(EntityName, EntityId, role)`.
- `attach_media_to_entity` prend le `SavedUpload` issu de `save_image_upload`.
- La table est créée par une migration **livrée avec le starter**.

## Après ce starter

L'image est en base.
La suite : afficher toutes les images d'une entité.

[Afficher la galerie](image-gallery.md)
