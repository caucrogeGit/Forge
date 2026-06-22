# Le routeur dans Forge

Ce document décrit le routeur HTTP : déclarer des routes et les regrouper.

Le fichier de code correspondant est `core/http/router.py`.

## 1. À quoi sert ce module ?

Le routeur associe une méthode et un chemin à un gestionnaire (l'action d'un contrôleur).
Il permet aussi de **regrouper** des routes partageant des réglages (préfixe, accès public, CSRF, API).

## 2. Déclarer des routes

```python
from core.http.router import Router

router = Router()

with router.group("", public=True) as public:
    public.add("GET",  "/article", ArticleController.index, name="article-index")
    public.add("POST", "/article/store", ArticleController.store, name="article-store")
```

## 3. Les objets

| Objet | Rôle |
|---|---|
| `Router` | le routeur : enregistre les routes et ouvre des groupes |
| `RouteGroup` | un groupe de routes partageant `prefix`, `public`, `csrf`, `api` |
| `RouteEntry` | une route déclarée (méthode(s), motif, gestionnaire, nom, indicateurs) |

`RouteEntry(method, pattern, handler, *, name=None, public=False, csrf=True, api=False)` :

- `public` : route accessible sans authentification ;
- `csrf` : protection CSRF exigée (par défaut `True`) ;
- `api` : route d'API (réponses JSON, pas de redirection login) ;
- `name` : nom stable de la route (convention `contrôleur-méthode`, ADR-029).

## 4. Les groupes

`router.group(prefix, *, public=False, csrf=True, api=False)` ouvre un `RouteGroup` : toutes les routes ajoutées dedans héritent de ses réglages.
C'est le moyen idiomatique de séparer un groupe public d'un groupe protégé.

## 5. Contextes d'utilisation

- **`mvc/routes.py`** : déclarer les routes de l'application par groupes.
- **Opt-in** : `register_<module>_routes(router)` ajoute ses routes au routeur.

## 6. Voir aussi

- [L'objet Request](request.md) : la requête routée.
- [Les helpers de réponse](helpers.md) : produire la réponse d'un gestionnaire.
