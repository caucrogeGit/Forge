# API JSON légère Forge

[Accueil](../index.html) · [Référence API et CLI](api.md)

---

## Objectif

Forge propose une capacité JSON légère pour construire des endpoints simples sans transformer le framework en moteur d'API.

```text
réponse JSON explicite
+ conventions de contrôleur
+ routes API séparées
+ auth Bearer token minimale
```

Ce n'est pas un équivalent de FastAPI, Django REST Framework ou Symfony API Platform.
C'est une couche minimale, explicite et testable.

---

## Ce que Forge fournit

| Brique | Module | Description |
|---|---|---|
| `json_response(data, status=200)` | `core.http` | Réponse JSON brute |
| `json_error(code, status, message=None)` | `core.http` | Réponse d'erreur, forme unique (ADR-088) |
| `mvc/api_routes.py` | convention projet | Fichier optionnel de routes API |
| `register_api_routes(router)` | convention projet | Fonction d'enregistrement des routes |
| `is_bearer_authorized(request, token)` | `core.http.bearer` | Vérification d'un jeton Bearer, en temps constant |
| `API_TOKEN` | variable d'environnement | Jeton attendu côté serveur, lu par l'application |

## Ce que Forge ne fournit pas encore

- pas de JWT ;
- pas d'OAuth ;
- pas de refresh token ;
- pas de scopes ;
- pas de multi-token ;
- pas de rate limiting API ;
- pas de parsing automatique du body JSON entrant ;
- pas de validation de payload ;
- pas de pagination avancée ;
- pas de versioning `/api/v1` ;
- pas de Swagger / OpenAPI ;
- pas de génération CRUD API.

---

## Réponse JSON simple

Pour retourner un JSON libre :

```python
from core.http import json_response

def status(request):
    return json_response({"status": "ok"})
```

Réponse produite :

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"status": "ok"}
```

`json_response` sérialise tout type compatible `json.dumps` : `dict`, `list`, `str`, `int`, `float`, `bool`, `None`.
Lève `ValueError` si les données ne sont pas sérialisables.

---

## Réponse de succès

Une réponse de succès rend **la ressource**, sans enveloppe.

```python
from core.http import json_response

def status(request):
    return json_response({"status": "ok", "service": "forge"})
```

Réponse :

```json
{"status": "ok", "service": "forge"}
```

Avec un statut personnalisé, à la création :

```python
return json_response({"id": 42}, status=201)
```

Une liste se rend telle quelle, et une métadonnée de comptage se place dans la
ressource quand elle en fait partie :

```python
items = [{"id": 1, "nom": "Alice"}, {"id": 2, "nom": "Bob"}]
return json_response({"items": items, "count": len(items)})
```

!!! info "Pourquoi pas d'enveloppe `success` / `data`"
    Forge a longtemps proposé `api_success` et `api_error`, qui enveloppaient
    la réponse dans `{"success": ..., "data": ...}`.
    L'ADR-088 les a retirés, pour deux raisons.

    Le code HTTP porte déjà l'information de succès, et Forge le traite comme
    tel avec soin, 405 accompagné de son en-tête `Allow`, 503 distinct du 500,
    401 distinct d'une redirection. Un champ `success` la redoublait.

    Et l'enveloppe n'avait **aucun adoptant** : quand les trois opt-ins de
    Forge exposant du JSON ont eu ce besoin, les trois ont rendu la ressource
    directement.

---

## Réponse d'erreur

Une réponse d'erreur rend un objet plat, produit par `json_error`.

```python
from core.http import json_error

def show(request):
    return json_error("not_found", 404)
