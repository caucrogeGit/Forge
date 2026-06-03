# API JSON protégée

Objectif : exposer des données en **JSON** à des clients, derrière un **jeton
d'authentification**.

**Ce que vous allez apprendre :** renvoyer du JSON avec `Response.json`, et
**protéger** la route par un jeton `Authorization: Bearer …` lu via
`request.header(...)`. Sans jeton valide, l'API répond `401`. C'est le motif
d'authentification le plus courant pour une API consommée par un front
JavaScript, un script ou un autre service.

Palier 4 du **niveau avancé** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Envoyer un email](send-email.md).

## Ce que ce starter montre

- une route qui renvoie des données en JSON (`Response.json`) ;
- la lecture de l'en-tête `Authorization` avec `request.header(...)` ;
- la vérification d'un **jeton Bearer** avant de répondre ;
- une réponse `401` JSON quand le jeton est absent ou invalide.

Les données proviennent de la table `first_sql_messages`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `request.header` | Lire l'en-tête `Authorization` de la requête. | [Request](../../../reference/api.md#corehttp) |
| `Response.json` | Renvoyer des données (ou une erreur) en JSON. | [Response](../../../reference/api.md#corehttp) |
| `core.database.db.fetch_all` | Lire les messages à exposer. | [Base de données](../../../reference/api.md#coredatabase) |

## Tester

```bash
forge run
```

Sans jeton, la requête est refusée :

```bash
curl -k https://localhost:8000/json-api
# {"error": "Jeton manquant ou invalide."}  (HTTP 401)
```

Avec le jeton de démonstration, l'API renvoie les données :

```bash
curl -k -H "Authorization: Bearer forge-demo-token" https://localhost:8000/json-api
# {"messages": [{"id": 1, "content": "…"}, …]}
```

## Le contrôleur

```python
# mvc/controllers/json_api_controller.py
from core.database.db import fetch_all


API_TOKEN = "forge-demo-token"
SELECT_MESSAGES = "SELECT id, content FROM first_sql_messages ORDER BY id"


class JsonApiController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        authorization = request.header("Authorization") or ""
        if authorization != f"Bearer {API_TOKEN}":
            return Response.json({"error": "Jeton manquant ou invalide."}, status=401)
        messages = fetch_all(SELECT_MESSAGES)
        return Response.json({"messages": messages})
```

### Comprendre ce code

- `request.header("Authorization")` lit l'en-tête envoyé par le client. On le
  compare à `Bearer <jeton>` : c'est la convention des API à jeton.
- Si le jeton ne correspond pas, on renvoie **immédiatement** `Response.json(...,
  status=401)` — on ne lit même pas la base. La sécurité vient **avant** la
  donnée.
- Sinon, on lit les messages et on les renvoie en JSON. `fetch_all` rend des
  dictionnaires, directement sérialisables.
- Le jeton est ici une **constante de démonstration**. Une vraie application le
  garderait secret (hors du code versionné) et le renouvellerait.

## À retenir

- `Response.json(data, status=…)` renvoie données **et** code HTTP.
- `request.header(...)` donne accès aux en-têtes — dont `Authorization`.
- On vérifie l'autorisation **avant** de produire la donnée ; un refus = `401`.

## Après ce starter

Vous savez exposer une API protégée. Dernier palier : écrire plusieurs lignes de
façon atomique.

[Écritures transactionnelles](db-transaction.md)
