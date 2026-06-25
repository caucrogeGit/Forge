# Convention d'inspection, classes HTTP publiques

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Ticket fondateur : **API-INSPECTABLE-OBJECTS-CONVENTION-001**.

Cette page décrit le contrat que Forge applique aux classes API publiques
manipulées par le développeur : `Request`, `Response`, et, par
extension, les objets que les tickets suivants amèneront dans le périmètre
(`UploadedFile`, `Form`, `Session`, `RouteEntry`).

L'objectif est qu'un développeur qui découvre Forge puisse explorer un objet
sans connaître ses attributs internes ni recourir à `vars()` ou
`obj.__dict__`. La convention reste **explicite et pédagogique** : pas de
magie, pas de dump brut, pas de fuite de secrets.

---

## 1. Contrat

Une classe API publique inspectable expose :

1. **Une vue globale `.data`**, un `dict` lisible, stable, masquant les
   champs sensibles (mots de passe, jetons, en-têtes d'authentification,
   cookies). C'est une **représentation publique**, pas un dump brut.
2. **Des accesseurs ciblés et nommés**, `obj.field(key, default=None)`.
   La forme retournée est scalaire (ou objet métier), pas un conteneur
   intermédiaire (`list[str]` pour `parse_qs`, `HTTPMessage` pour les
   headers…).
3. **Des annotations utiles à l'autocomplétion**, `str | None`,
   `UploadedFile | None`, etc., pour que les IDE remontent une signature
   claire au survol.
4. **Un `__repr__` sûr**, ligne courte, pas de dump des attributs
   internes, pas de fuite de header sensible.
5. **Aucun dump naïf**, `.data` n'est jamais un `self.__dict__`. Les
   valeurs binaires (corps de réponse, contenu de fichiers uploadés) ne
   figurent jamais dans `.data`, uniquement leurs métadonnées.

---

## 2. Champs sensibles, règles de masquage

Les valeurs marquées sensibles sont remplacées par la chaîne littérale
`"[masked]"` dans `.data`. Le contrôle est volontairement large :

### Headers (égalité exacte, casse insensible)

```
authorization, proxy-authorization, cookie, set-cookie,
x-api-key, x-auth-token, x-csrf-token
```

### Champs formulaire / JSON (sous-chaîne, casse insensible)

```
password, passwd, secret, token, csrf, api_key, apikey
```

Sous-chaîne signifie que `password_confirmation`, `csrf_token`,
`_csrf`, `api_key_v2`, `bearer_token` sont également masqués.

### Cookies de réponse

`response.cookies` retourne uniquement les **noms** des cookies posés via
`Set-Cookie`, jamais leurs valeurs (qui contiennent typiquement le token
de session).

---

## 3. `Request`, référence

```python
request.method          # str — "GET", "POST", …
request.original_method # str — méthode reçue avant override _method
request.path            # str
request.ip              # str
request.headers         # http.client.HTTPMessage (case-insensitive)
request.params          # dict[str, list[str]]    — query string parsée
request.body            # dict[str, list[str]]    — formulaire parsé
request.json_body       # dict | list | ...       — JSON parsé
request.files           # dict[str, UploadedFile]
request.route_params    # dict[str, str]
```

### Accesseurs

| API | Lit | Retourne |
|---|---|---|
| `request.query(key, default=None)` | `params` | `str` ou `default` |
| `request.header(name, default=None)` | `headers` | `str` ou `default` (insensible à la casse) |
| `request.form(key, default=None)` | `body` | `str` ou `default` |
| `request.json(key, default=None)` | `json_body` | valeur JSON ou `default` |
| `request.file(key, default=None)` | `files` | `UploadedFile` ou `default` |
| `request.route(key, default=None)` | `route_params` | `str` ou `default` |

### Exemple

```python
from core.http.request import Request
from core.http.response import Response


def search(request: Request) -> Response:
    page = request.query("page", default="1")
    accept = request.header("Accept", default="text/html")
    return Response.text(f"page={page} accept={accept}")


def create_user(request: Request) -> Response:
    email = request.form("email")
    name = request.json("name")  # body JSON
    return Response.json({"created": email or name})
```