```

Réponse :

```json
{"error": "not_found"}
```

Le `code` est un identifiant **stable et lisible par une machine**, jamais une
phrase destinée à un humain. Un client teste `error == "not_found"`, il ne lit
pas un message.

### Le champ `message`, réservé à la validation

```python
return json_error("validation_error", 422, message="email est obligatoire")
```

```json
{"error": "validation_error", "message": "email est obligatoire"}
```

C'est le **seul** cas prévu, celui où le client a besoin de savoir quoi
corriger.

!!! warning "Ne pas expliquer un refus"
    Une erreur d'authentification ou d'autorisation ne porte pas de message.

    Distinguer « en-tête absent », « schéma invalide » et « jeton invalide »
    renseigne un attaquant sur l'étape qu'il a franchie, et lui indique où
    porter son effort suivant.

    C'est la raison pour laquelle l'ADR-088 a retiré l'implémentation qui
    faisait cette distinction, au profit de celle des opt-ins, qui rend un
    refus opaque.

### Statuts HTTP recommandés

| Cas | Statut |
|---|---|
| Succès lecture | 200 |
| Création | 201 |
| Requête invalide | 400 |
| Non authentifié | 401 |
| Interdit | 403 |
| Introuvable | 404 |
| Erreur de validation | 422 |
| Erreur serveur | 500 |

---

## Contrôleur JSON

Un contrôleur JSON Forge est un contrôleur normal qui retourne une réponse JSON :

```python
# mvc/controllers/api_contacts_controller.py

from core.http import json_error, json_response


def index(request):
    contacts = [{"id": 1, "nom": "Alice"}, {"id": 2, "nom": "Bob"}]
    return json_response({"contacts": contacts, "count": len(contacts)})


def show(request):
    contact_id = int(request.route_params.get("id", 0))
    contact = None  # remplacer par une vraie requête DB
    if contact is None:
        return json_error("not_found", 404)
    return json_response(contact)


def create(request):
    # créer le contact...
    return json_response({"id": 42}, status=201)
```

Pas d'héritage spécifique requis, un contrôleur API est une fonction Python ordinaire.

---

## Routes API séparées

Les routes API se déclarent dans un fichier optionnel `mvc/api_routes.py`.
Si ce fichier est absent, l'application fonctionne normalement.
S'il est présent, il est chargé automatiquement par `Application` au démarrage.

```python
# mvc/api_routes.py

from mvc.controllers import api_contacts_controller

def register_api_routes(router):
    with router.group("/api", public=False, api=True) as api:
        api.add("GET",  "/contacts",      api_contacts_controller.index,  name="api_contacts")
        api.add("GET",  "/contacts/{id}", api_contacts_controller.show,   name="api_contact_show")
        api.add("POST", "/contacts",      api_contacts_controller.create, name="api_contact_create",
                csrf=False)
```

Les routes HTML restent dans `mvc/routes/__init__.py`.
Les deux fichiers partagent le même routeur mais sont séparés organisationnellement.

Le drapeau `api=True` **modifie le comportement** de la route depuis le ticket `CORE-ROUTE-API-FLAG-001` : les refus et erreurs que le framework produit après avoir trouvé la route sont rendus en JSON, jamais en redirection ni en page HTML.
Le détail figure dans [la documentation du routeur](../core-http/router.md).

Le drapeau `csrf=False` est recommandé pour les routes d'API, qui s'authentifient par jeton Bearer et non par session, donc n'ont pas de jeton CSRF à présenter.

---

## Authentification API minimale

### Configuration

Définir le token attendu dans le fichier d'environnement :

```bash
# env/dev ou env/prod
API_TOKEN=votre-token-secret
```

!!! warning "Ne jamais versionner `API_TOKEN`"
    Le fichier `env/dev` et `env/prod` ne doivent pas être dans Git.
    Utilisez `.gitignore` pour les exclure.

### Protéger une route

La vérification est **explicite**, dans le contrôleur, par `is_bearer_authorized`.

```python
# mvc/controllers/api_status_controller.py

import os

from core.http import json_error, json_response
from core.http.bearer import is_bearer_authorized


def status(request):
    if not is_bearer_authorized(request, os.getenv("API_TOKEN") or None):
        return json_error("unauthorized", 401)
    return json_response({"status": "ok", "service": "forge"})
