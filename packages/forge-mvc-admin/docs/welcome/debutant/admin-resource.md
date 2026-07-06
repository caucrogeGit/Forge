# Débutant 2 : Déclarer une ressource

Objectif : rendre l'entité `Article` administrable.

## Déclarer un `AdminResource`

Ouvrez `mvc/admin/resources.py` et déclarez la ressource :

```python
from forge_mvc_admin import AdminResource, registry

registry.register(AdminResource(
    entity="Article",
    slug="articles",
    label="Article",
    plural_label="Articles",
    list_fields=("title", "published_at"),
    form_fields=("title", "body"),
    table="articles",
))
```

Chaque attribut est explicite :

- `entity` : le nom de l'entité, tel que dans son contrat ;
- `slug` : le segment d'URL sous `/admin` ;
- `label` et `plural_label` : les libellés affichés ;
- `list_fields` : les colonnes montrées en liste ;
- `form_fields` : les colonnes éditables en formulaire ;
- `table` : la table physique.

Ces noms de colonnes entrent directement dans les requêtes : ce sont les noms réels des colonnes de la table.

## Vérifier

Rechargez `/admin`.
La ressource « Articles »
apparaît désormais dans le tableau de bord.

Vous pouvez aussi vérifier la cohérence avec le contrat d'entité :

```bash
forge admin:doctor
```

## À retenir

- Une ressource est une déclaration Python, pas un fichier de configuration.
- Le registre est explicite : vous enregistrez vos ressources à la main.

## Étape suivante

[Suivant : la liste](admin-list.md)
