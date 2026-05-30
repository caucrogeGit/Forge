# Le jeton CSRF

Objectif : comprendre le jeton CSRF et le placer dans un formulaire.

**Ce que vous allez apprendre :** pourquoi Forge protège les
formulaires contre les attaques **CSRF**, et comment fournir le jeton
attendu via un champ caché généré par `BaseController.csrf_token(...)`.
Le traitement du POST viendra au palier suivant.

Palier 7 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Réponse JSON](json-response.md).

## Ce que ce starter montre

- une route `GET /csrf`
- un contrôleur `CsrfController`
- un formulaire HTML avec le champ caché `csrf_token`
- la génération du jeton avec `BaseController.csrf_token(request)`

Aucune base de données.
Le **traitement** du POST est l'objet du palier suivant (`form-post`).

## Pourquoi un jeton CSRF ?

Une attaque **CSRF** (Cross-Site Request Forgery) fait exécuter une
action à l'utilisateur **à son insu** : un site malveillant soumet un
formulaire vers votre application en réutilisant la session de la
victime. Pour s'en protéger, Forge exige sur chaque requête POST un
**jeton secret** que seul votre serveur connaît :

1. le serveur génère un jeton lié à la session et l'injecte dans le
   formulaire (champ caché `csrf_token`) ;
2. à la soumission, le middleware Forge compare le jeton reçu à celui
   de la session — en temps constant ;
3. s'ils ne correspondent pas (ou si le jeton est absent), la requête
   est **refusée**.

Un site tiers ne peut pas deviner ce jeton : il ne peut donc pas forger
de POST valide.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par la méthode du contrôleur. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Renvoie la page rendue. | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | `render(...)` + `csrf_token(...)`. | [BaseController](../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/csrf` : la page affiche un formulaire.
Inspectez le HTML (clic droit → code source) : le champ caché
`csrf_token` contient une valeur générée par le serveur.

## Les routes

```python
# mvc/routes.py
from mvc.controllers.csrf_controller import CsrfController

with router.group("", public=True) as pub:
    pub.add("GET", "/csrf", CsrfController.index, name="csrf_index")
```

## Le contrôleur

```python
# mvc/controllers/csrf_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class CsrfController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "csrf/index.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )
```

### Comprendre ce code

- `BaseController.csrf_token(request)` génère (ou réutilise) le jeton lié
  à la session courante et le renvoie pour l'injecter dans la vue.
- Le jeton est passé au template via `context={"csrf_token": ...}` puis
  rendu dans un champ caché.
- Aucune vérification ici : c'est le **middleware CSRF** de Forge qui
  vérifie automatiquement le jeton sur les requêtes POST (palier suivant).

## La vue

```html
<!-- mvc/views/csrf/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Le jeton CSRF — Forge</title>
</head>
<body>
  <h1>Le jeton CSRF</h1>

  <!-- Formulaire illustratif : pas de soumission ici (voir form-post). -->
  <form>
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <label for="name">Prénom</label>
    <input id="name" name="name" type="text">
  </form>
</body>
</html>
```

### Comprendre ce code

- Le champ caché `csrf_token` transporte le jeton dans le corps du POST.
- `{{ csrf_token }}` est la valeur injectée par le contrôleur.
- Sans ce champ, Forge refuse la soumission.

## À retenir

- CSRF = un site tiers qui forge une requête en réutilisant votre
  session ; le jeton secret l'empêche.
- Le jeton se génère avec `BaseController.csrf_token(request)` et se
  place dans un champ caché `csrf_token`.
- Forge le vérifie automatiquement (middleware) sur chaque POST, en
  temps constant.

## Après ce starter

Passez au palier suivant : **Premier formulaire POST** — vous y
apprendrez à **traiter** la soumission et à lire la valeur envoyée avec
`request.form(...)`.

[Continuer avec Premier formulaire POST](form-post.md)
