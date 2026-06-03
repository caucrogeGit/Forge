# First CRUD

Objectif : réaliser un **CRUD complet** (créer, lire, modifier, supprimer)
sur une table unique, avec du **SQL visible** et aucun ORM.

**Ce que vous allez apprendre :** assembler les quatre opérations d'un CRUD
(`fetch_all` / `insert` / `fetch_one` + `execute`) dans un seul contrôleur,
lire un paramètre de chemin `{id}` avec `request.route_param(...)`, et
ré-afficher une liste à jour après chaque écriture — le tout sur une entité
**neutre** (`message`), sans notion métier.

Premier **starter autonome** après la progression de découverte
[Bonjour Forge](../welcome-forge/welcome.md) : il prolonge directement les
paliers « Première base SQL » et « Écrire en base » en passant d'une seule
écriture à un cycle CRUD entier.

## Prérequis

Ce starter réutilise la table `first_sql_messages` créée par la migration
du palier « Première base SQL ». Appliquez d'abord cette migration :

```
mvc/migrations/20260527120000_create_first_sql_messages.sql
```

```sql
CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Ce que ce starter montre

- une route `GET /messages` — la liste **et** le formulaire de création
- une route `POST /messages` — l'insertion d'un message
- une route `GET /messages/{id}/edit` — le formulaire de modification
- une route `POST /messages/{id}` — la mise à jour
- une route `POST /messages/{id}/delete` — la suppression
- les quatre opérations SQL en clair : `SELECT`, `INSERT`, `UPDATE`, `DELETE`

Aucune notion métier.
Aucun ORM.
Aucune authentification.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `fetch_all` | Lire toutes les lignes pour la liste. | [Migrations SQL](../../features/migrations.md) |
| `fetch_one` | Lire une ligne pour la modification. | [Migrations SQL](../../features/migrations.md) |
| `insert` | Insérer une ligne. | [Migrations SQL](../../features/migrations.md) |
| `execute` | Mettre à jour ou supprimer une ligne. | [Migrations SQL](../../features/migrations.md) |
| `Request` | Lire un champ (`request.form`) et un segment d'URL (`request.route_param`). | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Renvoyer la page ou une erreur (`status=422`/`404`). | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | `render(...)` pour les vues, `csrf_token(...)` pour le jeton. | [BaseController](../../reference/api.md#coremvccontroller) |

## Tester

Depuis le projet Forge déjà créé avec ce starter (migration appliquée) :

```bash
forge run
```

Ouvrez :

```
https://localhost:8000/messages
```

- Ajoutez un message → il apparaît dans la liste.
- Cliquez sur **Modifier** → changez le texte → il est mis à jour.
- Cliquez sur **Supprimer** → la ligne disparaît.

## Les routes

```python
# mvc/routes.py
from mvc.controllers.messages_controller import MessagesController

with router.group("", public=True) as pub:
    pub.add("GET",  "/messages",             MessagesController.index,   name="messages_index")
    pub.add("POST", "/messages",             MessagesController.create,  name="messages_create")
    pub.add("GET",  "/messages/{id}/edit",   MessagesController.edit,    name="messages_edit")
    pub.add("POST", "/messages/{id}",        MessagesController.update,  name="messages_update")
    pub.add("POST", "/messages/{id}/delete", MessagesController.destroy, name="messages_destroy")
```

## Le contrôleur

```python
# mvc/controllers/messages_controller.py
from core.database.db import execute, fetch_all, fetch_one, insert
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL = "SELECT id, content FROM first_sql_messages ORDER BY id DESC"
SELECT_ONE = "SELECT id, content FROM first_sql_messages WHERE id = ?"
INSERT_ONE = "INSERT INTO first_sql_messages (content) VALUES (?)"
UPDATE_ONE = "UPDATE first_sql_messages SET content = ? WHERE id = ?"
DELETE_ONE = "DELETE FROM first_sql_messages WHERE id = ?"


