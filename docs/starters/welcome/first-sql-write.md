# Écrire en base

Objectif : insérer une ligne en base depuis un formulaire avec
`db.insert(...)`.

**Ce que vous allez apprendre :** **écrire** une donnée en base (et plus
seulement la lire) en réunissant tout ce que vous avez vu : un
formulaire protégé par CSRF, la validation serveur, et une requête SQL
`INSERT` visible. C'est le **dernier palier avant le CRUD complet**.

Palier 11 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Première base SQL](first-sql.md).

## Ce que ce starter montre

- deux routes `GET` / `POST` sur `/first-sql-write`
- un formulaire avec jeton CSRF
- la validation serveur (refus d'un message vide → `422`)
- une requête `INSERT` avec `db.insert(...)`
- la réutilisation de la table `first_sql_messages` du palier précédent

Aucune entité JSON.
Aucun CRUD complet (lecture/mise à jour/suppression) — c'est l'objet du
**starter suivant** (First CRUD).

## Prérequis

Ce palier suppose acquis : le formulaire + CSRF (`csrf`, `form-post`), la
validation serveur (`server-validation`) et le SQL visible (`first-sql`).
La table `first_sql_messages` est créée par la migration du palier
« Première base SQL » : appliquez-la d'abord.

```bash
forge migration:apply
forge run
```

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Lire la valeur soumise avec `request.form(...)`. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Réponse `422` ou confirmation texte. | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | `render(...)` + `csrf_token(...)`. | [BaseController](../../reference/api.md#coremvccontroller) |
| `core.database.db.insert` | Exécuter l'`INSERT` paramétré. | [Migrations SQL](../../features/migrations.md) |

## Tester

Ouvrez `https://localhost:8000/first-sql-write`, saisissez un message,
envoyez. La réponse confirme l'enregistrement. Le message inséré est
ensuite lisible via le palier « Première base SQL »
(`/first-sql` lit la première ligne de la même table).

## Les routes

```python
# mvc/routes.py
from mvc.controllers.first_sql_write_controller import FirstSqlWriteController

with router.group("", public=True) as pub:
    pub.add("GET",  "/first-sql-write", FirstSqlWriteController.index,  name="first_sql_write_index")
    pub.add("POST", "/first-sql-write", FirstSqlWriteController.submit, name="first_sql_write_submit")
```

## Le contrôleur

```python
# mvc/controllers/first_sql_write_controller.py
from core.database.db import insert
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


INSERT_MESSAGE = "INSERT INTO first_sql_messages (content) VALUES (?)"


class FirstSqlWriteController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "first_sql_write/index.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def submit(request: Request) -> Response:
        content = request.form("content", default="").strip()

        if not content:
            return Response.text("Le message est obligatoire", status=422)

        insert(INSERT_MESSAGE, (content,))
        return Response.text(f"Message enregistré : {content}")
```

### Comprendre ce code

- `INSERT INTO ... VALUES (?)` est une requête **paramétrée** : la valeur
  passe par `params`, jamais concaténée dans la chaîne SQL (protection
  contre l'injection). **Forge garde le SQL visible.**
- `db.insert(...)` exécute l'`INSERT` et valide la transaction.
- La validation (`if not content`) précède l'écriture : on ne stocke
  jamais une donnée invalide.

## La vue

```html
<!-- mvc/views/first_sql_write/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Écrire en base — Forge</title>
</head>
<body>
  <h1>Écrire en base</h1>

  <form method="post" action="/first-sql-write">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <label for="content">Message</label>
    <input id="content" name="content" type="text">

    <button type="submit">Enregistrer</button>
  </form>
</body>
</html>
```

## À retenir

- L'écriture en base se fait avec une requête `INSERT` **paramétrée** et
  `db.insert(...)` — le SQL reste visible, sans ORM.
- On valide **avant** d'écrire.
- Avec la lecture (palier précédent) et l'écriture (ici), vous avez les
  deux moitiés du CRUD ; le palier suivant les organise en un CRUD
  complet.

## Après ce starter

C'est le **dernier palier** du starter de découverte *Bonjour Forge*.
Vous savez maintenant **lire et écrire** en base. Faites le point sur
tout ce que vous avez validé, puis enchaînez sur le premier starter
autonome : le **CRUD complet**, qui structure ces opérations (créer,
lister, modifier, supprimer) sur une entité neutre.

[Bilan du starter Bonjour Forge](bilan.md)

[Prochain starter : First CRUD](../crud/first-crud.md)
