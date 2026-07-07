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
| `api_success(data, status=200, meta=None)` | `core.http` | Réponse JSON structurée, succès |
| `api_error(message, status=400, code, details)` | `core.http` | Réponse JSON structurée, erreur |
| `mvc/api_routes.py` | convention projet | Fichier optionnel de routes API |
| `register_api_routes(router)` | convention projet | Fonction d'enregistrement des routes |
| `@require_api_token` | `core.security.api_auth` | Protection par token Bearer |
| `API_TOKEN` | variable d'environnement | Token attendu côté serveur |

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

## Réponse de succès structurée

Pour une réponse structurée avec `success/data` :

```python
from core.http import api_success

def status(request):
    return api_success({
        "status": "ok",
        "service": "forge"
    })
```

Réponse :

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "forge"
  }
}
```

Avec statut HTTP personnalisé (création) :

```python
return api_success({"id": 42}, status=201)
```

Avec liste et métadonnées :

```python
items = [{"id": 1, "nom": "Alice"}, {"id": 2, "nom": "Bob"}]
return api_success(items, meta={"count": len(items)})
```

Résultat :

```json
{
  "success": true,
  "data": [{"id": 1, "nom": "Alice"}, {"id": 2, "nom": "Bob"}],
  "meta": {"count": 2}
}
```

---

## Réponse d'erreur structurée

```python
from core.http import api_error

def show(request):
    return api_error(
        "Ressource introuvable",
        status=404,
        code="not_found"
    )
```

Réponse :

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Ressource introuvable"
  }
}
```

Avec détails de validation :

```python
return api_error(
    "Données invalides",
    status=422,
    code="validation_error",
    details={"email": "Champ obligatoire"}
)
```

Résultat :

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Données invalides",
    "details": {"email": "Champ obligatoire"}
  }
}
```

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

from core.http import api_success, api_error

def index(request):
    contacts = [{"id": 1, "nom": "Alice"}, {"id": 2, "nom": "Bob"}]
    return api_success(contacts, meta={"count": len(contacts)})

def show(request):
    contact_id = int(request.route_params.get("id", 0))
    contact = None  # remplacer par une vraie requête DB
    if contact is None:
        return api_error("Contact introuvable", status=404, code="not_found")
    return api_success(contact)

def create(request):
    # créer le contact...
    return api_success({"id": 42}, status=201)
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

Le flag `api=True` est déclaratif, il identifie les routes API sans modifier leur comportement.
Le flag `csrf=False` est recommandé pour les routes API qui reçoivent du JSON, car elles utilisent le token Bearer plutôt que le CSRF.

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

```python
# mvc/controllers/api_status_controller.py

from core.http import api_success
from core.security.api_auth import require_api_token

@require_api_token
def status(request):
    return api_success({"status": "ok", "service": "forge"})
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

Réponse si token valide :

```json
{"success": true, "data": {"status": "ok", "service": "forge"}}
```

---

## Réponses d'erreur d'authentification

| Situation | Statut | `error.code` |
|---|---|---|
| Header `Authorization` absent | 401 | `unauthorized` |
| Format invalide (`Token …`, `Basic …`) | 401 | `invalid_authorization_header` |
| Token invalide | 401 | `invalid_token` |
| `API_TOKEN` non configuré côté serveur | 401 | `invalid_token` |

Exemple :

```json
{
  "success": false,
  "error": {
    "code": "unauthorized",
    "message": "Authentification API requise"
  }
}
```

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

from core.http import api_success
from core.security.api_auth import require_api_token

@require_api_token
def status(request):
    return api_success({"status": "ok", "version": "1.0"})
```

### 3. Routes API

```python
# mvc/api_routes.py

from mvc.controllers import api_status_controller

def register_api_routes(router):
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
- **Ne pas afficher le token dans les logs**, le module `api_auth` ne le logue jamais.
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