Les contrôleurs générés par Forge (`forge new`, `forge make:crud`,
`forge make:public-page`, `forge make:public-list`, `forge make:public-form`,
`forge make:public-contact`) importent `Request` et `Response` et annotent
chaque action publique avec `request: Request` et `-> Response`. C'est
suffisant pour que Pylance/VS Code fournisse l'autocomplétion sur
`request.` (query, form, json, file, route, header, data) sans
import manuel.

### `Response.text` vs `BaseController.render`, quand utiliser quoi

`Response.text(...)` retourne du texte brut. `BaseController.render(...)`
rend une **vue template** existante située dans `mvc/views/`. Confondre
les deux est la source d'erreur la plus fréquente pour un débutant :

```python
# Texte brut — pas de moteur de template, aucune vue requise.
return Response.text("Bonjour Forge")

# Vue template — Forge cherche mvc/views/welcome/index.html.
return BaseController.render("welcome/index.html", request=request)

# Inspection d'un objet en développement.
return Response.debug(request)
```

Si un contrôleur appelle `BaseController.render("bonjour", ...)` et que
`mvc/views/bonjour` n'existe pas, Forge renvoie en `APP_ENV=dev` un
message d'erreur explicite (text/plain, statut 500) qui rappelle le rôle
de `render()` et propose `Response.text(...)` / `Response.debug(...)`.
En `APP_ENV=prod`, le message reste minimal, pas de fuite du chemin
demandé ni du dossier `views/` (voir DX-RENDER-ERROR-001).

### `request.data`

```python
{
  "method": "POST",
  "original_method": "POST",
  "path": "/contacts",
  "ip": "127.0.0.1",
  "params": {"page": ["2"]},
  "route_params": {"id": "42"},
  "headers": {
    "User-Agent": "curl/8.0",
    "Authorization": "[masked]"
  },
  "body": {"email": ["a@b.c"], "password": "[masked]"},
  "json_body": {"name": "Forge", "csrf_token": "[masked]"},
  "files": {
    "avatar": {"filename": "x.png", "size": 12345, "content_type": "image/png"}
  }
}
```

Le contenu binaire des fichiers uploadés n'est jamais inclus, seuls
`filename`, `size` et `content_type`.

---

## 4. `Response`, référence

```python
response.status        # int
response.content_type  # str
response.body          # bytes
response.headers       # dict[str, str]
response.cookies       # list[str] — noms uniquement
response.data          # dict — vue publique masquée
```

### Constructeurs nommés

| API | Content-Type produit |
|---|---|
| `Response.text(body, status=200, headers=None)` | `text/plain; charset=utf-8` |
| `Response.html(body, status=200, headers=None)` | `text/html; charset=utf-8` |
| `Response.json(data, status=200, headers=None)` | `application/json; charset=utf-8` |
| `Response.debug(obj, status=200)` | `text/html` en `dev`, refus 404 en `prod` |

`Response.json(data)` lève `ValueError` si `data` n'est pas sérialisable.

### `Response.debug(obj)`

En `APP_ENV=dev` (DX-DEBUG-DUMP-HTML-001) :

- retourne une page HTML pédagogique (`text/html; charset=utf-8`) titrée
  « Debug Forge » ;
- normalisation : si `obj.data` est un `dict`/`list`/`tuple`/`set`,
  l'attribut est déballé ; sinon les conteneurs natifs (`dict`, `list`,
  `tuple`, `set`) sont rendus récursivement ; les autres objets affichent
  `type(obj).__name__` suivi de `repr(obj)` ;
- masquage automatique des clés sensibles (`Authorization`,
  `Proxy-Authorization`, `Cookie`, `Set-Cookie`, `password`, `passwd`,
  `secret`, `token`, `csrf`, `api_key`, `apikey`, …), mêmes règles que
  `request.data` ;
