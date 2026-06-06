# Bonjour Forge RBAC

Objectif : premier contact avec le module **opt-in** `forge-mvc-rbac` et son
**contrat déclaratif**.

**Ce que vous allez apprendre :** Forge sépare les **rôles** (qui on est) des
**permissions** (ce qu'on a le droit de faire), déclarés dans un contrat
`mvc/security/rbac.json` (ADR-014). `load_rbac_contract` le charge ;
`get_contract_permissions` liste les permissions d'un rôle.

Premier palier du **niveau débutant** de la progression RBAC
([vue d'ensemble des starters](../../index.md)).

!!! note "Module opt-in"
    Ce starter livre un contrat de démonstration (`mvc/security/rbac.json`) et
    l'inspecte. Installé via `pip install --pre forge-mvc-rbac` (palier « Installation »).

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /rbac-welcome`) ;
- le contrat chargé (rôles, entités) + les permissions du rôle `admin`
  (`GET /rbac-welcome/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.load_rbac_contract` | Charger et valider `mvc/security/rbac.json`. | [RBAC](../../../reference/api.md) |
| `forge_mvc_rbac.get_contract_permissions` | Permissions accordées à un ensemble de rôles. | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-welcome` puis `/rbac-welcome/inspect`.

## Le contrôleur

```python
# mvc/controllers/rbac_welcome_controller.py
from forge_mvc_rbac import get_contract_permissions, load_rbac_contract


def _inspect() -> dict:
    result = load_rbac_contract(".")
    return {
        "contract_exists": result.exists,
        "valid": result.valid,
        "roles_count": result.roles_count,
        "entities_count": result.entities_count,
        "admin_permissions": sorted(get_contract_permissions(result, ["admin"])),
    }
```

### Comprendre ce code

- Le contrat est un **fichier déclaratif** : on décrit qui peut quoi, sans coder de
  conditions dans chaque contrôleur.
- `load_rbac_contract` est **lecture seule** : il valide le fichier et renvoie un
  résultat (existence, validité, comptes).
- `get_contract_permissions(result, ["admin"])` agrège les permissions de tous les
  rôles donnés.

## À retenir

- RBAC sépare **rôles** et **permissions**, déclarés dans un contrat.
- Le contrat vit dans `mvc/security/rbac.json` (ADR-014).
- Déclaratif = lisible et auditable, pas de logique dispersée.

## Après ce starter

Premier contact établi. La suite : la brique « permission ».

[Code de permission](rbac-permission.md)
