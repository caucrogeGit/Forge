# Contrat d'une ressource admin

Une **ressource admin** décrit comment une entité d'un projet Forge est
administrée : quelle entité, sous quel slug d'URL, avec quels libellés, et quels
champs sont montrés en liste et éditables en formulaire.

!!! warning "Statut : châssis en cours"
    Cette page documente le contrat (`AdminResource`) et le registre
    (`AdminRegistry`) livrés par le ticket `ADMIN-RESOURCE-CONTRACT-001`.
    Les vues qui consomment ce contrat viendront par les tickets suivants.

## Principe

Le contrat est une **déclaration Python**, pas un nouveau fichier de
configuration.
L'entité reste décrite par son contrat JSON ; la ressource admin est une couche
de présentation au-dessus, écrite en code explicite et modifiable.

La ressource valide sa propre forme à la construction.
Elle ne lit ni le contrat d'entité ni la base : le rapprochement avec l'entité
réelle (existence de l'entité, des champs) relèvera d'une vérification ultérieure
(`forge admin:doctor`).

## `AdminResource`

`AdminResource` est une dataclass immuable (`frozen`).

| Attribut | Type | Rôle |
|---|---|---|
| `entity` | `str` | nom canonique de l'entité (PascalCase, ex. `Article`) |
| `slug` | `str` | segment d'URL sous `/admin/` (minuscules, tirets, ex. `articles`) |
| `label` | `str` | libellé singulier |
| `plural_label` | `str` | libellé pluriel |
| `list_fields` | `tuple[str, ...]` | champs affichés en liste (au moins un) |
| `form_fields` | `tuple[str, ...]` | champs éditables en formulaire (au moins un) |

Règles de validation, sinon `AdminResourceError` :

- `entity` en PascalCase ;
- `slug` en minuscules, chiffres et tirets, commençant par une lettre ;
- `label` et `plural_label` non vides ;
- `list_fields` et `form_fields` non vides, chaque nom en snake_case, sans doublon.

```python
from forge_mvc_admin import AdminResource

article = AdminResource(
    entity="Article",
    slug="articles",
    label="Article",
    plural_label="Articles",
    list_fields=("title", "published_at"),
    form_fields=("title", "body"),
)
```

## `AdminRegistry`

Le registre rassemble les ressources d'un projet.
Il est **explicite** : l'application enregistre ses ressources à la main, il n'y
a aucune découverte automatique.
Forge Core n'enregistre rien ; le registre par défaut est vide tant que
l'application ne l'a pas peuplé.

| Méthode | Rôle |
|---|---|
| `register(resource)` | enregistre une ressource ; lève si le slug est déjà pris |
| `get(slug)` | retourne la ressource d'un slug ; lève si inconnue |
| `all()` | retourne les ressources dans leur ordre d'enregistrement |
| `slug in registry` | teste la présence d'un slug |
| `len(registry)` | nombre de ressources |

L'ordre d'enregistrement est préservé : il pilotera l'ordre de la navigation.

```python
from forge_mvc_admin import registry, AdminResource

registry.register(article)

# Ailleurs, l'application peut aussi créer son propre registre :
from forge_mvc_admin import AdminRegistry
mon_registre = AdminRegistry()
```

## Limites assumées

- Le contrat ne vérifie pas que l'entité ou les champs existent réellement.
- Aucun rendu, aucune route, aucune action ne sont fournis par ce ticket.
- Les types de champs et les widgets ne sont pas encore pris en compte.
