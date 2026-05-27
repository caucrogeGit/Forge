# Bonjour Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Premier contact avec Forge : du chemin le plus court entre une requête
HTTP et une réponse, jusqu'à l'introduction d'une vue HTML. Sans base
de données. Sans entité. Sans CRUD.

Ce parcours suit l'ordre pédagogique du starter d'entrée
[Bonjour Forge](starters/welcome/index.md) :

```text
forge run → route → contrôleur → Request → Response.text(...)
                                         → Response.debug(...)
                                         → BaseController.render(...)
```

!!! tip "Forge n'est pas encore installé ?"
    Commencez par le parcours d'installation :
    [VM Debian vierge](install/vm-debian.md),
    [pipx](install/pipx.md),
    [depuis GitHub](install/github.md),
    [Windows + WSL (parcours complet)](install/windows-wsl.md).

---

## 1. Lancer Forge avec `forge run`

Une fois Forge installé et un projet créé (`forge new mon-projet`), la
commande officielle de développement est :

```bash
forge run
```

`forge run` lit `APP_ENV` (défaut `dev`), démarre le serveur de
développement et active l'autoreload : `python app.py` est redémarré
automatiquement dès qu'un fichier applicatif change. Pour désactiver
l'autoreload (chemin legacy) :

```bash
forge run --no-reload
```

En production (`APP_ENV=prod`), `forge run` refuse de démarrer le
serveur intégré et affiche la stratégie WSGI recommandée — voir
[Déploiement WSGI minimal](wsgi-deployment.md).

Une fois le serveur démarré, ouvrez `https://localhost:8000/welcome`
dans votre navigateur.

---

## 2. Comprendre la route

Toutes les routes Forge sont déclarées **explicitement** dans
`mvc/routes.py`. Aucune découverte automatique, aucune convention
cachée :

```python
# mvc/routes.py
from mvc.controllers.welcome_controller import WelcomeController

with router.group("", public=True) as pub:
    pub.add("GET", "/welcome",         WelcomeController.index,   name="welcome_index")
    pub.add("GET", "/welcome/greet",   WelcomeController.greet,   name="welcome_greet")
    pub.add("GET", "/welcome/inspect", WelcomeController.inspect, name="welcome_inspect")
    pub.add("GET", "/welcome/cycle",   WelcomeController.cycle,   name="welcome_cycle")
```

Chaque ligne associe une méthode HTTP et un chemin à une méthode de
contrôleur. Ce qui est dans `mvc/routes.py` est exactement ce qui est
routé.

---

## 3. Comprendre le contrôleur

Un contrôleur Forge est une classe Python qui reçoit une `Request` et
retourne une `Response`. Les méthodes sont statiques, typées et
explicites :

```python
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):
    @staticmethod
    def index(request: Request) -> Response:
        ...
```

Les annotations `request: Request -> Response` sont systématiques pour
que Pylance/VS Code propose l'autocomplétion sur `request.param(...)`,
`request.form(...)`, `request.json(...)`, `request.file(...)`,
`request.route_param(...)`, `request.header(...)` et `request.data`
sans import manuel. Voir
[Convention HTTP inspectable](reference/http.md).

---

## 4. Retourner `Response.text("Bonjour Forge")`

La méthode la plus courte : aucun template, aucun moteur Jinja2.

```python
@staticmethod
def index(request: Request) -> Response:
    return Response.text("Bonjour Forge")
```

`Response.text(...)` produit une réponse `text/plain; charset=utf-8`.
Le navigateur sur `/welcome` affiche simplement :

```text
Bonjour Forge
```

Le cycle complet est minimal :

```text
Navigateur → GET /welcome → Router → WelcomeController.index(request) → Response.text(...)
```

---

## 5. Utiliser `request.param(...)`

`request.param("name", default="Forge")` retourne la première valeur
du paramètre `?name=...`, ou la valeur par défaut.

```python
@staticmethod
def greet(request: Request) -> Response:
    name = request.param("name", default="Forge")
    return Response.text(f"Bonjour {name}")
```

- `https://localhost:8000/welcome/greet?name=Roger` → `Bonjour Roger`
- `https://localhost:8000/welcome/greet` → `Bonjour Forge`

D'autres accesseurs nommés couvrent les autres canaux d'entrée :

| Accesseur | Lit | Retourne |
|---|---|---|
| `request.param(key, default=None)` | query string | `str` ou `default` |
| `request.form(key, default=None)` | formulaire `application/x-www-form-urlencoded` | `str` ou `default` |
| `request.json(key, default=None)` | body JSON | valeur JSON ou `default` |
| `request.header(name, default=None)` | en-têtes HTTP (insensible à la casse) | `str` ou `default` |
| `request.route_param(key, default=None)` | paramètres dynamiques (`/contacts/{id}`) | `str` ou `default` |
| `request.file(key, default=None)` | upload `multipart/form-data` | `UploadedFile` ou `default` |

---

## 6. Inspecter `request.data`

