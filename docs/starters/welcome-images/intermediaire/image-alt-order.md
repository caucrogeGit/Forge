# Texte alternatif et ordre

Objectif : rendre la galerie **accessible** et **ordonnée** en éditant deux
champs d'une image : son texte alternatif et sa position.

**Ce que vous allez apprendre :** `update_media_alt_text` renseigne le texte lu
par les lecteurs d'écran (`alt_text`), `update_media_position` fixe l'ordre
d'affichage (`position`). Deux écritures ciblées sur une ligne `media`.

Troisième palier du **niveau intermédiaire** de la progression images.

!!! note "Module opt-in et table `media`"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation ») et
    la table `media` appliquée (`forge migration:apply`). Si elle manque, la
    page reste **pédagogique**.

## Ce que ce starter montre

- la liste des images d'une entité avec un formulaire d'édition par image ;
- `update_media_alt_text` pour l'accessibilité ;
- `update_media_position` pour l'ordre d'affichage.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.list_media_for_entity` | Lister les images à éditer. | [Médias](../../../features/media.md) |
| `forge_mvc_images.update_media_alt_text` | Renseigner le texte alternatif. | [Médias](../../../features/media.md) |
| `forge_mvc_images.update_media_position` | Fixer l'ordre d'affichage. | [Médias](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-alt-order`, renseignez un texte alternatif
et une position, enregistrez : la galerie reflète l'ordre et l'accessibilité.

## Le contrôleur

```python
# mvc/controllers/image_alt_order_controller.py
from forge_mvc_images import (
    list_media_for_entity,
    update_media_alt_text,
    update_media_position,
)

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1


class ImageAltOrderController(BaseController):

    @staticmethod
    def update(request: Request) -> Response:
        media_id = request.form("media_id")
        alt_text = request.form("alt_text")
        position = request.form("position")
        update_media_alt_text(int(media_id), alt_text or None)
        update_media_position(int(media_id), int(position or 0))
        return ImageAltOrderController._render(request, updated=f"Image #{media_id} mise à jour.")
```

### Comprendre ce code

- `alt_text` est un enjeu d'**accessibilité** : un lecteur d'écran l'annonce à
  la place de l'image. Le module le limite à 255 caractères.
- `position` pilote l'ordre : `get_media_gallery` trie dessus, l'effet est donc
  immédiat à l'affichage.
- Les deux écritures ciblent une ligne précise par son identifiant `media_id`.

## À retenir

- Une galerie sérieuse est **accessible** (`alt_text`) et **ordonnée**
  (`position`).
- `update_media_alt_text` et `update_media_position` modifient une ligne `media`
  ciblée.
- L'ordre fixé ici est respecté par `get_media_gallery`.

## Après ce starter

Vous avez fait le tour du niveau intermédiaire : rattacher, afficher, ordonner.

[Bilan du niveau intermédiaire](bilan.md)
