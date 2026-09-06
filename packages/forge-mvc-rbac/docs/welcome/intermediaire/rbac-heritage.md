# Intermédiaire 4 : L'héritage entre rôles

Objectif : ne pas recopier les permissions du lecteur dans l'éditeur, ni celles de l'éditeur dans l'administrateur.

## Le problème que cela retire

Sans héritage, chaque rôle liste toutes ses permissions.
Ajouter une action au lecteur oblige à l'ajouter aussi à l'éditeur et à l'administrateur, et un oubli passe inaperçu jusqu'à ce que quelqu'un se plaigne.

```json
{
  "schema_version": "1.0",
  "roles": {
    "lecteur":  ["article.lire"],
    "editeur":  ["article.publier"],
    "admin":    ["article.supprimer"]
  },
  "role_inherits": {
    "admin":   ["editeur"],
    "editeur": ["lecteur"]
  }
}
```

L'administrateur possède ses trois permissions : la sienne, celle de l'éditeur, et celle du lecteur.

## L'héritage est transitif

`admin` hérite d'`editeur`, qui hérite de `lecteur` : `admin` obtient tout, sans avoir à citer `lecteur`.

| Rôle | Permissions effectives |
|---|---|
| `lecteur` | `article.lire` |
| `editeur` | `article.publier`, `article.lire` |
| `admin` | `article.supprimer`, `article.publier`, `article.lire` |

!!! danger "Un cycle est refusé, et le refus nomme le cycle"
    `admin` héritant d'`editeur` héritant d'`admin` n'a pas d'ordre de lecture.

    S'arrêter arbitrairement donnerait des permissions différentes selon l'ordre du fichier, ce qu'un contrôle d'accès ne peut pas se permettre. `forge rbac:audit` refuse et dit « cycle d'héritage : admin puis editeur puis admin ».

!!! warning "Un rôle hérité inconnu est signalé"
    Une faute de frappe n'accorde rien du tout, et personne ne s'en aperçoit avant qu'un utilisateur se plaigne.

    L'audit vérifie donc que chaque rôle cité dans `role_inherits` figure bien dans `roles`.

!!! info "L'héritage accorde, il ne retire jamais"
    Il n'existe pas de « sauf » : on ne peut pas hériter de tout sauf d'une permission.

    Un rôle qui doit avoir moins qu'un autre ne l'hérite pas, il liste ce qu'il a.

## Le voir

```bash
forge rbac:export
```

L'export rend les permissions **effectives**, héritage compris : c'est la question que pose une revue de sécurité.

## À retenir

- `role_inherits` déclare `héritier : [parents]`, et l'héritage est transitif.
- Un cycle et un rôle inconnu sont refusés par l'audit, en nommant la cause.
- L'héritage n'accorde que ; pour avoir moins, on n'hérite pas.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