class MessagesController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "messages/index.html",
            request=request,
            context={
                "messages": messages,
                "csrf_token": BaseController.csrf_token(request),
            },
        )

    @staticmethod
    def create(request: Request) -> Response:
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le message est obligatoire", status=422)

        insert(INSERT_ONE, (content,))
        return MessagesController.index(request)

    @staticmethod
    def edit(request: Request) -> Response:
        message = fetch_one(SELECT_ONE, (request.route_param("id"),))
        if message is None:
            return Response.text("Message introuvable", status=404)

        return BaseController.render(
            "messages/edit.html",
            request=request,
            context={
                "message": message,
                "csrf_token": BaseController.csrf_token(request),
            },
        )

    @staticmethod
    def update(request: Request) -> Response:
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le message est obligatoire", status=422)

        execute(UPDATE_ONE, (content, request.route_param("id")))
        return MessagesController.index(request)

    @staticmethod
    def destroy(request: Request) -> Response:
        execute(DELETE_ONE, (request.route_param("id"),))
        return MessagesController.index(request)
```

### Comprendre ce code

- Chaque opération CRUD a sa requête SQL nommée en clair en haut du
  fichier (`SELECT_ALL`, `INSERT_ONE`, …). Le SQL reste **visible** :
  pas d'ORM, pas de magie.
- `request.route_param("id")` lit le segment `{id}` de l'URL (différent de
  `request.form(...)`, qui lit le corps du formulaire, et de
  `request.param(...)`, qui lit la *query string*).
- Forge ne fournit **pas** de redirection. Après une écriture
  (`create`, `update`, `destroy`), on appelle `MessagesController.index(request)`
  pour relire la base et renvoyer la liste à jour. Dans une vraie
  application, on utiliserait le motif *POST-Redirect-GET* ; ici on reste
  au plus simple.
- `create` et `update` refusent un message vide avec un statut
  `422 Unprocessable Entity` — la validation serveur vue au palier
  « Validation serveur ».
- `edit` renvoie `404 Not Found` si l'`id` n'existe pas.

## Les vues

```html
<!-- mvc/views/messages/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>First CRUD — Forge</title>
</head>
<body>
  <h1>Messages</h1>

  <form method="post" action="/messages">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <label for="content">Nouveau message</label>
    <input id="content" name="content" type="text">

    <button type="submit">Ajouter</button>
  </form>

  <ul>
    {% for message in messages %}
    <li>
      {{ message.content }}
      <a href="/messages/{{ message.id }}/edit">Modifier</a>
      <form method="post" action="/messages/{{ message.id }}/delete" style="display:inline">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit">Supprimer</button>
      </form>
    </li>
    {% else %}
    <li>Aucun message pour l'instant.</li>
    {% endfor %}
  </ul>
</body>
</html>
```

```html
<!-- mvc/views/messages/edit.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Modifier un message — Forge</title>
</head>
<body>
  <h1>Modifier le message #{{ message.id }}</h1>

  <form method="post" action="/messages/{{ message.id }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <label for="content">Message</label>
    <input id="content" name="content" type="text" value="{{ message.content }}">

    <button type="submit">Enregistrer</button>
  </form>

  <p><a href="/messages">Retour à la liste</a></p>
</body>
</html>
```

### Comprendre ce code

- Chaque ligne de la liste porte un lien **Modifier** (`GET`) et un
  formulaire **Supprimer** (`POST` avec jeton CSRF) : toute écriture passe
  par un POST protégé, jamais par un simple lien.
- Les lignes renvoyées par `fetch_all` / `fetch_one` sont des
  dictionnaires : `{{ message.content }}` et `{{ message.id }}` y accèdent
  directement.
- Le bloc `{% else %}` de la boucle affiche un message quand la table est
  vide.

## À retenir

- Un CRUD = quatre opérations sur une table : **C**reate (`INSERT`),
  **R**ead (`SELECT`), **U**pdate (`UPDATE`), **D**elete (`DELETE`).
- Forge garde le SQL visible : chaque requête est écrite et nommée par
  vous, sans couche d'abstraction.
- Les écritures se font toujours en `POST` avec un jeton CSRF ;
  les lectures en `GET`.
- Faute de redirection, on relit la base et on ré-affiche la liste après
  chaque écriture.

## Après ce starter

Vous maîtrisez désormais un CRUD complet à SQL visible — le socle de la
plupart des applications Forge.

La suite (premiers starters orientés exemple, authentification…) sera
reliée ici prochainement. En attendant, explorez le
[catalogue complet des starters](../index.md).
