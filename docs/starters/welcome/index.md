# Bonjour Forge

Premier contact avec Forge : afficher une réponse texte. Pas de vue HTML,
pas de base de données, pas de moteur Jinja2.

Ce starter reste le **Starter 7** dans la CLI Forge (identifiant
`welcome`, alias `bienvenue` / `bonjour` / `bonjour-forge`).

## Ce que ce starter installe

- une route `/welcome`
- une route `/welcome/greet`
- un contrôleur `WelcomeController` avec deux méthodes
- aucune vue HTML
- aucune base de données

## Les routes

```python
# mvc/routes.py
from mvc.controllers.welcome_controller import WelcomeController

with router.group("", public=True) as pub:
    pub.add("GET", "/welcome",       WelcomeController.index, name="welcome_index")
    pub.add("GET", "/welcome/greet", WelcomeController.greet, name="welcome_greet")
```

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

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `http://localhost:8000/welcome` | `Bonjour Forge` |
| `http://localhost:8000/welcome/greet` | `Bonjour Forge` |
| `http://localhost:8000/welcome/greet?name=Roger` | `Bonjour Roger` |

## Démarrer

```bash
# Nouveau projet avec le starter pré-appliqué (recommandé)
forge new mon-projet --starter welcome
cd mon-projet
source .venv/bin/activate
forge run
# Ouvrir http://localhost:8000/welcome
```

Ou dans un projet Forge existant :

```bash
forge starter:build 7
forge run
```

## À retenir

- Une URL appelle une route.
- La route appelle une méthode du contrôleur.
- La méthode reçoit `request` et retourne `Response`.
- `Response.text(...)` ne passe par aucun template.

## Après ce starter

Ce premier contact assimilé, la **progression pédagogique officielle**
des starters Forge passe par plusieurs étapes intermédiaires avant
d'aborder un CRUD complet. Le saut direct vers Contacts CRUD est
explicitement déconseillé : Jinja2, routes dynamiques, formulaires POST,
validation serveur et SQL/migrations méritent chacun leur propre starter.

La feuille de route détaillée :
[Progression recommandée des starters](../index.md#progression-recommandee).

En attendant la livraison des starters intermédiaires (tickets
`STARTER-QUERY-PARAMS-001` → `STARTER-FIRST-SQL-001` dans la
[roadmap Forge](../../roadmap/forge-roadmap.md)), le starter Contacts
CRUD reste accessible si vous êtes déjà familier des notions ci-dessus :

```bash
forge starter:build 1 --init-db
```

[Vue d'ensemble des starters](../index.md) · [Starter 1 — Contacts (niveau avancé)](../01-contact-simple/index.md)
