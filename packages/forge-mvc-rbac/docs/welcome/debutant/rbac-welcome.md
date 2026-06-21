# Bonjour Forge RBAC

Objectif : premier contact avec le module **opt-in** `forge-mvc-rbac` et son
**contrat déclaratif**.

**Ce que vous allez apprendre :** Forge sépare les **rôles** (qui on est) des
**permissions** (ce qu'on a le droit de faire), déclarés dans un contrat
`mvc/security/rbac.json` (ADR-014). `load_rbac_contract` le charge ;
`get_contract_permissions` liste les permissions d'un rôle.

Premier palier du **niveau débutant** de la progression RBAC
(vue d'ensemble des starters).

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
| `forge_mvc_rbac.load_rbac_contract` | Charger et valider `mvc/security/rbac.json`. | RBAC |
| `forge_mvc_rbac.get_contract_permissions` | Permissions accordées à un ensemble de rôles. | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-welcome` puis `/rbac-welcome/inspect`.

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_welcome_controller.py` :

```python
# mvc/controllers/rbac_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

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


class RbacWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge RBAC."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge RBAC")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_inspect())
```

### Comprendre ce code

- Le contrat est un **fichier déclaratif** : on décrit qui peut quoi, sans coder de
  conditions dans chaque contrôleur.
- `load_rbac_contract` est **lecture seule** : il valide le fichier et renvoie un
  résultat (existence, validité, comptes).
- `get_contract_permissions(result, ["admin"])` agrège les permissions de tous les
  rôles donnés.

## Le contrat

Créez le contrat de démonstration `mvc/security/rbac.json` :

```json
{
  "schema_version": "1.0",
  "entities": {
    "Article": {
      "permissions": {
        "list": "article.list",
        "show": "article.show",
        "create": "article.create",
        "update": "article.update",
        "delete": "article.delete"
      }
    }
  },
  "roles": {
    "admin": ["article.list", "article.show", "article.create", "article.update", "article.delete"],
    "editor": ["article.list", "article.show", "article.create", "article.update"],
    "reader": ["article.list", "article.show"]
  }
}
```

Ce contrat sert tout le parcours : il déclare une entité `Article`, ses permissions,
et trois rôles (`admin`, `editor`, `reader`) avec les permissions accordées à chacun.

!!! tip "Valider `rbac.json` dans VS Code (optionnel)"
    RBAC est un opt-in : son schéma n'est pas livré par le squelette nu.
    `forge-mvc` le fournit, voici comment activer la validation et l'autocomplétion de `mvc/security/rbac.json`.

    Copiez le schéma dans `schemas/` du projet :

    ```bash
    python -c "import forge_cli, pathlib, shutil; shutil.copy(pathlib.Path(forge_cli.__file__).parent / 'schemas' / 'rbac.schema.json', 'schemas/rbac.schema.json')"
    ```

    Puis ajoutez l'association dans `.vscode/settings.json`, dans le tableau `json.schemas` existant :

    ```json
    { "fileMatch": ["/mvc/security/rbac.json"], "url": "./schemas/rbac.schema.json" }
    ```

    `forge opt-in:enable rbac` rappelle aussi ces étapes.

## La route

Ajoutez l'import et les deux routes dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_welcome_controller import RbacWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-welcome", RbacWelcomeController.index, name="rbac_welcome_index")
    public.add("GET", "/rbac-welcome/inspect", RbacWelcomeController.inspect, name="rbac_welcome_inspect")
```

## À retenir

- RBAC sépare **rôles** et **permissions**, déclarés dans un contrat.
- Le contrat vit dans `mvc/security/rbac.json` (ADR-014).
- Déclaratif = lisible et auditable, pas de logique dispersée.

## Après ce starter

Premier contact établi. La suite : la brique « permission ».

[Code de permission](rbac-permission.md)
