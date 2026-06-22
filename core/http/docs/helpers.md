# Les helpers de réponse dans Forge

Ce document décrit les fonctions raccourcies pour construire une réponse HTTP courante.

Le fichier de code correspondant est `core/http/helpers.py`.

## 1. À quoi sert ce module ?

Construire une `Response` à la main est répétitif pour les cas fréquents : rendre un gabarit, renvoyer du JSON, répondre une API.
Ces helpers raccourcissent ces cas tout en restant explicites.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `html(template, status=200, context=None, *, raw=False)` | rend un gabarit en `Response` HTML |
| `json_response(data, status=200)` | renvoie `data` sérialisé en JSON |
| `api_success(data=None, status=200, meta=None)` | réponse d'API normalisée de succès |
| `api_error(message, status=400, code="error", details=None)` | réponse d'API normalisée d'erreur |

## 3. Exemples

```python
from core.http.helpers import html, json_response, api_success, api_error

def page(request):
    return html("article/index.html", context={"articles": rows})

def feed(request):
    return json_response({"items": rows})

def api(request):
    return api_success(data=rows, meta={"total": len(rows)})
    # ou, en cas d'erreur :
    return api_error("Champ manquant", status=422, code="validation")
```

## 4. Le contrat des réponses d'API

`api_success` et `api_error` produisent une enveloppe JSON cohérente (succès/erreur, code, métadonnées), pour que les clients d'API trouvent toujours la même forme.

## 5. Contextes d'utilisation

- **Vue HTML** : `html(template, context=...)`.
- **Endpoint JSON simple** : `json_response(...)`.
- **API structurée** : `api_success` / `api_error`.

## 6. Voir aussi

- [L'objet Response](response.md) : ce que ces helpers construisent.
- [L'objet Request](request.md) : l'entrée de l'échange.
