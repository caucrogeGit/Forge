# Schéma JSONL des erreurs runtime Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## Objectif

Définir le format canonique des événements d'erreur runtime Forge en mode développement.

Ce document décrit le schéma v1.0 utilisé pour structurer chaque erreur avant son écriture dans `storage/logs/errors.dev.jsonl`.

---

## Source canonique

```text
storage/logs/errors.dev.jsonl
```

Ce fichier JSONL est la **source unique de vérité** des erreurs runtime de développement.

- Il est écrit par le collecteur d'erreurs (`core/errors/runtime_error_logger.py`).
- Il est actif uniquement en `APP_ENV=dev`.
- Le rendu Markdown (`errors.dev.md`) est régénéré automatiquement après chaque écriture.
- La future vue Forge Design lira ce fichier directement.
- Il n'est jamais la source de réponse HTTP.
  La page `errors/500.html` reste statique en production.
  En `APP_ENV=dev`, le dispatcher lui passe en plus un contexte `error` (type, message, trace) construit par `build_dev_error_context()`, et le template affiche la cause si le bloc `{% if error %}` est présent.
  Aucune trace n'est exposée en production (`build_dev_error_context()` retourne `None` hors dev).

---

## Format JSONL

Chaque erreur est **une ligne JSON valide** :

- une ligne = un événement ;
- pas de tableau global ni de virgule entre les lignes ;
- encodage UTF-8 ;
- aucun retour à la ligne à l'intérieur d'une ligne ;
- append simple : chaque nouvelle erreur est ajoutée à la fin.

Exemple de fichier `errors.dev.jsonl` :

```jsonl
{"schema_version":"1.0","id":"err_20260509_094200_8f3a","timestamp":"2026-05-09T07:42:00+00:00","environment":"dev","level":"ERROR","category":"controller","exception_type":"TypeError","message":"index() missing 1 required positional argument: 'request'","safe_for_display":false}
{"schema_version":"1.0","id":"err_20260509_094502_2c1d","timestamp":"2026-05-09T07:45:02+00:00","environment":"dev","level":"ERROR","category":"template","exception_type":"TemplateNotFound","message":"dashboard.html","safe_for_display":false}
```

---

## Champs obligatoires

Tous les événements doivent contenir ces champs :

| Champ | Type | Rôle |
|---|---|---|
| `schema_version` | `string` | Version du schéma (`"1.0"`) |
| `id` | `string` | Identifiant unique, format `err_YYYYMMDD_HHMMSS_xxxx` |
| `timestamp` | `string` | Date ISO 8601 avec fuseau (`datetime.now(timezone.utc).isoformat()`) |
| `environment` | `string` | Environnement courant (`"dev"` ou `"prod"`) |
| `level` | `string` | Niveau d'erreur, voir section Niveaux |
| `category` | `string` | Catégorie fonctionnelle, voir section Catégories |
| `exception_type` | `string` | Nom du type d'exception Python (`"RuntimeError"`, `"TemplateNotFound"`, …) |
| `message` | `string` | Message court de l'erreur |
| `safe_for_display` | `boolean` | `true` si le message peut être montré au visiteur, `false` par défaut |

---

## Champs optionnels

Ces champs sont recommandés quand l'information est disponible :

