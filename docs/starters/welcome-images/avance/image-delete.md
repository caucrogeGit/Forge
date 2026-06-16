# Supprimer proprement

Objectif : supprimer une image **sans laisser de trace** — ni ligne en base, ni
fichier orphelin, ni variante oubliée.

**Ce que vous allez apprendre :** supprimer une image, c'est supprimer trois
choses : la ligne `media`, le fichier original et ses variantes.
`delete_media(..., delete_files=True)` fait les trois en une opération.

Deuxième palier du **niveau avancé** de la progression images.

!!! note "Module opt-in et table `media`"
    Ce starter suppose `forge-mvc-images` installé (palier « Installation ») et
    la table `media` appliquée (`forge migration:apply`). Si elle manque, la
    page reste **pédagogique**.

## Ce que ce starter montre

- la liste des images avec un bouton Supprimer par image ;
- la suppression atomique (ligne + fichier + variantes) avec `delete_media` ;
- un repli **pédagogique** si la table `media` n'existe pas.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_images.delete_media` | Supprimer ligne + fichier + variantes. | [Médias](../../../features/media.md) |
| `forge_mvc_images.list_media_for_entity` | Lister les images à supprimer. | [Médias](../../../features/media.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/image-delete` et supprimez une image : sa ligne et
ses fichiers disparaissent ensemble.

## Le contrôleur

```python
# mvc/controllers/image_delete_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import delete_media, list_media_for_entity

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageDeleteController(BaseController):
    """Starter pédagogique : supprimer une image (ligne + fichier + variantes)."""

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
            "image_delete/index.html", context=context, request=request
        )

    @staticmethod
    def index(request: Request) -> Response:
        return ImageDeleteController._render(request)

    @staticmethod
    def delete(request: Request) -> Response:
        media_id = request.form("media_id")
        if not media_id:
            return ImageDeleteController._render(request, error="Aucune image sélectionnée.")
        try:
            delete_media(int(media_id), delete_files=True)
        except Exception:
            return ImageDeleteController._render(request, error=_TABLE_NOT_READY)
        return ImageDeleteController._render(request, updated=f"Image #{media_id} supprimée.")
```

### Comprendre ce code

- `delete_files=True` est ce qui distingue une suppression **propre** d'une
  simple suppression de ligne : sans lui, le fichier et ses variantes
  resteraient sur le disque.
- `delete_media` est idempotent : supprimer un média déjà absent ne lève pas
  d'erreur, il renvoie un compte rendu.
- On supprime par identifiant `media_id` : une opération ciblée, jamais en masse.

## La vue

Le contrôleur rend `image_delete/index.html` : créez ce fichier.

```html
<!-- mvc/views/image_delete/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Supprimer proprement — Forge</title>
</head>
<body>
  <h1>Supprimer proprement</h1>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% endif %}
  {% if updated %}
  <p data-level="success">{{ updated }}</p>
  {% endif %}

  {% if items %}
  {% for item in items %}
  <form method="post" action="/image-delete">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="hidden" name="media_id" value="{{ item.id }}">
    <code>#{{ item.id }} — {{ item.path }}</code>
    <button type="submit">Supprimer</button>
  </form>
  {% endfor %}
  {% elif not error %}
  <p>Aucune image à supprimer.</p>
  {% endif %}
</body>
</html>
```

## La migration

Ce palier utilise la table `media`. Si vous ne l'avez pas encore créée, créez le
fichier de migration suivant sous `mvc/migrations/`, puis appliquez-le avec
`forge migration:apply`.

```sql
-- mvc/migrations/20260605111000_create_media.sql
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
from mvc.controllers.image_delete_controller import ImageDeleteController

with router.group("", public=True) as public:
    public.add("GET", "/image-delete", ImageDeleteController.index, name="image_delete_index")
    public.add("POST", "/image-delete", ImageDeleteController.delete, name="image_delete_remove")
```

## À retenir

- Une suppression propre retire **la ligne et les fichiers** (original +
  variantes).
- `delete_media(delete_files=True)` couvre les trois en une fois.
- Laisser des fichiers orphelins est une dette silencieuse — Forge l'évite.

## Après ce starter

La suppression est propre. Dernier palier : la garde de sécurité à l'upload.

[Garde de sécurité à l'upload](image-safety.md)
