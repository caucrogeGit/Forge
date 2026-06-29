# Les helpers de réponse dans Forge

Ce document explique les fonctions raccourcies du module `core.http.helpers`, qui construisent les réponses HTTP les plus fréquentes : gabarit HTML, JSON, enveloppe d'API.

## 1. Rôle

`core.http.helpers` fournit des raccourcis pour construire une `Response` dans les cas courants.

Construire une `Response` à la main est répétitif pour les cas fréquents : rendre un gabarit, renvoyer du JSON, répondre une API.
Ces helpers raccourcissent ces cas tout en restant explicites : chacun retourne un objet `Response` prêt à être renvoyé par le contrôleur.

Le helper `html(...)` ajoute une garde utile : son deuxième argument positionnel est le statut HTTP, pas le contexte.
Passer un dictionnaire en deuxième position lève une `TypeError` claire, au lieu d'une erreur différée et obscure.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Module | `core.http.helpers` |
| Couche | HTTP |
| Rôle | construire les réponses HTTP courantes |
| Objet produit | `Response` |
| API publique | `html`, `json_response`, `api_success`, `api_error` |
| Exception liée | `TypeError` si le 2e argument de `html()` n'est pas un entier ; `ValueError` si les données JSON ne sont pas sérialisables |
| Dépend de | `core.templating` (rendu des gabarits), `core.forge` (lecture de `app_env` et `views_dir`) |

## 3. Schémas UML

### 3.1 Diagramme de classe

Le diagramme montre les quatre helpers et l'objet `Response` qu'ils produisent tous.

```mermaid
classDiagram
    direction LR

    class helpers {
        <<module>>
        +html(template, status, context, raw) Response
        +json_response(data, status) Response
        +api_success(data, status, meta) Response
        +api_error(message, status, code, details) Response
    }

    class Response {
        +int status
        +bytes body
        +str content_type
    }

    helpers --> Response : construit et retourne
    api_success ..> json_response : délègue
    api_error ..> json_response : délègue
```

À retenir :

- les quatre helpers retournent tous un `Response` ;
- `api_success` et `api_error` délèguent à `json_response` ;
- `html(...)` rend un gabarit, `json_response(...)` sérialise des données brutes.

## 4. API publique

| Élément | Signature | Rôle |
|---|---|---|
| `html` | `html(template: str, status: int = 200, context: dict[str, Any] | None = None, *, raw: bool = False) -> Response` | rend un gabarit en `Response` HTML |
| `json_response` | `json_response(data: Any, status: int = 200) -> Response` | renvoie `data` sérialisé en JSON |
| `api_success` | `api_success(data: Any = None, status: int = 200, meta: dict[str, Any] | None = None) -> Response` | enveloppe d'API de succès |
| `api_error` | `api_error(message: str, status: int = 400, code: str = "error", details: Any = None) -> Response` | enveloppe d'API d'erreur |

Forme des enveloppes d'API :

| Helper | Corps JSON produit |
|---|---|
| `api_success` | `{"success": true, "data": ..., "meta": ...}` (`meta` ajouté si fourni) |
| `api_error` | `{"success": false, "error": {"code": ..., "message": ..., "details": ...}}` (`details` ajouté si fourni) |

`api_success` et `api_error` produisent une enveloppe JSON cohérente.
Les clients d'API trouvent ainsi toujours la même forme : un drapeau `success`, des données ou un bloc d'erreur structuré.

## 5. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Rendre une vue HTML | `html(template, context=...)` |
| Renvoyer du JSON brut | `json_response(...)` |
| Répondre une API structurée (succès) | `api_success(...)` |
| Répondre une API structurée (erreur) | `api_error(...)` |

## 6. Exemples d'utilisation

```python
from core.http.helpers import html, json_response, api_success, api_error


def page(request):
    return html("article/index.html", context={"articles": rows})


def feed(request):
    return json_response({"items": rows})


def api(request):
    return api_success(data=rows, meta={"total": len(rows)})


def api_invalid(request):
    return api_error("Champ manquant", status=422, code="validation")
```

!!! warning "Le 2e argument de html() est le statut"
    `html(template, {...})` ne passe pas un contexte : le deuxième argument positionnel est le statut HTTP.

    Passez toujours le contexte par mot-clé : `html(template, context={...})`.
    Le helper lève une `TypeError` explicite si le deuxième argument n'est pas un entier.

!!! warning "Données JSON sérialisables"
    `json_response(...)` lève `ValueError` si les données ne sont pas sérialisables en JSON.

    Convertissez vos objets (dates, décimaux) avant de les passer.

## Voir aussi

- [L'objet Response dans Forge](response.md) : ce que ces helpers construisent.
- [L'objet Request dans Forge](request.md) : l'entrée de l'échange HTTP.
