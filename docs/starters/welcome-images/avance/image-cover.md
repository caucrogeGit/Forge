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
from forge_mvc_images import attach_media_to_entity, get_cover_media, save_image_upload

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1


class ImageCoverController(BaseController):

    @staticmethod
    def set_cover(request: Request) -> Response:
        uploaded = request.file("image")
        saved = save_image_upload(uploaded, "images")
        attach_media_to_entity(
            saved, entity_name=_ENTITY_NAME, entity_id=_ENTITY_ID, role="cover"
        )
        # … puis ré-affichage via get_cover_media(role="cover", fallback_to_gallery=True)
```

### Comprendre ce code

- Le **rôle** est la clé : une même entité peut avoir une galerie (`gallery`) et
  une couverture (`cover`), distinguées par cette seule colonne.
- `fallback_to_gallery=True` rend l'affichage robuste : pas de couverture
  explicite ? On montre la première image de la galerie.
- Désigner une couverture, c'est simplement rattacher un média avec le bon rôle.

## À retenir

- La couverture est un média de **rôle** `cover`, lu par `get_cover_media`.
- Le repli sur la galerie évite une page vide quand aucune couverture n'est posée.
- Le rôle classe les médias sans table supplémentaire.

## Après ce starter

La couverture est en place. La suite : supprimer une image proprement.

[Supprimer proprement](image-delete.md)