| Champ | Type | Rôle |
|---|---|---|
| `request` | `object` | Informations de requête filtrées, voir [Objet request](#objet-request) |
| `location` | `object` | Dernier frame de la pile (`file`, `line`, `function`) |
| `traceback` | `array` | Pile d'appels simplifiée, liste de frames |
| `hint` | `string` | Piste de correction pour le développeur |
| `route` | `string` | Nom ou chemin de route si disponible |
| `controller` | `string` | Contrôleur concerné si identifiable |
| `template` | `string` | Nom du template concerné si identifiable |
| `sql` | `string` | Requête SQL anonymisée si applicable (jamais de valeurs) |
| `correlation_id` | `string` | Identifiant de corrélation futur |

---

## Objet `request`

L'objet `request` ne doit jamais contenir de valeurs sensibles :

```json
{
  "method": "POST",
  "path": "/login",
  "query": "",
  "post_keys": ["email", "password"],
  "headers": ["Host", "User-Agent", "Content-Type"]
}
```

**Règles :**

- `post_keys` : liste des **noms** des champs POST, jamais les valeurs.
- `headers` : liste des **noms** des headers, jamais les valeurs.
- Les valeurs de champs comme `password`, `token`, `cookie`, `authorization` ne sont **jamais** incluses.

---

## Objet `traceback`

```json
[
  {"file": "app.py", "line": 186, "function": "do_GET"},
  {"file": "core/app/application.py", "line": 54, "function": "dispatch"},
  {"file": "mvc/controllers/user_controller.py", "line": 42, "function": "index"}
]
```

Chaque frame contient : `file` (chemin relatif au projet), `line`, `function`.

---

## Catégories

| Catégorie | Usage |
|---|---|
| `runtime` | Exception générique non rattrapée dans un contrôleur |
| `controller` | Erreur dans un contrôleur identifié |
| `routing` | Route inconnue, méthode incorrecte, callback invalide |
| `template` | Template introuvable, erreur de syntaxe Jinja2, variable absente |
| `database` | Requête SQL échouée, pool épuisé, connexion impossible |
| `configuration` | Mauvais `VIEWS_DIR`, renderer non enregistré, config manquante |
| `http` | Erreur de parsing de requête, taille dépassée |
| `unknown` | Exception non classifiable |

---

## Niveaux

| Niveau | Usage |
|---|---|
| `ERROR` | Erreur non gérée interceptée par le dispatcher, utilisé par défaut |
| `WARNING` | Comportement anormal mais non bloquant |
| `INFO` | Événement informatif (ex : démarrage, rechargement) |
| `CRITICAL` | Erreur fatale empêchant le serveur de fonctionner |

Les erreurs runtime collectées en production sont majoritairement `ERROR`.

---

## Règles de sécurité

### Ce qui ne doit jamais être enregistré en clair

- Mots de passe (`password`, `passwd`, `pwd`, `secret`)
- Tokens (`token`, `access_token`, `refresh_token`, `api_key`, `apikey`)
- Sessions complètes et cookies
- Headers `Authorization`, `Cookie`, `Set-Cookie`
- Clés API et clés privées
- Contenu complet des formulaires POST (seuls les **noms** des champs)
- Secrets des fichiers `.env`

### safe_for_display

Le champ `safe_for_display: false` (valeur par défaut) signifie que le `message` **ne peut pas** être affiché au visiteur.
Il peut contenir des informations techniques internes.

Un message est `safe_for_display: true` uniquement s'il a été explicitement composé pour l'affichage (ex : message de validation métier).

---

## Exemple minimal

```json
{
  "schema_version": "1.0",
  "id": "err_20260509_094200_8f3a",
  "timestamp": "2026-05-09T07:42:00+00:00",
  "environment": "dev",
  "level": "ERROR",
  "category": "runtime",
  "exception_type": "RuntimeError",
  "message": "Division par zéro",
  "safe_for_display": false
}
```

---

## Exemple complet

```json
{
  "schema_version": "1.0",
  "id": "err_20260509_094200_8f3a",
  "timestamp": "2026-05-09T07:42:00+00:00",
  "environment": "dev",
  "level": "ERROR",
  "category": "controller",
  "exception_type": "TypeError",
  "message": "UserController.index() missing 1 required positional argument: 'request'",
  "safe_for_display": false,
  "request": {
    "method": "GET",
    "path": "/users",
    "query": "page=1",
    "post_keys": [],
    "headers": ["Host", "User-Agent", "Accept"]
  },
  "location": {
    "file": "mvc/controllers/user_controller.py",
    "line": 42,
    "function": "index"
  },
  "traceback": [
    {"file": "app.py", "line": 186, "function": "do_GET"},
    {"file": "core/app/application.py", "line": 54, "function": "dispatch"},
    {"file": "mvc/controllers/user_controller.py", "line": 42, "function": "index"}
  ],
  "hint": "Vérifier la signature de la méthode du contrôleur."
}
```

---

## Module Python

Le module `core/errors/runtime_errors.py` fournit les outils pour construire et sérialiser les événements :

```python
from core.errors.runtime_errors import (
    build_error_event,
    build_error_event_from_exc,
    serialize_event,
    validate_event,
    safe_request_info,
    CATEGORIES,
    LEVELS,
    REQUIRED_FIELDS,
)

# Depuis une exception active (dans un except)
try:
    raise RuntimeError("boom")
except RuntimeError as exc:
    event = build_error_event_from_exc(exc, environment="dev")
    line  = serialize_event(event)   # une seule ligne JSON
    validate_event(event)            # vérifie les champs obligatoires
```

---

## Collecteur : core/errors/runtime_error_logger.py

Le collecteur est dans `core/errors/runtime_error_logger.py`.
Il est branché sur `core/app/application.py`.

**Comportement en `APP_ENV=dev` :**

Chaque erreur non gérée capturée par `Application.dispatch()` est enregistrée dans `storage/logs/errors.dev.jsonl`, puis `errors.dev.md` est régénéré immédiatement.

- Le dossier `storage/logs/` est créé automatiquement s'il n'existe pas.
- La catégorie est détectée automatiquement selon le type d'exception (template, database, configuration, runtime).
- L'objet `request` est filtré : seuls les noms des champs POST sont conservés, jamais les valeurs.
- Si l'écriture échoue, un warning est logué en console et l'application continue.
- Si la génération du Markdown échoue, elle est silencieuse et n'affecte pas le JSONL.

**Comportement en `APP_ENV=prod` :** aucune écriture.

```python
from core.errors.runtime_error_logger import log_runtime_error

# Appelé automatiquement depuis Application.dispatch()
# Peut aussi être appelé manuellement depuis un except
try:
    raise RuntimeError("boom")
except RuntimeError as exc:
    log_runtime_error(exc, request=None)  # request facultatif
```

---

## Rendu Markdown : core/errors/runtime_error_markdown.py

Le rendu Markdown est dans `core/errors/runtime_error_markdown.py`.
Il est déclenché automatiquement après chaque écriture JSONL.

```text
storage/logs/errors.dev.jsonl  →  storage/logs/errors.dev.md
(source canonique)                 (rendu lisible, ne pas modifier)
```

- `errors.dev.md` contient un résumé (nombre d'erreurs, horodatage de la dernière), puis une section par erreur.
- Les lignes JSONL invalides sont signalées avec un avertissement `⚠`.
- Le fichier MD n'est pas créé si le JSONL est absent ou vide.

---

## Ce qui n'est pas encore implémenté

- Page debug enrichie dans le navigateur.
- Filtrage automatique des messages contenant des données sensibles.
- Rotation des fichiers JSONL.
- Logs en mode prod (`errors.prod.jsonl`).
- Vue Forge Design (projet compagnon futur).

---

## Tickets livrés

| Ticket | Objectif |
|---|---|
| `DX-RUNTIME-ERRORS-SCHEMA-001` | Schéma canonique JSONL v1.0 |
| `DX-RUNTIME-ERRORS-JSONL-001` | Collecteur d'erreurs → `storage/logs/errors.dev.jsonl` |
| `DX-RUNTIME-ERRORS-MD-001` | Rendu lisible `errors.dev.md` régénéré après chaque erreur |
