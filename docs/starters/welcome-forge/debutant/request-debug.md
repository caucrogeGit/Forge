# Inspecter une requête

Objectif : afficher la structure d'une requête avec `request.data` et
`Response.debug(...)`.

**Ce que vous allez apprendre :** inspecter tout ce que reçoit votre
contrôleur (méthode, chemin, paramètres, headers) via `request.data`, et
l'afficher en développement avec `Response.debug(...)` — un outil de
débogage qui refuse de s'exécuter en production.

Palier 5 de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Route dynamique](dynamic-route.md).

## Ce que ce starter montre

- une route `/request-debug`
- un contrôleur `RequestDebugController`
- l'accès global `request.data`
- un rendu de debug avec `Response.debug(...)`

Aucune vue HTML.
Aucune base de données.
Aucun formulaire.
Aucun CRUD.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Source de `request.data`, vue globale et stable de la requête. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Rendu de debug avec `Response.debug(...)` (refusé en `prod`). | [Response](../../../reference/http.md#4-response-reference) |

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
https://localhost:8000/request-debug?name=Roger
```

Vous devez voir une page de debug HTML contenant les informations de la
requête : méthode, chemin, paramètres, headers (les valeurs sensibles
sont masquées automatiquement).

## Les routes

```python
# mvc/routes.py
from mvc.controllers.request_debug_controller import RequestDebugController

with router.group("", public=True) as pub:
    pub.add("GET", "/request-debug", RequestDebugController.index, name="request_debug_index")
```

## Le contrôleur

```python
# mvc/controllers/request_debug_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class RequestDebugController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.debug(request.data)
```

### Comprendre ce code

- `request.data` est une vue globale et stable de la requête : méthode,
  chemin, paramètres, headers, body, fichiers. Les valeurs sensibles
  (`Authorization`, `Cookie`, `password`, `csrf`…) sont automatiquement
  remplacées par `[masked]`.
- `Response.debug(...)` rend cette structure sous forme de page HTML
  lisible. C'est un outil de **développement**, pas une réponse destinée
  au public.
- En `APP_ENV=prod`, `Response.debug(...)` retourne `404` sans aucun
  détail — le starter reste sûr à laisser branché en dev.
- À observer dans la sortie : le chemin, les paramètres reçus et les
  headers. C'est ce que voit réellement votre contrôleur.

## À retenir

- `request.data` donne une vue globale et stable de la requête, avec
  les clés sensibles (`Authorization`, `Cookie`, `password`, `csrf`…)
  remplacées par `[masked]`.
- `Response.debug(...)` sert à explorer un objet en développement —
  c'est un outil de compréhension, pas un affichage public de
  production.
- En `APP_ENV=prod`, `Response.debug(...)` refuse et retourne `404`
  sans aucun détail. Le starter reste donc sûr à laisser branché en
  développement, mais n'expose rien en production.

## Après ce starter

Passez au palier suivant : **Réponse JSON**.

Vous y apprendrez à retourner des données structurées au format JSON :

```python
return Response.json({"message": "Bonjour JSON"})
```

[Continuer avec Réponse JSON](json-response.md)
