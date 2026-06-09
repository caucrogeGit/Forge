# L'objet Request dans Forge

Ce document explique ce qu'est une **requête** HTTP, comment Forge la représente avec l'objet `Request`, ce qu'il contient et comment on le lit dans un contrôleur.

## 1. Qu'est-ce qu'une requête ?

Quand un visiteur ouvre une page ou envoie un formulaire, son navigateur envoie une **requête** au serveur.
Cette requête transporte tout ce que le serveur a besoin de savoir pour répondre :

- une **méthode** (`GET` pour consulter, `POST` pour envoyer des données…) ;
- un **chemin** (l'URL demandée, par exemple `/welcome/hello`) ;
- des **en-têtes** (informations techniques : type de contenu, cookies…) ;
- parfois un **corps** (les champs d'un formulaire, un document JSON…).

Le serveur lit la requête, puis renvoie une réponse.

## 2. La requête dans Forge

Dans Forge, chaque action de contrôleur reçoit un objet `Request` qui représente la requête en cours :

```python
def hello(request: Request) -> Response:
    name = request.query("name", default="Forge")
    return Response.text(f"Bonjour {name}")
```

Vous ne **créez** jamais cet objet vous-même : Forge le construit pour vous et vous le passe.
Votre rôle est seulement de **le lire** pour produire la réponse.

## 3. Ce qu'il contient

L'objet `Request` rassemble les informations de la requête :

| Attribut | Type | Contenu |
|---|---|---|
| `method` | `str` | la méthode effective (`GET`, `POST`…), après surcharge éventuelle |
| `original_method` | `str` | la méthode réellement reçue, avant toute surcharge |
| `path` | `str` | le chemin demandé, par exemple `/welcome/hello` |
| `params` | `dict` | les paramètres de la query string (`?clé=valeur`) |
| `route_params` | `dict` | les segments dynamiques de la route (`/article/{id}`) |
| `headers` | en-têtes | les en-têtes HTTP (recherche insensible à la casse) |
| `body` | `dict` | les champs d'un formulaire envoyé en POST |
| `json_body` | `dict` | le corps décodé quand la requête est en JSON |
| `files` | `dict` | les fichiers téléversés (objets `UploadedFile`) |
| `ip` | `str` | l'adresse du client |

## 4. Lire la requête : les accesseurs

Plutôt que de fouiller ces attributs à la main, on lit la requête avec des méthodes **nommées d'après leur source** : on sait ainsi d'où vient la donnée.

| Accesseur | Lit dans | Exemple |
|---|---|---|
| `request.query(clé, default)` | la query string (`?clé=…`) | `request.query("name")` |
| `request.route(clé, default)` | les segments de route (`/{id}`) | `request.route("id")` |
| `request.form(clé, default)` | les champs d'un formulaire POST | `request.form("email")` |
| `request.json(clé, default)` | un corps JSON | `request.json("title")` |
| `request.header(nom, default)` | les en-têtes HTTP | `request.header("Accept")` |
| `request.file(clé, default)` | les fichiers téléversés | `request.file("avatar")` |

Chacun renvoie `default` si la donnée est absente : pas d'exception, pas de `None` à gérer si vous fournissez une valeur de repli.

## 5. Inspecter la requête en développement

La propriété `request.data` renvoie une **vue lisible et sûre** de la requête, pratique pour le debug.
Les valeurs sensibles (`Authorization`, `Cookie`, `password`, `csrf`…) y sont masquées, et le contenu des fichiers n'est jamais inclus (seulement leurs métadonnées).

```python
def debug(request: Request) -> Response:
    return Response.debug(request)
```

## 6. Contextes d'utilisation

- **Lire une valeur d'URL** : `request.query(...)` (recherche, pagination…).
- **Lire un segment de route** : `request.route("id")` (`/article/{id}`).
- **Traiter un formulaire** : `request.form(...)` après un POST.
- **Recevoir du JSON** : `request.json(...)` pour une API.
- **Téléversement** : `request.file(...)`.
- **Inspecter** : `request.data` ou `Response.debug(request)` en développement.

## 7. Voir aussi

- [L'objet Response dans Forge](response.md) : l'autre moitié de l'échange HTTP.
- [La session HTTP dans Forge](session.md) : la mémoire entre deux requêtes.
- [Convention d'inspection HTTP](../http.md) : le masquage des valeurs sensibles.
