# Bonjour Forge

Objectif : afficher une réponse texte avec Forge et comprendre le cycle
requête → contrôleur → réponse.

**Ce que vous allez apprendre :** écrire votre premier contrôleur Forge,
déclarer une route dans `mvc/routes.py`, et renvoyer une réponse texte
avec `Response.text(...)`, sans vue HTML, sans base de données et sans
moteur de template.

Ce starter est identifié par `welcome` dans la CLI Forge
(aliases `bienvenue` / `bonjour` / `bonjour-forge`).

Ce guide vous montre comment créer manuellement les fichiers du starter
pour bien comprendre le fonctionnement de Forge. Si vous préférez obtenir
directement le résultat final sans faire l’exercice, le préambule
d’[installation](../installation.md) construit le starter pour vous.

## Fichiers déjà présents dans un projet Forge nu

Avant d’installer ce starter, un projet Forge généré à partir du squelette
nu contient déjà notamment :

- `mvc/routes.py` avec la route d’accueil `/`
- `mvc/controllers/home_controller.py`
- `mvc/controllers/welcome_controller.py` peut déjà être présent
- le routeur principal et la configuration de base du projet

## Ce que ce starter installe

- une route `/welcome`
- un contrôleur `WelcomeController` avec une méthode `index`
- une réponse texte via `Response.text(...)`
- aucune vue HTML
- aucune base de données

## Classes Forge utilisées

Ces classes sont les notions de base utilisées dans ce starter :
- `Request` représente la requête envoyée par le navigateur.
- `Response` représente la réponse renvoyée au navigateur.
- `BaseController` est la classe parente qui permet de définir un contrôleur
  compatible avec le routeur Forge.

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçoit les données de la requête. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Génère la réponse texte avec `Response.text(...)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente de `WelcomeController`. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Le contrôleur

Un contrôleur est une classe qui reçoit la requête, exécute la logique et
retourne une réponse. C’est le point de contact entre le routeur et le
code métier qui construit la réponse.

Ouvrez (ou créez si nécessaire) le fichier `mvc/controllers/welcome_controller.py`

```python
# mvc/controllers/welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")
```

### Comprendre ce code

- `WelcomeController` hérite de `BaseController`, ce qui en fait un
  contrôleur Forge utilisable par le routeur.
- Chaque action reçoit un `request: Request` et doit retourner un
  `Response`.
- `Response.text(...)` construit une réponse `text/plain` ; aucun template
  HTML n'est rendu ici.
- La lecture des paramètres d'URL avec `request.param(...)` est abordée au
  palier suivant (`query-params`).

## Les routes

Une route définit l’URL et le verbe HTTP qu’un navigateur utilise, puis
l’associe à une action de contrôleur. C’est le lien entre l’adresse web
et le code qui répond à la requête.

Dans le fichier `mvc/routes.py`, ajoutez la route qui relie le chemin au
contrôleur que vous venez de créer.

```python
# mvc/routes.py
from mvc.controllers.welcome_controller import WelcomeController

with router.group("", public=True) as pub:
    pub.add("GET", "/welcome", WelcomeController.index, name="welcome_index")
```

### Comprendre ce code

- `router.group("", public=True)` ouvre un espace de routes publiques
  (sans authentification et sans préfixe d'URL).
- `pub.add(...)` enregistre une route avec son verbe HTTP, son chemin,
  la méthode de contrôleur à exécuter et un `name=`.
- Le nom de route permet de générer l'URL ailleurs sans la coder en dur.
- Au démarrage, le routeur lit ce fichier et oriente chaque requête vers la
  méthode correspondante.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome` | `Bonjour Forge` |

## À retenir

- Une URL est mappée à une route.
- La route appelle une méthode du contrôleur.
- La méthode reçoit `request` et retourne `Response`.
- `Response.text(...)` renvoie du texte brut sans template.

## Après ce starter

Passez au palier suivant : **Paramètres d'URL**.
Vous y apprendrez à récupérer une valeur dans l'adresse
(`?name=...`) avec `request.param(...)`.

[Continuer avec Paramètres d'URL](query-params.md)
