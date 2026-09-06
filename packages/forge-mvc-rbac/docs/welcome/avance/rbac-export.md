# Avancé 6 : Exporter le contrat

Objectif : répondre à « qui a le droit de faire quoi » sans lire un JSON à l'œil.

## La question d'une revue

`rbac:validate` dit si le contrat est valide.
`rbac:audit` compare le contrat et la base.
Ni l'un ni l'autre ne rend le contrat **lisible**, ce qui se fait mal dès la dizaine de rôles.

```bash
forge rbac:export
forge rbac:export --format csv
```

## Ce que l'export rend

```text
| Rôle      | Entité    | Actions        |
|---|---|---|
| `admin`   | `Article` | list, publish  |
| `editeur` | `Article` | list           |
| `lecteur` | `Article` | list           |
```

Les permissions sont **effectives**, héritage compris.
Rendre les seules permissions directes ferait croire un administrateur privé de droits qu'il possède, et c'est exactement ce qu'une revue ne doit pas conclure.

| Sortie | Usage |
|---|---|
| Markdown | à versionner à côté du code ; une différence montre alors qu'un rôle a gagné une permission |
| CSV | pour un tableur, où une revue se mène ligne à ligne |

!!! info "Une permission qu'aucune entité ne réclame apparaît quand même"
    Elle est rendue sous l'entité « (aucune) ».

    La taire ferait disparaître d'une revue de sécurité un droit pourtant accordé, et c'est justement ce genre de reste qu'une revue cherche.

!!! warning "L'export rend le contrat, pas la base"
    Il ne lit aucune table : il montre ce qui est **déclaré**, non ce qui est provisionné.

    `forge rbac:audit` compare déjà les deux, et confondre les deux sorties ferait prendre une intention pour un état.

!!! danger "Un contrat invalide n'est pas exporté"
    L'export refuse plutôt que de rendre un tableau qui ne s'applique pas.

    Corrigez d'abord ; `forge rbac:validate` détaille.

## À retenir

- Deux sorties : Markdown pour lire et versionner, CSV pour réviser.
- Les permissions rendues sont effectives, héritage compris.
- L'export dit le contrat ; `rbac:audit` dit l'écart avec la base.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
