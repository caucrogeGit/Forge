# Le jeton Bearer dans Forge

Ce document explique la primitive d'authentification par jeton Bearer de Forge, le module `core.http.bearer`, et comment protéger une route d'API avec.

## 1. Rôle

`core.http.bearer` répond à une seule question : cette requête présente-t-elle le bon jeton d'API ?

Un client d'API ne porte pas de session ni de cookie.
Il s'annonce par un en-tête `Authorization: Bearer <jeton>`, et le serveur compare ce jeton à celui qu'il attend.

Le module est une **primitive partagée**, et c'est sa raison d'être.
Trois opt-ins exposent des routes protégeables par jeton, `forge-mvc-iot`, `forge-mvc-video` et `forge-mvc-audio`, et chacun en avait d'abord écrit sa copie.
Le ticket `CORE-HTTP-BEARER-PRIMITIVE-001` les a rassemblés ici, au motif qu'un correctif de sécurité appliqué à une seule copie laisse les autres vulnérables (principe 7).

L'ADR-088 en a fait la **seule** implémentation du dépôt, en retirant `core.security.api_auth` qui faisait la même chose autrement, et moins bien.

La comparaison passe par `secrets.compare_digest`, donc en temps constant.
Une comparaison ordinaire s'arrête au premier caractère différent, et la durée de la réponse renseigne alors sur le préfixe correct du jeton, ce qui permet de le reconstituer caractère par caractère.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Module | `core.http.bearer` |
| Couche | HTTP |
| Rôle | extraire et vérifier un jeton Bearer, en temps constant |
| Constante liée | `BEARER_PREFIX` (`"Bearer "`) |
| API publique | `extract_bearer_token`, `is_bearer_authorized` |
| Décision liée | ADR-088 (contrat unique des réponses d'API JSON) |
| Employé par | `forge-mvc-iot`, `forge-mvc-video`, `forge-mvc-audio` |

## 3. API publique

| Élément | Signature | Rôle |
|---|---|---|
| `extract_bearer_token` | `extract_bearer_token(request) -> str \| None` | rend le jeton de l'en-tête `Authorization`, ou `None` |
| `is_bearer_authorized` | `is_bearer_authorized(request, api_token: str \| None) -> bool` | la requête est-elle autorisée pour ce jeton attendu |
| `BEARER_PREFIX` | `"Bearer "` | le schéma exact reconnu, espace compris |

## 4. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Protéger une route d'API | `is_bearer_authorized(request, jeton_attendu)` |
| Lire le jeton présenté, sans le vérifier | `extract_bearer_token(request)` |
| Laisser une API ouverte en local | passer `None` comme jeton attendu |

## 5. Exemples d'utilisation

### 5.1 Protéger une route

```python
import os

from core.http import json_error, json_response
from core.http.bearer import is_bearer_authorized


def status(request):
    if not is_bearer_authorized(request, os.getenv("API_TOKEN") or None):
        return json_error("unauthorized", 401)
    return json_response({"status": "ok"})
```

Le refus rend un code unique et opaque.
Distinguer « en-tête absent », « schéma invalide » et « jeton invalide » renseignerait un attaquant sur l'étape qu'il a franchie, et lui indiquerait où porter son effort suivant.

### 5.2 Refuser une API ouverte en production

```python
def register_api_routes(router):
    if os.getenv("APP_ENV") == "prod" and not os.getenv("API_TOKEN"):
        raise RuntimeError("API ouverte interdite en production : définir API_TOKEN.")
    ...
```

!!! danger "Jeton attendu à `None` égale API ouverte"
    Quand `api_token` vaut `None`, `is_bearer_authorized` rend `True` sans rien vérifier.
    C'est le mode local et pédagogique, voulu pour qu'un parcours d'apprentissage n'exige pas de configurer un secret.

    En production, c'est une API ouverte que rien ne signale.
    Refusez de démarrer plutôt que de servir sans le savoir, comme le fait `forge-mvc-iot` dans `register_iot_routes`.

## 6. Limites

Le jeton est **statique**, lu par l'application depuis son environnement.
Il n'y a ni rotation automatique, ni jetons multiples, ni portées, ni expiration.

Forge ne fournit ni JWT, ni OAuth, ni jeton de rafraîchissement.
Ces sujets relèvent de l'application, ou d'un opt-in qui n'existe pas et que l'ADR-052 range hors trajectoire 1.x.

Un jeton Bearer transite en clair dans l'en-tête.
Il n'est protégé que par HTTPS, et ne doit jamais être employé sans lui.

## Voir aussi

- [API JSON légère](../reference/api-json.md), la page qui montre le tout assemblé.
- [Helpers de réponse](helpers.md), dont `json_error`, la fabrique unique des erreurs d'API.
- [Le routeur](router.md), et le drapeau `api` d'une route.
