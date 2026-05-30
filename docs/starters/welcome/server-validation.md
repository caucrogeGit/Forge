# Validation serveur

Objectif : vérifier côté serveur une valeur reçue depuis un
formulaire.

**Ce que vous allez apprendre :** ne jamais faire confiance au client —
valider une donnée côté serveur, refuser une valeur vide et répondre
avec un statut `422 Unprocessable Entity` plutôt qu'un `200` trompeur.

Palier 9 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Premier formulaire POST](form-post.md).

*Prérequis : savoir afficher et traiter un formulaire POST (palier 8).*

## Ce que ce starter montre

- une route `GET /server-validation`
- une route `POST /server-validation`
- un formulaire HTML minimal
- une lecture avec `request.form(...)`
- une vérification simple côté serveur
- une réponse `422` si la valeur est vide

Aucune base de données.
Aucun CRUD.
Aucun système complet de validation.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Lire le champ envoyé avec `request.form(...)`. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Construire la réponse texte, succès ou erreur (`status=422`). | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../reference/api.md#coremvccontroller) |

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
https://localhost:8000/server-validation
```

Essayez deux cas :

- **Prénom = `Roger`** → `Bonjour Roger`
- **Prénom vide** → `Le prénom est obligatoire` (HTTP 422)

## Les routes

```python
# mvc/routes.py
from mvc.controllers.server_validation_controller import ServerValidationController

with router.group("", public=True) as pub:
    pub.add("GET",  "/server-validation", ServerValidationController.index,  name="server_validation_index")
    pub.add("POST", "/server-validation", ServerValidationController.submit, name="server_validation_submit")
```

## Le contrôleur

```python
# mvc/controllers/server_validation_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class ServerValidationController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        csrf_token = BaseController.csrf_token(request)
        return BaseController.render(
            "server_validation/index.html",
            context={"csrf_token": csrf_token},
            request=request,
        )

    @staticmethod
    def submit(request: Request) -> Response:
        name = request.form("name", default="").strip()

        if not name:
            return Response.text("Le prénom est obligatoire", status=422)

        return Response.text(f"Bonjour {name}")
```

### Comprendre ce code

- `request.form("name", default="").strip()` lit la valeur soumise et
  supprime les espaces autour. Le `default=""` évite un `None` à gérer.
- `if not name:` détecte les cas vides (chaîne vide, espaces uniquement).
  C'est la **validation côté serveur** dans sa forme la plus simple.
- Si la donnée est invalide, le contrôleur retourne `422 Unprocessable
  Entity` avec un message d'erreur — pas un `200` trompeur.
- Règle d'or : **le serveur ne fait jamais confiance aux données reçues**.
  Toute requête peut venir d'un client modifié (curl, JS désactivé,
  Postman), donc la validation client doit toujours être doublée
  côté serveur.

## La vue

```html
<!-- mvc/views/server_validation/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Validation serveur — Forge</title>
</head>
<body>
  <h1>Validation serveur</h1>

  <form method="post" action="/server-validation">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <label for="name">Prénom</label>
    <input id="name" name="name" type="text">

    <button type="submit">Envoyer</button>
  </form>
</body>
</html>
```

## À retenir

- Le navigateur peut envoyer n'importe quelle valeur — même rien,
  même un espace, même un contenu inattendu.
- Le serveur doit toujours vérifier ce qu'il reçoit avant de
  l'utiliser. Ici, on vérifie simplement que `name` n'est pas vide
  après `.strip()`.
- Le statut HTTP `422 Unprocessable Entity` indique « la requête est
  bien formée mais les données ne sont pas exploitables ».
- La validation complète d'une application (règles multiples,
  messages d'erreur réaffichés dans le formulaire, conservation des
  anciennes valeurs) viendra plus tard avec un système dédié — ce
  starter reste le **contrôle minimum**.

## Après ce starter

Passez au palier suivant : **Première base SQL**.

Vous y apprendrez à lire une donnée depuis MariaDB avec du SQL
visible :

```python
from core.database.db import fetch_one

row = fetch_one("SELECT content FROM first_sql_messages ORDER BY id LIMIT 1")
```

[Continuer avec Première base SQL](first-sql.md)