`request.data` retourne un dictionnaire stable décrivant la requête
courante (méthode, chemin, paramètres, headers, body, fichiers). Les
champs sensibles (`Authorization`, `Cookie`, `password`, `csrf_token`,
`token`, `secret`, `api_key`, …) sont automatiquement remplacés par
`[masked]`.

```python
request.data
# {
#   "method": "GET",
#   "path": "/welcome/inspect",
#   "ip": "127.0.0.1",
#   "params": {},
#   "route_params": {},
#   "headers": {"User-Agent": "curl/8.0", "Authorization": "[masked]"},
#   "body": {},
#   "json_body": {},
#   "files": {}
# }
```

C'est une **vue publique**, sûre à afficher en développement, jamais
un dump brut de `request.__dict__`. Voir
[Convention HTTP inspectable](reference/http.md).

---

## 7. Utiliser `Response.debug(request.data)`

`Response.debug(obj)` rend une page HTML pédagogique titrée « Debug
Forge » **en développement** et refuse en production.

```python
@staticmethod
def inspect(request: Request) -> Response:
    return Response.debug(request.data)
```

Visitez `https://localhost:8000/welcome/inspect` : Forge affiche un
dump HTML lisible (échappé, masqué) de la requête courante.

| Environnement | Comportement |
|---|---|
| `APP_ENV=dev` | Page HTML masquée, titre « Debug Forge », clés/valeurs lisibles |
| `APP_ENV=prod` | 404 minimal, **aucune** fuite du payload |

Le renderer borne la profondeur (`MAX_DEPTH=5`), détecte les
références circulaires (`<cycle detected>`), échappe systématiquement
les chaînes HTML et masque les clés sensibles. Voir
[Convention HTTP inspectable](reference/http.md#responsedebugobj).

---

## 8. Comprendre `BaseController.render(...)`

Quand on a besoin de pages HTML structurées (layout, navigation,
templates Jinja2), on passe à `BaseController.render(...)`. Forge
cherche le chemin sous `mvc/views/` :

```python
@staticmethod
def cycle(request: Request) -> Response:
    return BaseController.render("welcome/cycle.html", request=request)
```

Forge cherche alors la vue dans :

```text
mvc/views/welcome/cycle.html
```

---

## `Response.text(...)` vs `BaseController.render(...)`

La confusion la plus fréquente pour un débutant — à ne pas confondre :

```python
# Texte brut — pas de moteur de template, aucune vue requise.
return Response.text("Bonjour Forge")

# Vue template Jinja2 — Forge cherche mvc/views/welcome/index.html.
return BaseController.render("welcome/index.html", request=request)

# Inspection d'un objet en développement.
return Response.debug(request.data)
```

Si un contrôleur appelle `BaseController.render("bonjour", ...)` et
que `mvc/views/bonjour` n'existe pas, Forge renvoie en `APP_ENV=dev`
un message d'erreur explicite (`text/plain`, statut 500) qui rappelle
le rôle de `render()` et propose `Response.text(...)` /
`Response.debug(...)`. En `APP_ENV=prod`, le message reste minimal —
pas de fuite du chemin demandé ni du dossier `views/`. Voir le ticket
`DX-RENDER-ERROR-001` dans la [roadmap Forge](roadmap/forge-roadmap.md).

---

## Récapitulatif des outils livrés

Cette progression met en jeu les briques DX livrées en phase beta 11 :

| Brique | Rôle |
|---|---|
| `forge run` | Point d'entrée officiel — autoreload par défaut en dev |
| `Request` inspectable | Accesseurs nommés + `request.data` masqué |
| `Response.text(...)` | Réponse `text/plain; charset=utf-8` |
| `Response.html(...)` | Réponse `text/html; charset=utf-8` |
| `Response.json(...)` | Réponse `application/json; charset=utf-8` |
| `Response.debug(obj)` | Page HTML pédagogique en dev, 404 en prod |
| Squelettes typés | `request: Request -> Response` partout par défaut |
| Erreur render pédagogique | Message clair si la vue n'existe pas (dev) |
| Starter `welcome` (`Bonjour Forge`) | Parcours d'entrée sans BDD |

---

## Aller plus loin

Une fois ce premier contact assimilé :

| Étape | Ressource |
|---|---|
| Démarrer un projet réel | [Démarrer avec Forge](getting-started.md) |
| Parcours guidé avec MariaDB | [Guide de démarrage](guide.md) |
| Première application complète | [Application complète](app-complete-tutorial.md) |
| Catalogue des starters | [Vue d'ensemble des starters](starters/index.md) |
| Détails du starter `welcome` | [Bonjour Forge — starter](starters/welcome/index.md) |
| Référence HTTP complète | [Convention HTTP inspectable](reference/http.md) |
| Toutes les commandes CLI | [Commandes CLI](reference/cli-commands.md) |

---

## Voir aussi

- [API Forge complète](reference/api.md)
- [Roadmap Forge](roadmap/forge-roadmap.md) — tickets DX livrés en phase beta 11
- [Contrat de stabilité](stability-contract.md) — fichiers garantis préservés
- [Release et compatibilité](release-and-compatibility.md) — versions supportées
