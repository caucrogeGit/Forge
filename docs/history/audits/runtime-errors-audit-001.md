# Audit DX-RUNTIME-ERRORS-AUDIT-001 — Erreurs runtime et mode debug

## Objectif

Auditer la gestion actuelle des erreurs runtime dans Forge et répondre à la question :

> Que se passe-t-il aujourd'hui quand une application Forge plante pendant son exécution ?

Ce document ne décrit aucune implémentation future. Il photographie l'état actuel et identifie les risques.

---

## Résumé exécutif

Forge capture toutes les exceptions runtime via deux niveaux de `try/except` dans `app.py` et `core/application.py`. Le visiteur reçoit une page HTML statique (500 ou 404) sans aucun détail technique. Le développeur voit un traceback Python dans la console.

Il n'existe pas de mode debug HTTP (pas de `APP_DEBUG`), pas de logging persistant, et aucune distinction dans la réponse HTTP entre `APP_ENV=dev` et `APP_ENV=prod`. L'état est acceptable pour une version 1.x mais insuffisant pour une utilisation sérieuse en développement : le développeur doit lire le terminal pour diagnostiquer une erreur.

Le risque le plus concret est le scénario de double-échec : si `errors/500.html` lui-même ne peut pas être rendu, la connexion est fermée brutalement par Python sans réponse HTTP.

---

## Chemin actuel d'une erreur runtime

```
Navigateur → RequestHandler.do_GET / do_POST / etc.
  └─ try/except Exception [niveau 1 — app.py]
       └─ self._dispatch(request)
            └─ _app.dispatch(request)
                 └─ try/except Exception [niveau 2 — application.py]
                      ├─ router.match()        — peut retourner None
                      ├─ csrf.check()          — peut retourner Response(403)
                      ├─ middleware.check()    — peut retourner Response(302/403)
                      └─ route.handler(request) — le contrôleur applicatif
```

### Niveau 2 — `core/application.py` `dispatch()`

```python
except Exception:
    logger.exception("Erreur non gérée — %s %s", request.method, request.path)
    return _html("errors/500.html", 500)
```

- Capture toutes les exceptions non gérées du contrôleur.
- Logue le traceback complet sur `stderr` (console).
- Retourne le rendu Jinja2 de `mvc/views/errors/500.html`.

### Niveau 1 — `app.py` `do_GET()`

```python
except Exception:
    logger.exception("Erreur GET %s", self.path)
    self._send_response(_html("errors/500.html", 500))
```

- Ne voit que les exceptions qui échappent au niveau 2.
- Cas typique : `_html("errors/500.html", 500)` a lui-même échoué dans le niveau 2.
- Tente à nouveau de rendre `errors/500.html` → **risque de double-échec**.

### `_handle_dynamic_request` (POST/PUT/PATCH/DELETE)

```python
except RequestEntityTooLarge:
    self._send_response(_html("errors/413.html", 413))
except Exception:
    logger.exception("Erreur %s %s", label, self.path)
    self._send_response(_html("errors/500.html", 500))
```

- `RequestEntityTooLarge` est le seul type d'exception distingué à ce niveau.
- Toutes les autres exceptions → 500.

---

## Comportement en mode développement

`APP_ENV=dev` (défaut) :

| Élément | Comportement |
|---|---|
| Niveau de log | `logging.DEBUG` |
| Format log | `[DEBUG-DEV] message` (sans timestamp) |
| Traceback console | Oui — via `logger.exception()` |
| Traceback dans la réponse HTTP | **Non** — page HTML statique |
| Cache fichiers statiques | `max-age=3600` (1 h) |
| SSL par défaut | Activé si `APP_SSL_ENABLED` non défini |
| Logs fichier | **Aucun** |

Le développeur doit lire le terminal pour voir le traceback. Il n'y a pas de page debug dans le navigateur.

---

## Comportement en mode production

`APP_ENV=prod` :

| Élément | Comportement |
|---|---|
| Niveau de log | `logging.INFO` |
| Format log | `2026-01-01 12:00:00 [INFO-PROD] message` (avec timestamp) |
| Traceback console | Oui — via `logger.exception()` (mais niveau INFO peut filtrer) |
| Traceback dans la réponse HTTP | **Non** |
| Cache fichiers statiques | `max-age=604800, immutable` (7 jours) |
| SSL par défaut | Désactivé (`APP_SSL_ENABLED=false`) |
| Logs fichier | **Aucun** |