```

`is_bearer_authorized` compare le jeton en temps constant, avec
`secrets.compare_digest`, ce qui écarte les attaques par mesure du temps de
réponse.

!!! danger "Jeton absent égale API ouverte"
    Quand le second argument vaut `None`, `is_bearer_authorized` **autorise
    tout le monde**. C'est le mode local et pédagogique, et c'est un piège en
    production.

    Refusez de démarrer plutôt que de servir une API ouverte sans le savoir.
    C'est ce que fait `forge-mvc-iot`, dont vous pouvez reprendre le geste.

    ```python
    def register_api_routes(router):
        if os.getenv("APP_ENV") == "prod" and not os.getenv("API_TOKEN"):
            raise RuntimeError(
                "API ouverte interdite en production : définir API_TOKEN."
            )
        ...
    ```

### Requête authentifiée

```http
GET /api/status HTTP/1.1
Authorization: Bearer votre-token-secret
```

Avec `curl` :

```bash
curl -H "Authorization: Bearer <token>" https://example.com/api/status
```

Réponse si le jeton est valide :

```json
{"status": "ok", "service": "forge"}
```

---

## Réponses d'erreur d'authentification

Un seul code, et c'est délibéré.

| Situation | Statut | Corps |
|---|---|---|
| En-tête `Authorization` absent | 401 | `{"error": "unauthorized"}` |
| Format invalide (`Token …`, `Basic …`) | 401 | `{"error": "unauthorized"}` |
| Jeton invalide | 401 | `{"error": "unauthorized"}` |

!!! info "Pourquoi un seul code"
    Distinguer « en-tête absent », « schéma invalide » et « jeton invalide »
    renseigne un attaquant sur l'étape qu'il a franchie, et lui indique où
    porter son effort suivant.

    Forge rend donc un refus **opaque**. C'est la pratique qu'avaient adoptée
    d'eux-mêmes `forge-mvc-iot`, `forge-mvc-video` et `forge-mvc-audio`, et que
    l'ADR-088 a retenue en retirant l'implémentation concurrente qui distinguait
    trois causes.

---

## Exemple complet minimal

### 1. Configuration d'environnement

```bash
# env/prod
API_TOKEN=changeme-en-production
```

### 2. Contrôleur

```python
# mvc/controllers/api_status_controller.py

import os

from core.http import json_error, json_response
from core.http.bearer import is_bearer_authorized


def status(request):
    if not is_bearer_authorized(request, os.getenv("API_TOKEN") or None):
        return json_error("unauthorized", 401)
    return json_response({"status": "ok", "version": "1.0"})
```

### 3. Routes API

```python
# mvc/api_routes.py

import os

from mvc.controllers import api_status_controller


def register_api_routes(router):
    if os.getenv("APP_ENV") == "prod" and not os.getenv("API_TOKEN"):
        raise RuntimeError("API ouverte interdite en production : définir API_TOKEN.")
    router.add("GET", "/api/status", api_status_controller.status,
               public=True, api=True)
```

### 4. Vérification avec curl

```bash
# Token absent → 401
curl https://example.com/api/status

# Token valide → 200
curl -H "Authorization: Bearer changeme-en-production" \
     https://example.com/api/status
```

---

## Sécurité

- **Utiliser uniquement en HTTPS**, un Bearer token en HTTP clair est interceptable.
- **Ne pas exposer `API_TOKEN` dans Git**, utilisez `env/prod` hors versionnement.
- **Ne pas afficher le token dans les logs**, `core.http.bearer` ne le journalise jamais et ne le renvoie dans aucune réponse.
- **Rotation des tokens**, changer `API_TOKEN` régulièrement en production.
- **Auth minimale**, cette approche est adaptée aux projets simples.
  Pour une application SaaS publique ou multi-utilisateur, envisagez JWT ou OAuth dans un ticket futur.

---

## Limites actuelles

| Limite | Statut |
|---|---|
| Parsing automatique du body JSON entrant | non, utiliser `request.json_body` |
| Validation de payload | non |
| Pagination avancée | non, `meta.count` disponible mais pas de helper de pagination |
| Versioning `/api/v1` | non |
| JWT / OAuth | non |
| Multi-token / scopes | non |
| Rate limiting API | non |
| Documentation OpenAPI / Swagger | non |
| Génération CRUD API | non |

---

## Tickets futurs possibles

| Ticket | Sujet |
|---|---|
| `API-BODY-001` | Parsing automatique du body JSON entrant |
| `API-VALIDATE-001` | Validation de payload JSON |
| `API-PAGINATE-001` | Helper de pagination JSON |
| `API-RATE-LIMIT-001` | Rate limiting API |
| `API-JWT-001` | Auth JWT |

---

## Voir aussi

- [Référence API et CLI](api.md), documentation complète des modules
- [Sécurité et RBAC](../philosophy/security.md), sécurité générale Forge
- [Déploiement avancé](../deployment/deploy-advanced.md), HTTPS, Nginx, production
- [Contrat de stabilité](../release/stability-contract.md), garanties sur les API publiques
