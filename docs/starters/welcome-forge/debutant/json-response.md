# Réponse JSON

Objectif : retourner des données structurées avec `Response.json(...)`.

**Ce que vous allez apprendre :** renvoyer une réponse **JSON**
(`application/json`) au lieu d'un texte ou d'une page HTML — la brique de
base d'une API consommée par un front, un script ou Forge Design.

Palier 6 de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Inspecter une requête](request-debug.md).

## Ce que ce starter montre

- une route `GET /json-response`
- un contrôleur `JsonResponseController`
- une réponse JSON avec `Response.json({...})`

Aucune vue HTML.
Aucune base de données.
Aucun formulaire.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par la méthode du contrôleur. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Construire la réponse JSON avec `Response.json(...)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
https://localhost:8000/json-response
```

Résultat attendu (corps `application/json`) :

```json
{
  "framework": "Forge",
  "message": "Bonjour JSON",
  "items": ["alpha", "beta", "gamma"]
}
```

## Les routes

```python
# mvc/routes.py
from mvc.controllers.json_response_controller import JsonResponseController

with router.group("", public=True) as pub:
    pub.add("GET", "/json-response", JsonResponseController.index, name="json_response_index")
```

## Le contrôleur

```python
# mvc/controllers/json_response_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class JsonResponseController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.json(
            {
                "framework": "Forge",
                "message": "Bonjour JSON",
                "items": ["alpha", "beta", "gamma"],
            }
        )
```

### Comprendre ce code

- `Response.json(...)` sérialise un `dict` (ou une liste) en JSON et pose
  l'en-tête `Content-Type: application/json`. Pas de template, pas de
  rendu HTML.
- Les clés/valeurs doivent être sérialisables JSON (str, nombres, bool,
  listes, dicts) — pas d'objet Python arbitraire.
- C'est la réponse type d'une **API** : un client (JavaScript, `curl`,
  Forge Design) la consomme directement.

## À retenir

- `Response.json(...)` renvoie des données structurées, pas du HTML.
- L'en-tête `application/json` est posé automatiquement.
- C'est la base d'une API : la même donnée peut alimenter une page, un
  script ou un autre service.

## Après ce starter

Passez au palier suivant : **Le jeton CSRF** — vous y apprendrez
pourquoi Forge protège les formulaires et comment fournir le jeton
attendu.

[Continuer avec Le jeton CSRF](csrf.md)
