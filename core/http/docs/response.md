# L'objet Response dans Forge

Ce document explique ce qu'est une **réponse** HTTP, comment Forge la représente avec l'objet `Response`, ce qu'il contient et comment on le crée dans un contrôleur.

## 1. Qu'est-ce qu'une réponse ?

Après avoir lu la requête, le serveur renvoie une **réponse** au navigateur.
Elle transporte :

- un **code de statut** (`200` tout va bien, `404` introuvable, `403` refusé…) ;
- des **en-têtes** (type de contenu, cookies à poser…) ;
- un **corps** (le HTML de la page, du texte, du JSON…).

Le navigateur lit la réponse et l'affiche.

## 2. La réponse dans Forge

Dans Forge, une action de contrôleur doit **retourner** un objet `Response` :

```python
def hello(request: Request) -> Response:
    return Response.text("Bonjour Forge")
```

On ne construit presque jamais une `Response` à la main : on passe par un **constructeur nommé** (ci-dessous) qui choisit le bon type de contenu pour vous.

## 3. Ce qu'il contient

| Attribut | Type | Contenu |
|---|---|---|
| `status` | `int` | le code de statut HTTP (défaut `200`) |
| `content_type` | `str` | le type du contenu, par exemple `text/html; charset=utf-8` |
| `body` | `bytes` | le corps de la réponse (encodé en UTF-8 si vous passez du texte) |
| `headers` | `dict` | les en-têtes additionnels, dont `Set-Cookie` |
| `stream` | itérable ou `None` | corps envoyé par morceaux (fichiers volumineux) ; `None` pour les réponses ordinaires |
| `content_length` | `int` ou `None` | taille en octets quand le corps est envoyé en flux |

Deux propriétés de lecture, utiles surtout pour l'inspection :

| Propriété | Type | Contenu |
|---|---|---|
| `cookies` | `list` | les **noms** des cookies posés (jamais leurs valeurs) |
| `data` | `dict` | une vue lisible et sûre de la réponse (valeurs sensibles masquées, sans le corps brut) |

## 4. Créer une réponse : les constructeurs

| Constructeur | Produit |
|---|---|
| `Response.text(corps)` | du texte brut (`text/plain`) |
| `Response.html(corps)` | du HTML (`text/html`) |
| `Response.json(données)` | du JSON (`application/json`) ; lève une erreur si les données ne sont pas sérialisables |
| `Response.debug(objet)` | une page de debug lisible en développement, refusée en production |
| `Response.file(chemin)` | un fichier servi en flux (avec support des téléchargements partiels) |

Pour rendre un **gabarit** (un fichier de vue), on n'utilise pas un constructeur de `Response` mais `BaseController.render(...)`, qui renvoie lui aussi un objet `Response` rempli avec le HTML produit.

## 5. Contextes d'utilisation

- **Répondre du texte** : `Response.text(...)` (réponses simples, débogage).
- **Rendre une page** : `BaseController.render("vue.html", ...)`.
- **Répondre du JSON** : `Response.json(...)` pour une API.
- **Servir un fichier** : `Response.file(...)`.
- **Poser un cookie** : on écrit dans `response.headers["Set-Cookie"]`, par
  exemple via le cookie de session (voir [La session HTTP](../reference/http/session.md)).
- **Inspecter** : `response.data` montre une vue masquée et sûre de la réponse.

## 6. Voir aussi

- [L'objet Request dans Forge](request.md) : l'autre moitié de l'échange HTTP.
- [La session HTTP dans Forge](../reference/http/session.md) : poser et retrouver la session via
  un cookie de la réponse.
- [Convention d'inspection HTTP](../reference/http.md) : le masquage des valeurs sensibles.
