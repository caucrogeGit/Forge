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
from forge_mvc_images import delete_media, list_media_for_entity


class ImageDeleteController(BaseController):

    @staticmethod
    def delete(request: Request) -> Response:
        media_id = request.form("media_id")
        delete_media(int(media_id), delete_files=True)
        # … puis ré-affichage de la liste
```

### Comprendre ce code

- `delete_files=True` est ce qui distingue une suppression **propre** d'une
  simple suppression de ligne : sans lui, le fichier et ses variantes
  resteraient sur le disque.
- `delete_media` est idempotent : supprimer un média déjà absent ne lève pas
  d'erreur, il renvoie un compte rendu.
- On supprime par identifiant `media_id` : une opération ciblée, jamais en masse.

## À retenir

- Une suppression propre retire **la ligne et les fichiers** (original +
  variantes).
- `delete_media(delete_files=True)` couvre les trois en une fois.
- Laisser des fichiers orphelins est une dette silencieuse — Forge l'évite.

## Après ce starter

La suppression est propre. Dernier palier : la garde de sécurité à l'upload.

[Garde de sécurité à l'upload](image-safety.md)
