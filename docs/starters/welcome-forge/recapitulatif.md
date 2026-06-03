# Aide-mémoire de la progression

Récapitulatif des **11 paliers** de la progression pédagogique et des
API Forge introduites à chaque étape. À garder sous la main avant
d'aborder le premier CRUD complet (`first-crud`).

## Les 11 paliers

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge](debutant/welcome.md) | Premier contrôleur, une route, réponse texte | `Response.text(...)` |
| 2 | [Paramètres d'URL](debutant/query-params.md) | Lire la query string | `request.param("name", default=...)` |
| 3 | [Première vue HTML](debutant/first-html-view.md) | Rendre un template | `BaseController.render(...)` |
| 4 | [Route dynamique](debutant/dynamic-route.md) | Segment variable d'URL | `request.route_param("id")` |
| 5 | [Inspecter une requête](debutant/request-debug.md) | Explorer la requête en dev | `request.data`, `Response.debug(...)` |
| 6 | [Réponse JSON](debutant/json-response.md) | Données structurées (API) | `Response.json({...})` |
| 7 | [Le jeton CSRF](debutant/csrf.md) | Protéger les formulaires | `BaseController.csrf_token(request)` |
| 8 | [Premier formulaire POST](debutant/form-post.md) | Traiter un POST | `request.form("name", default=...)` |
| 9 | [Validation serveur](debutant/server-validation.md) | Refuser une valeur invalide | `Response.text(..., status=422)` |
| 10 | [Première base SQL](debutant/first-sql.md) | Lire en base, SQL visible | `core.database.db.fetch_one(...)` |
| 11 | [Écrire en base](debutant/first-sql-write.md) | Insérer une ligne | `core.database.db.insert(...)` |

## Réponses (`core.http.response.Response`)

| Méthode | Usage |
|---------|-------|
| `Response.text(body, status=200)` | Réponse `text/plain` |
| `Response.html(body)` | Réponse HTML brute |
| `Response.json(obj)` | Réponse `application/json` |
| `Response.debug(obj)` | Page de debug (dev uniquement, `404` en prod) |
| `BaseController.render(template, request=..., context=...)` | Rendu d'un template Jinja2 |

## Lecture de la requête (`core.http.request.Request`)

| Accès | Source |
|-------|--------|
| `request.param("k", default=...)` | Query string (`?k=...`) |
| `request.route_param("k")` | Segment de route (`/x/{k}`) |
| `request.form("k", default=...)` | Corps d'un formulaire POST |
| `request.data` | Vue globale (méthode, chemin, headers, body…) |

## Base de données (`core.database.db`)

| Fonction | Usage |
|----------|-------|
| `fetch_one(sql, params)` | Première ligne (`dict`) ou `None` |
| `fetch_all(sql, params)` | Liste de lignes |
| `insert(sql, params)` | Insertion (paramétrée) |
| `execute(sql, params)` | Écriture générique |

Les requêtes restent **paramétrées** (placeholders `?`) — jamais de
concaténation de valeurs. **Forge garde le SQL visible.**

## Sécurité

- **CSRF** : champ caché `csrf_token` exigé sur chaque POST, vérifié
  automatiquement par le middleware (palier 7).
- **Validation serveur** : ne jamais faire confiance au client ; valider
  avant d'utiliser ou d'écrire (palier 9).

## Et ensuite

Une fois ces 11 paliers acquis, enchaînez les **starters autonomes** par
ordre de complexité : d'abord le [First CRUD](../crud/first-crud.md)
(CRUD complet à SQL visible, entité neutre), puis les exemples métier
depuis la [vue d'ensemble](../index.md) :
First CRUD (généré) → Utilisateurs/Auth → …
