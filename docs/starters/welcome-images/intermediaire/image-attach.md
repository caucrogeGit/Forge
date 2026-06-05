# Rattacher une image à une entité

Objectif : faire entrer l'image **en base**. Jusqu'ici elle vivait sur le
disque ; on crée maintenant une ligne `media` qui la relie à une entité.

**Ce que vous allez apprendre :** après l'upload (`save_image_upload`),
`attach_media_to_entity` crée une ligne dans la table `media` reliée à une
entité par `(EntityName, EntityId)` et un `role`. Une image appartient toujours
à « quelque chose ».

Premier palier du **niveau intermédiaire** de la progression images.

!!! note "Module opt-in et table `media`"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation »). La
    table `media` est créée par la **migration livrée avec le starter** :
    appliquez-la avec `forge migration:apply`. Si la table manque, la route
    reste **pédagogique** au lieu de planter.

## Ce que ce starter montre

- un formulaire d'upload (CSRF) ;
- `save_image_upload` pour vérifier + écrire + générer les variantes ;
- `attach_media_to_entity` pour créer la ligne `media` (rôle `gallery`) ;
- l'affichage de l'identifiant média attribué, ou d'un message pédagogique si la
  table n'existe pas encore.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.save_image_upload` | Vérifier, écrire, générer les variantes. | [Médias](../../../features/media.md) |
| `forge_mvc_images.attach_media_to_entity` | Créer la ligne `media` reliée à l'entité. | [Médias](../../../features/media.md) |
| `request.file(...)` | Récupérer l'image envoyée. | [Request](../../../reference/http.md) |

## Tester

Appliquez d'abord la migration (`forge migration:apply`), puis :

```bash
forge run
```

Ouvrez `https://localhost:8000/image-attach`, envoyez une image : la page
confirme la création de la ligne `media` avec son identifiant.

## Le contrôleur

```python
# mvc/controllers/image_attach_controller.py
from forge_mvc_files import UploadError
from forge_mvc_images import attach_media_to_entity, save_image_upload

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1


class ImageAttachController(BaseController):

    @staticmethod
    def attach(request: Request) -> Response:
        uploaded = request.file("image")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucune image sélectionnée."
            return BaseController.render("image_attach/index.html", context=context, request=request)
        try:
            saved = save_image_upload(uploaded, "images")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render("image_attach/index.html", context=context, request=request)
        media_id = attach_media_to_entity(
            saved, entity_name=_ENTITY_NAME, entity_id=_ENTITY_ID, role="gallery"
        )
        context["saved"] = saved
        context["media_id"] = media_id
        return BaseController.render("image_attach/index.html", context=context, request=request)
```

### Comprendre ce code

- `(EntityName, EntityId)` relie l'image à une entité. La table `media`
  n'impose **aucune clé étrangère** : on illustre ici avec une entité de démo
  neutre (`gallery-demo`, `1`), sans dépendre d'une entité métier.
- Le `role` (`gallery`, `cover`…) classe le média : une même entité peut avoir
  une galerie et une couverture.
- L'upload précède toujours le rattachement : on n'enregistre en base qu'un
  fichier déjà vérifié et écrit.

## À retenir

- Une image en base est une ligne `media` reliée à une entité par
  `(EntityName, EntityId, role)`.
- `attach_media_to_entity` prend le `SavedUpload` issu de `save_image_upload`.
- La table est créée par une migration **livrée avec le starter**.

## Après ce starter

L'image est en base. La suite : afficher toutes les images d'une entité.

[Afficher la galerie](image-gallery.md)
