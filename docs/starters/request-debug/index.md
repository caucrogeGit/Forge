# Inspecter une requête

Objectif : afficher la structure d'une requête avec `request.data` et
`Response.debug(...)`.

Palier 5 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Route dynamique](../dynamic-route/index.md).

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
| `Request` | Source de `request.data`, vue globale et stable de la requête. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Rendu de debug avec `Response.debug(...)` (refusé en `prod`). | [Response](../../reference/http.md#4-response-reference) |

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
http://localhost:8000/request-debug?name=Roger
```

Vous devez voir une page de debug HTML contenant les informations de la
requête : méthode, chemin, paramètres, headers (les valeurs sensibles
sont masquées automatiquement).

## Code essentiel

```python
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

Passez au palier suivant : **Premier formulaire POST**.

Vous y apprendrez à envoyer des données depuis un formulaire HTML
et à lire la valeur reçue côté serveur avec :

```python
request.form("name", default="Forge")
```

[Continuer avec Premier formulaire POST](../form-post/index.md)
