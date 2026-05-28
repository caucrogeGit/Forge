# Bonjour Forge

Premier contact avec Forge : afficher une réponse texte. Pas de vue HTML,
pas de base de données, pas de moteur Jinja2.

Identifiant : `welcome` (alias `bienvenue` / `bonjour` / `bonjour-forge`).

## Ce que ce starter installe

- une route `/welcome`
- une route `/welcome/greet`
- un contrôleur `WelcomeController` avec deux méthodes
- aucune vue HTML
- aucune base de données

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par chaque méthode du contrôleur. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Construire la réponse texte avec `Response.text(...)`. | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../reference/api.md#coremvccontroller) |

## Les routes

```python
# mvc/routes.py
from mvc.controllers.welcome_controller import WelcomeController

with router.group("", public=True) as pub:
    pub.add("GET", "/welcome",       WelcomeController.index, name="welcome_index")
    pub.add("GET", "/welcome/greet", WelcomeController.greet, name="welcome_greet")
```

### Comprendre ce code

- `router.group("", public=True)` ouvre un groupe de routes publiques
  (sans authentification requise) et sans préfixe d'URL.
- Chaque `pub.add(...)` enregistre une route : verbe HTTP, URL, méthode
  de contrôleur à appeler, et un `name=` pour générer l'URL ailleurs
  sans la coder en dur.
- Le routeur lit ce fichier au démarrage et oriente chaque requête
  entrante vers la bonne méthode.

## Le contrôleur

```python
# mvc/controllers/welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")

    @staticmethod
    def greet(request: Request) -> Response:
        name = request.param("name", default="Forge")
        return Response.text(f"Bonjour {name}")
```

### Comprendre ce code

- `WelcomeController` hérite de `BaseController` — c'est ce qui en fait
  un contrôleur Forge utilisable par le routeur.
- Chaque action reçoit `request: Request` et doit renvoyer `Response`.
  C'est la signature unique d'une méthode de contrôleur Forge.
- `Response.text(...)` produit une réponse `text/plain` ; aucun template
  HTML n'est rendu à ce stade.
- `request.param("name", default="Forge")` lit la valeur de `?name=...`
  dans l'URL. Si la clé est absente, `default` est retourné — pas
  d'exception, pas de `None` à manipuler.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `http://localhost:8000/welcome` | `Bonjour Forge` |
| `http://localhost:8000/welcome/greet` | `Bonjour Forge` |
| `http://localhost:8000/welcome/greet?name=Roger` | `Bonjour Roger` |

## À retenir

- Une URL appelle une route.
- La route appelle une méthode du contrôleur.
- La méthode reçoit `request` et retourne `Response`.
- `Response.text(...)` ne passe par aucun template.

## Après ce starter

Passez au palier suivant : **Paramètres d'URL**.

Vous y apprendrez à lire une valeur transmise dans l'adresse, par
exemple :

```text
/query-params/hello?name=Roger
```

avec :

```python
request.param("name", default="Forge")
```

[Continuer avec Paramètres d'URL](../query-params/index.md)