Remarque : `logger.exception()` logue au niveau ERROR, qui passe même en INFO. Le traceback arrive donc bien en production dans la console ou le gestionnaire système (`journald`, `supervisor`, etc.).

---

## Erreurs contrôleur

### Exception non rattrapée dans le contrôleur

```python
def index(request):
    raise RuntimeError("boom")
```

→ Capturée par `Application.dispatch()` → log + `errors/500.html` (status 500).  
→ Aucun détail technique dans la réponse.

### Contrôleur retournant un type incorrect

```python
def index(request):
    return "chaîne de caractères"  # pas un objet Response
```

→ `Application.dispatch()` retourne la chaîne à `RequestHandler._send_response()`.  
→ `_send_response()` tente `response.status`, `response.body` → `AttributeError`.  
→ Capturée par `RequestHandler.do_GET()` (niveau 1) → log + `errors/500.html`.

### Route pointant vers un callable inexistant

Si `route.handler` est `None` ou un non-callable, `route.handler(request)` → `TypeError`.  
→ Capturée par `Application.dispatch()` → 500.

### Méthode de contrôleur absente

Si le routeur pointe vers `controller.methode_absente`, Python lève `AttributeError` lors du dispatch.  
→ Capturée par `Application.dispatch()` → 500.

---

## Erreurs routes

### Route inconnue (404)

```python
result = self._router.match(request.method, request.path)
if result is None:
    return _html("errors/404.html", 404)
```

→ Géré explicitement avant le `try/except` général. Retourne 404 proprement.

### Route définie mais méthode HTTP incorrecte

Par exemple : route GET `/clients`, requête POST `/clients`.  
→ `router.match("POST", "/clients")` retourne `None` → 404.  
→ Aucun 405 Method Not Allowed n'est émis.

### Erreur à l'import de `mvc/routes.py`

```python
_routes = importlib.import_module(APP_ROUTES_MODULE)
```

Si `mvc/routes.py` contient une erreur de syntaxe ou une `ImportError`, le serveur ne démarre pas. L'erreur est levée avant la création de `_app`. Pas de comportement HTTP — échec au démarrage.

---

## Erreurs templates

### Template introuvable

```python
# core/http/helpers.py
template_manager.render(template, context or {})
```

→ `Jinja2Renderer.render()` appelle `self._env.get_template(template)`.  
→ `jinja2.TemplateNotFound` est levée si le fichier est absent.  
→ Propagée jusqu'à `Application.dispatch()` → capturée → log + `errors/500.html`.

### Template avec erreur de syntaxe Jinja2

→ `jinja2.TemplateSyntaxError` lors du chargement → même chemin → 500.

### Variable de contexte absente

