# Première base SQL

Objectif : lire une donnée depuis MariaDB avec du SQL visible.

Palier 8 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Validation serveur](../server-validation/index.md). C'est le
**dernier palier avant le CRUD Contacts**.

## Ce que ce starter montre

- une route `GET /first-sql`
- une table SQL minimale (`first_sql_messages`)
- une migration SQL visible
- une requête `SELECT` brute
- une réponse texte avec `Response.text(...)`

Aucun CRUD.
Aucune entité JSON.
Aucun formulaire.
Aucune validation avancée.
Aucune jointure.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par la méthode du contrôleur. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Construire la réponse texte avec `Response.text(...)`. | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../reference/api.md#coremvccontroller) |

## Tester

Depuis le projet Forge déjà créé avec ce starter, appliquer
d'abord la migration livrée puis démarrer le serveur :

```bash
forge migration:apply
forge run
```

Ouvrez :

```
http://localhost:8000/first-sql
```

Résultat attendu :

```
Message depuis la base : Bonjour SQL
```

## Code essentiel

```python
# mvc/controllers/first_sql_controller.py
from core.database.db import fetch_one
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_FIRST_MESSAGE = "SELECT content FROM first_sql_messages ORDER BY id LIMIT 1"


class FirstSqlController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        row = fetch_one(SELECT_FIRST_MESSAGE)
        message = row["content"] if row else "(aucun message)"
        return Response.text(f"Message depuis la base : {message}")
```

### Comprendre ce code

- La requête SQL est déclarée comme une chaîne Python lisible —
  **Forge garde le SQL visible**, sans génération cachée par un ORM.
- `fetch_one(...)` exécute la requête et retourne la première ligne
  sous forme de `dict`, ou `None` si la table est vide.
- Le contrôleur extrait la colonne `content` puis la réinjecte dans
  une réponse texte.
- Le cycle reste minimal : route → contrôleur → SQL → réponse. Dans une
  vraie application, on isolerait la requête dans un module modèle.

```sql
-- mvc/migrations/20260527120000_create_first_sql_messages.sql
CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT 'Bonjour SQL'
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages WHERE content = 'Bonjour SQL'
);
```

### Comprendre ce code

- `CREATE TABLE IF NOT EXISTS ...` rend la migration idempotente :
  rejouée, elle ne lève pas d'erreur si la table existe déjà.
- `INSERT ... WHERE NOT EXISTS (...)` insère la donnée de démo une
  seule fois — utile pour réappliquer la migration sans dupliquer.
- Les migrations Forge sont des fichiers SQL versionnés dans
  `mvc/migrations/` ; `forge migration:apply` les exécute dans l'ordre.

## À retenir

- **Forge garde le SQL visible** : la requête `SELECT` est une chaîne
  Python lisible, pas une méthode magique d'ORM.
- La migration crée la table avec `CREATE TABLE IF NOT EXISTS` et
  insère la donnée de démo de manière idempotente.
- Le contrôleur lit la donnée avec `fetch_one(...)` de
  `core.database.db` — c'est l'API officielle Forge (avec aussi
  `fetch_all`, `execute`, `insert`).
- Le CRUD complet vient seulement au palier suivant, qui utilise les
  mêmes briques en plus organisé.

## Après ce starter

Vous avez maintenant parcouru les bases nécessaires avant le CRUD :

- routes ;
- contrôleurs ;
- réponses texte ;
- vues HTML ;
- paramètres d'URL ;
- routes dynamiques ;
- inspection de requête ;
- formulaires POST ;
- validation serveur ;
- SQL visible.

Vous pouvez passer au palier final : **Contacts CRUD**.

[Continuer avec Contacts CRUD](../01-contact-simple/index.md)