- échappement HTML systématique des chaînes (les valeurs `<script>…`
  s'affichent comme texte, jamais comme balises) ;
- profondeur bornée par `MAX_DEPTH` (5), au-delà, le marqueur
  `<max depth reached>` est affiché ;
- références circulaires détectées (`<cycle detected>`), aucun risque
  de récursion infinie.

Le renderer est exposé via `core.http.debug_dumper.render_debug_html(obj)`
pour les tests et les outils de diagnostic, `Response.debug` reste la
seule API publique destinée aux contrôleurs.

En `APP_ENV=prod` : refuse, retourne `Response.text("Response.debug() est
désactivé en production.", status=404)`. Le payload n'est jamais inclus,
même tronqué, pas d'option pour contourner cette protection.

### Exemple

```python
from core.http.response import Response


def health(request):
    return Response.text("ok")


def api_user(request):
    return Response.json({"id": 1, "name": "Forge"})


def debug_request(request):
    return Response.debug(request)  # dev : dump masqué ; prod : 404
```

---

## 5. Audit du périmètre

Forge expose aujourd'hui plusieurs classes publiques utilisables par les
contrôleurs. Le ticket fondateur ne refactore pas tout en bloc, il
documente l'état et planifie l'extension.

| Classe | Statut convention | Notes |
|---|---|---|
| `core.http.request.Request` | **conforme** | accesseurs + `.data` ; voir §3. |
| `core.http.response.Response` | **conforme** | constructeurs + `.data` + `.cookies` ; voir §4. |
| `core.http.request.UploadedFile` | partiel | déjà un `dataclass(frozen=True)` lisible (`filename`, `size`, `content_type`) ; pas encore de `.data`. Ticket suivant. |
| `core.http.router.RouteEntry` | partiel | `method_label`, `pattern`, `name`, `public`, `csrf`, `api` exposés ; pas encore de `.data`. Ticket suivant. |
| `core.forms.form.Form` | hors-périmètre | API plus large (validation, erreurs, binding), audit dédié. |
| `core.sessions.SessionStore` | hors-périmètre | contrat protocole ; pas une classe pédagogique de premier ordre. |

Les classes marquées « partiel » ou « hors-périmètre » seront traitées par
des tickets `API-INSPECTABLE-<CLASS>-001` si le besoin est confirmé sur le
terrain. La règle reste celle de la charte : **tester avant d'élargir**.

---

## 6. Règles internes au framework

- Ne jamais inclure le corps brut d'une réponse ni le contenu binaire d'un
  upload dans `.data`. Préférer toujours une représentation par
  métadonnées.
- Ne jamais persister `.data` en base ni dans un log structuré : c'est une
  vue **debug**, pas une trace d'audit. Pour l'audit auth, voir ADR-008.
- Ne pas ajouter à `.data` un champ qui n'a pas d'utilité pédagogique
  claire : le but est l'introspection, pas la complétude.
- Les masquages sont en mémoire seulement, la requête réelle reçue par
  l'application reste intacte (`request.headers["Authorization"]` continue
  de fonctionner pour le contrôleur).

---

## 7. Compatibilité

- L'API existante (`request.params`, `request.body`, `request.json_body`,
  `request.files`, `request.route_params`, `request.headers`,
  `request.method`, `request.path`, `request.ip`) reste inchangée.
- Aucun appel `Response(status=…, body=…, …)` n'est cassé. Les
  constructeurs nommés (`Response.text`, `.html`, `.json`, `.debug`) sont
  additifs.
- `core.http.helpers.html` et `core.http.helpers.json_response`
  cohabitent avec `Response.html` / `Response.json` ; ils gardent leur
  rôle (rendu Jinja2, conventions API JSON).

---

## 8. Voir aussi

- [API Forge complète](api.md)
- [API JSON légère](api-json.md)
- [Sessions](sessions.md)
- [ADR-008, Audit Auth (architecture du logging)](../adr/008-auth-audit-architecture.md)