`jinja2.UndefinedError` lors du rendu (si `undefined` n'est pas `Undefined` silencieux).  
→ Même chemin → 500.

### Layout manquant (`layouts/base.html` absent)

Si un template étend un layout inexistant → `jinja2.TemplateNotFound`.  
→ Même chemin → 500.

### Renderer non enregistré

```python
# core/templating/manager.py
if self._renderer is None:
    raise RuntimeError("Aucun renderer enregistré...")
```

→ Levée si `template_manager.register()` n'a jamais été appelé.  
→ Capturée par `Application.dispatch()` → tente de rendre `errors/500.html` → même `RuntimeError` → **double-échec** → connexion fermée.

---

## Erreurs SQL

### Requête échouée

```python
# core/database/db.py
except Exception:
    if owns_connection and connection is not None:
        connection.rollback()
    raise
```

→ `_run_query()` fait un rollback puis **re-lève** l'exception.  
→ Propagée jusqu'au contrôleur, puis à `Application.dispatch()` → 500.  
→ Aucune page d'erreur SQL spécifique.

### Pool épuisé ou connexion impossible

```python
# core/database/connection.py
except _mariadb.PoolError as error:
    logger.exception("Pool épuisé ou connexion impossible : %s", error)
    raise
```

→ Logué + re-levé → propagé → 500.

### Base de données inaccessible au démarrage

La connexion est **lazy** : le pool n'est créé qu'au premier appel SQL.  
→ Le serveur démarre sans MariaDB. La première requête SQL échoue et retourne 500.

### Table ou colonne manquante

`mariadb.ProgrammingError` ou `mariadb.OperationalError` → re-levée → 500.

### Fichier SQL manquant (`sql_loader.py`)

```python
# core/database/sql_loader.py — charge un module .py de requêtes SQL
importlib.import_module(...)
```

→ `ModuleNotFoundError` si le fichier SQL Python est absent → propagé → 500.

---

## Erreurs HTTP 404 / 500

### 404

- Retourné par `Application.dispatch()` quand `router.match()` retourne `None`.
- Rendu via `_html("errors/404.html", 404)` (Jinja2).
- Page statique : titre "Page non trouvée", lien vers `/`.
- Aucun contexte de requête dans la page.

### 500

- Retourné par `Application.dispatch()` pour toute exception non gérée.
- Rendu via `_html("errors/500.html", 500)` (Jinja2).
- Page statique : titre "Erreur interne du serveur", lien vers `/`.
- Aucun détail technique dans la page — conforme aux bonnes pratiques de sécurité.
- Traceback complet dans la console via `logger.exception()`.

### Codes présents mais non mappés automatiquement

| Code | Page disponible | Déclenché automatiquement |
|------|----------------|--------------------------|
| 400  | `errors/400.html` | Non — retourné manuellement par les contrôleurs |
| 403  | `errors/403.html` | Oui — CsrfMiddleware / AuthMiddleware |
| 404  | `errors/404.html` | Oui — route inconnue |
| 413  | `errors/413.html` | Oui — `RequestEntityTooLarge` |
| 422  | `errors/422.html` | Non — retourné manuellement |
| 429  | `errors/429.html` | Non — retourné manuellement (rate limit) |
| 500  | `errors/500.html` | Oui — exception non gérée |

### Method Not Allowed (405)

Aucun 405 n'est émis. Une méthode HTTP incorrecte sur une route existante retourne 404.

---

## Logs existants

### Instances de logging dans Forge

| Fichier | Logger | Usage |
|---|---|---|
| `app.py` | `__name__` (`app`) | Démarrage serveur, erreurs GET/POST, requêtes reçues |
| `core/application.py` | `__name__` (`core.application`) | Erreur dispatch non gérée |
| `core/database/connection.py` | `__name__` (`core.database.connection`) | Initialisation pool, pool épuisé |

### Configuration

```python
logging.basicConfig(
    level  = logging.DEBUG if APP_ENV == "dev" else logging.INFO,
    format = "[%(levelname)s-DEV] %(message)s"        # dev
           | "%(asctime)s [%(levelname)s-PROD] %(message)s"  # prod
)
```

Configuré uniquement dans le bloc `if __name__ == "__main__"` de `app.py`.  
En tests ou import direct, aucune configuration n'est effectuée (logging Python par défaut).

### Sortie

- **Console uniquement** (stderr/stdout selon le handler Python par défaut).
- **Aucun fichier** dans `storage/logs/` ou ailleurs.
- **Aucun format structuré** (JSON, JSONL).
- **Aucun identifiant de corrélation** entre la réponse HTTP et l'entrée de log.

---

## Risques identifiés

### RISQUE-1 — Double-échec du rendu de la page d'erreur

**Scénario** : `errors/500.html` est absent, corrompu ou Jinja2 n'est pas initialisé.  
**Conséquence** : `Application.dispatch()` tente `_html("errors/500.html", 500)` → exception → capturée par `RequestHandler.do_GET()` → tente à nouveau `_html("errors/500.html", 500)` → deuxième exception → connexion fermée brutalement, sans réponse HTTP valide.  
**Fréquence** : théorique en fonctionnement normal, mais peut survenir lors du développement (mauvais `VIEWS_DIR`, renderer non configuré).

### RISQUE-2 — Aucune distinction dev/prod dans les réponses HTTP

Le développeur et le visiteur voient la même page 500 opaque. En développement, le traceback n'est visible que dans le terminal. Cela ralentit le diagnostic.

### RISQUE-3 — Pas de logs persistants

Toutes les erreurs runtime disparaissent à l'arrêt du serveur. Il est impossible de diagnostiquer un plantage a posteriori sans accès au terminal de la session.

### RISQUE-4 — Pas d'identifiant de corrélation

Impossible de relier une erreur vue par l'utilisateur (timestamp, URL) à une entrée de log précise quand plusieurs erreurs surviennent simultanément (serveur multi-thread).

### RISQUE-5 — Rendu Jinja2 requis pour les pages d'erreur

Toutes les pages d'erreur (404, 500, etc.) passent par `template_manager.render()` (Jinja2). Si le renderer n'est pas enregistré ou si `VIEWS_DIR` est incorrect, même les pages d'erreur échouent.

### RISQUE-6 — Absence de 405 Method Not Allowed

Une requête avec une mauvaise méthode HTTP retourne 404 au lieu de 405, ce qui peut induire le client ou les outils de monitoring en erreur.

### RISQUE-7 — Erreurs SQL silencieuses pour l'utilisateur

Toute erreur SQL remonte en 500 sans aucune indication sur la cause (connexion impossible, contrainte violée, table manquante). En développement, le diagnostic nécessite de lire le terminal.

---

## Ce qui est acceptable aujourd'hui

- **Aucun traceback dans les réponses HTTP** — le code actuel est correct de ce point de vue. La page 500 ne révèle jamais de détails techniques au visiteur.
- **Headers de sécurité** — X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security, etc. sont émis systématiquement, y compris sur les pages d'erreur.
- **Capture systématique des exceptions** — aucune exception ne passe à travers les deux niveaux catch sans déclencher un 500. Le serveur ne plante pas.
- **Logging sur `logger.exception()`** — le traceback complet est disponible dans la console. Suffisant pour un serveur de développement mono-utilisateur.

---

## Ce qui doit être corrigé plus tard

| Priorité | Problème | Ticket proposé |
|---|---|---|
| P1 | Pas de logs persistants : erreurs perdues à l'arrêt | `DX-RUNTIME-ERRORS-JSONL-001` |
| P1 | Aucune distinction dev/prod dans la réponse (pas de page debug) | `DX-RUNTIME-ERRORS-SCHEMA-001` |
| P2 | Double-échec si errors/500.html manque (connexion fermée sans réponse) | `DX-RUNTIME-ERRORS-SCHEMA-001` |
| P2 | Pas de corrélation entre réponse utilisateur et entrée de log | `DX-RUNTIME-ERRORS-JSONL-001` |
| P3 | Absence de 405 Method Not Allowed | À qualifier en DX ou SECURITY |
| P3 | Erreurs SQL non distinguées (tout devient 500) | `DX-RUNTIME-ERRORS-SCHEMA-001` |
| P4 | Pas de rendu Markdown lisible des erreurs | `DX-RUNTIME-ERRORS-MD-001` |

---

## Recommandation de trajectoire

La trajectoire naturelle est la suivante :

```text
DX-RUNTIME-ERRORS-AUDIT-001   (ce document — audit)
    ↓
DX-RUNTIME-ERRORS-SCHEMA-001  (définir le schéma d'un événement d'erreur runtime)
    ↓
DX-RUNTIME-ERRORS-JSONL-001   (collecteur → storage/logs/errors.dev.jsonl)
    ↓
DX-RUNTIME-ERRORS-MD-001      (rendu lisible errors.dev.md en développement)
```

**Règles à respecter :**

- JSONL = source canonique des erreurs runtime.
- Markdown = rendu secondaire lisible par le développeur.
- Forge Design (futur) = vue graphique des erreurs.
- La réponse HTTP reste toujours une page HTML statique sans détail technique.
- Le comportement en production ne change pas (log console / pas de fichier par défaut).
- `APP_ENV=dev` active le collecteur JSONL et la page debug enrichie.
- `APP_ENV=prod` garde le comportement actuel (console uniquement, 500 statique).

**Ce que ce schéma ne doit pas faire :**

- Exposer un traceback dans la réponse HTTP en production.
- Ajouter une dépendance externe (pas de Sentry, pas de Datadog).
- Modifier le comportement des pages d'erreur existantes.
- Alourdir le cœur du framework.

---

## Tickets suivants proposés

| Ticket | Objectif |
|---|---|
| `DX-RUNTIME-ERRORS-SCHEMA-001` | Définir le schéma d'un événement d'erreur (type, url, method, message, traceback, timestamp, env) |
| `DX-RUNTIME-ERRORS-JSONL-001` | Collecteur d'erreurs → `storage/logs/errors.dev.jsonl` en mode dev |
| `DX-RUNTIME-ERRORS-MD-001` | Rendu `errors.dev.md` lisible par le développeur |

**Prochaine priorité immédiate : `DX-RUNTIME-ERRORS-SCHEMA-001`.**
