# Vider le cache

Objectif : recharger les catalogues après les avoir modifiés.

**Ce que vous allez apprendre :** pour la performance, les catalogues sont mis en **cache** après leur première lecture.
Si vous éditez un fichier JSON pendant que l'application tourne, le changement n'apparaît qu'après `clear_translation_cache()`.

!!! note "Module opt-in"
    Le cache évite de relire le disque à chaque `trans`.
    En contrepartie, une modification à chaud nécessite de vider le cache.

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `clear_translation_cache()` | Vide le cache des catalogues. | Opt-ins |

## Le contrôleur

```python
# mvc/controllers/i18n_cache_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import clear_translation_cache, trans


class I18nCacheController(BaseController):

    @staticmethod
    def recharger(request: Request) -> Response:
        # Après avoir édité translations/fr.json sur le disque :
        clear_translation_cache()
        return Response.json({
            "rechargé": True,
            "title": trans("welcome.title", locale="fr"),
        })
```

### Comprendre ce code

- Sans `clear_translation_cache()`, `trans` continue de servir la version **déjà lue** du catalogue, même si le fichier a changé.
- Après l'appel, la prochaine lecture relit `translations/fr.json` à jour.
- En production, on vide rarement le cache : les catalogues changent au déploiement, pas en cours de requête.

## La route

```python
# mvc/routes.py
from mvc.controllers.i18n_cache_controller import I18nCacheController

with router.group("", public=True) as public:
    public.add("POST", "/i18n-cache/reload", I18nCacheController.recharger, name="i18n_cache_reload")
```

## À retenir

- Les catalogues sont **mis en cache** dès la première lecture.
- `clear_translation_cache()` force le rechargement après édition à chaud.
- En production, le cache se vide au déploiement.

## Après ce starter

Dernière étape : que faire d'un catalogue **absent ou invalide** ?

[Gérer les erreurs de catalogue](i18n-errors.md)
