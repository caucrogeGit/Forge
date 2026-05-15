# Audit complet — Forge MVC 2.0.0

> **Auditeur :** Claude (Sonnet 4.5 / Opus 4.7)
> **Date :** 9 mai 2026
> **Périmètre :** archive `Forge-main__3_.zip` — branche `main` au commit `435ffa9`
> **Méthode :** lecture statique du code, vérifications de sécurité ciblées, analyse architecturale, revue des tests et de la documentation

---

## 1. Synthèse exécutive

**Verdict global : 🟢 framework mature et solide, avec 4 points à corriger avant un usage en production.**

Forge 2.0.0 est un framework Python MVC sérieusement architecturé pour son périmètre déclaré (pédagogique + petites/moyennes applications web). La couverture de tests est exceptionnelle (ratio test/code ~2:1), les fondamentaux sécurité sont bien posés (CSRF auto, headers stricts, path traversal protégé, paramétrage SQL systématique, Argon2id disponible), et la séparation framework / application est correctement documentée et globalement respectée.

Les principaux problèmes relèvent de :

1. **Une dette architecturale réelle** : coexistence de deux piles d'authentification (`core/security/` legacy et `core/auth/` moderne) qui se chevauchent et créent un risque de bug latent.
2. **Un paramètre de hachage PBKDF2 sous-dimensionné** par rapport à la recommandation OWASP actuelle.
3. **Une incohérence entre starters et application par défaut** susceptible de produire des authentifications qui échouent silencieusement.
4. **Une génération de code CRUD potentiellement vulnérable à l'injection SQL** dans le mécanisme de filtres.

Aucun de ces points n'est rédhibitoire, et la correction de chacun est mécanique. La qualité globale du projet est largement au-dessus de la moyenne pour un framework "pédagogique".

**Recommandation principale :** corriger les 4 points 🔴 listés en section 12 avant de promouvoir Forge 2.0.0 comme prêt pour la production.

---

## 2. Méthode

- Extraction et cartographie de l'arborescence (713 fichiers, ~6.4 Mo).
- Lecture des fichiers structurels : `pyproject.toml`, `requirements*.txt`, `pytest.ini`, `.gitignore`, `.github/workflows/*`, `app.py`, `config.py`, `forge.py`, `README.md`, `CHANGELOG.md`.
- Lecture systématique de `core/` (modules clés : `application`, `http/router`, `http/request`, `security/*`, `auth/*`, `database/*`, `forms/*`, `uploads/*`, `templating/*`, `workflow/*`, `i18n/*`, `modules/*`, `mvc/controller/*`).
- Lecture comparée des starters générés (`forge_cli/starters/data/`).
- Recherches ciblées : injections SQL (f-strings, `%`, `format`), filtres `| safe` Jinja, secrets en dur, `TODO/FIXME`, doublons d'API.
- Analyse de la couverture de tests (179 fichiers, ~51 K LOC) et de la CI.

---

## 3. Vue d'ensemble du framework

### 3.1 Métriques

| Indicateur | Valeur |
|---|---|
| Fichiers Python totaux | ~190 (hors starter data) |
| LOC `core/` | 10 675 |
| LOC `forge_cli/` (hors starter data) | 12 375 |
| LOC `mvc/` (application par défaut) | 608 |
| LOC `cmd/` (legacy explicite) | 2 006 |
| LOC tests | 51 549 |
| Nombre de fichiers tests | 179 |
| Ratio LOC tests / LOC code (hors tests) | ~1.9 |
| Plus gros fichier `core/` | `core/auth/oidc.py` (1 011 lignes) |
| Versions Python testées en CI | 3.11, 3.12, 3.13, 3.14 |

### 3.2 Stack technique

- **Runtime :** Python 3.11+ (`http.server.ThreadingHTTPServer`, pas de framework asynchrone).
- **Templating :** Jinja2 (autoescape activé).
- **Base de données :** MariaDB 10.6+ via le connecteur officiel (`mariadb==1.1.14`), pool natif.
- **Auth :** Argon2id (`argon2-cffi`) + TOTP (`pyotp`), OIDC implémenté en interne.
- **Front :** Tailwind CSS (compilé), HTMX/Alpine optionnels.
- **Configuration :** `python-dotenv`, fichiers `env/*` non-commités.
- **CI :** GitHub Actions (tests + build + docs sur 4 versions de Python).

### 3.3 Philosophie déclarée

Le `README.md` énonce clairement la séparation `core/` (framework) vs `mvc/` (application). Cette doctrine est **réellement appliquée** dans la majorité du code, ce qui est rare et appréciable.

---

## 4. Architecture

### 4.1 Forces

- **Séparation MVC cohérente.** Le découpage `core/mvc/{controller,model,view}` côté framework et `mvc/{controllers,models,views,forms,validators,helpers}` côté application est lisible et respecté.
- **Dispatch central minimaliste.** `core/application.py` (54 lignes) est limpide : routage → CSRF → middlewares → handler. L'ordre des opérations est correct.
- **Routeur propre.** `core/http/router.py` supporte les paramètres dynamiques nommés, les groupes, les routes nommées (`url_for`), avec une compilation regex correcte. Pas de conflits de noms (vérifiés au moment de l'enregistrement).
- **Système de modules formellement défini** (`core/modules/`) avec manifeste, registre, découverte, injection de routes et de fichiers, tests dédiés (`test_module_*.py`).
- **Système de starters propre** (`forge_cli/starters/data/`) — démonstrateurs complets (Communes & Séjours, Carnet de contacts, Suivi pédagogique) générables via CLI.
- **Profils projet** (`minimal`, `standard`, `dynamic`, `multilingual`) permettant de calibrer le squelette généré.

### 4.2 Tensions architecturales

#### 🔴 4.2.1 Double pile d'authentification

C'est **le point structurel le plus important** de cet audit.

Deux modules coexistent et se chevauchent :

| Aspect | `core/security/` (legacy) | `core/auth/` (moderne) |
|---|---|---|
| Hachage mot de passe | PBKDF2-HMAC-SHA256 (`hacher_mot_de_passe`) | Argon2id (`hash_password`) |
| Session | Dict en mémoire (`creer_session`, `_sessions`) | Réutilise le même dict via fallback |
| API | Française (`est_authentifie`, `utilisateur_a_role`) | Anglaise (`is_authenticated`, `login_required`) |
| Décorateurs | `require_auth`, `require_role`, `require_csrf` | `login_required` |
| RBAC | `core/security/rbac.py` (223 lignes) | `core/auth/user_rbac.py` + `authorization.py` |
| Contrats | Aucun (dicts) | Dataclasses validées (`AuthUser`, `AuthMfaFactor`, etc.) |
| MFA / OIDC / audit | Absent | Présent et largement testé |

`core/auth/session.py` fait un fallback explicite vers `core/security/session.py` pour le stockage (lignes 132-139). Les deux modules ne sont donc **pas indépendants** : la pile moderne *repose* sur la legacy pour la persistance de session.

**Conséquences :**

- Le **`README.md` énonce une fausse information** dans son tableau « Ce que `core/` fournit » : il indique « `core/security/hashing.py` PBKDF2-HMAC-SHA256 » alors que la dépendance déclarée est `argon2-cffi>=25.1` et que la voie recommandée pour les nouveaux projets est Argon2id.
- L'`AuthController` par défaut (`mvc/controllers/auth_controller.py`) **mélange les deux APIs** : il importe `verifier_mot_de_passe` (PBKDF2) ET `is_mfa_enabled` (Argon2 stack). Il vérifie donc des hashes PBKDF2.
- Le starter `utilisateurs-auth/auth_controller.py` utilise quant à lui `verify_password` (Argon2). Les deux ne sont pas compatibles entre eux.

Cf. point 🔴 5.3 ci-dessous pour la conséquence concrète (incohérence entre `forge auth:user:create` et l'auth controller par défaut).

#### 🟠 4.2.2 Dossier `cmd/` legacy toujours livré

`cmd/README.md` déclare explicitement le dossier obsolète :

> *« Ils ne constituent pas l'interface officielle de Forge 1.1.0. […] Les scripts `python cmd/make.py …` sont conservés temporairement comme code historique. »*

Or :

- 2 006 LOC sont toujours livrées dans le wheel et le repo principal.
- `cmd/security/init_users.py` et `cmd/security/hash.py` utilisent encore PBKDF2 et peuvent être appelés par mégarde.
- Aucun warning de dépréciation n'est émis à l'exécution.

Soit ce code est utile (alors la mention « historique » dans le README est trompeuse), soit il ne l'est pas (alors il devrait être supprimé pour Forge 2.0.0).

#### 🟡 4.2.3 Quelques modules monolithiques

- `core/auth/oidc.py` : 1 011 lignes
- `core/auth/mfa.py` : 799 lignes
- `core/forms/fields.py` : 549 lignes
- `core/auth/__init__.py` : 427 lignes (essentiellement des re-exports — c'est lisible mais fastidieux à maintenir)

Pas critique, mais ces fichiers gagneraient à être éclatés (ex. : `oidc/` en sous-package avec `client.py`, `pkce.py`, `state.py`, `accounts.py`, `validation.py`).

### 4.3 Points neutres

- L'usage de `http.server.ThreadingHTTPServer` (pur stdlib) est cohérent avec la philosophie déclarée du framework. Cela limite la performance et exclut l'asynchrone, mais le `README` documente que la production passe par Nginx en reverse proxy. C'est un choix assumé.
- Les sessions en mémoire sont un choix assumé documenté (« Limites assumées en V1 : sessions perdues au redémarrage, pas de partage entre workers, pas de scaling horizontal »). Ce choix bloque toutefois toute mise en production multi-process derrière Nginx — voir 5.4.

---

## 5. Sécurité

### 5.1 Forces

- **CSRF automatique sur méthodes unsafe.** `core/application.py` vérifie `requires_csrf(method)` avant le dispatch. Token aléatoire par session (`secrets.token_hex(16)`), comparaison stricte, header `X-CSRF-Token` ou champ `csrf_token` accepté. Bonne implémentation.
- **Headers de sécurité par défaut sur toutes les réponses** (`app.py` lignes 184-194) :
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'`
- **Path traversal protégé.**
  - Statiques : `os.path.realpath` + `os.path.commonpath` (app.py ligne 142).
  - Médias uploadés : `core/uploads/storage.py::normalize_media_path` rejette `..`, `\x00`, schémas URI, séparateurs, chemins absolus, etc. Couverture exemplaire.
- **SQL paramétrisé partout dans le runtime applicatif.** Recherche exhaustive sur `cursor.execute(f"`, `cursor.execute(.* %`, `cursor.execute(.* + ` → 0 résultat dans `core/`, `mvc/models/`, et le code applicatif des starters.
- **Cookies sécurisés** : `HttpOnly; SameSite=Strict; Secure` dans tous les starters et le contrôleur d'auth principal.
- **Session fixation protégée** : rotation de `session_id` à l'authentification (`authentifier_session` ligne 54 de `core/security/session.py`).
- **Comparaisons de hash en temps constant** : `hmac.compare_digest` (PBKDF2), `secrets.compare_digest` (recovery codes).
- **Argon2id avec paramètres OWASP corrects** : `time_cost=2, memory_cost=19456 KiB (~19 Mo), parallelism=1` — conforme à la recommandation OWASP 2024 pour Argon2id.
- **Recovery codes MFA avec 80 bits d'entropie** (16 chars × log2(32)), alphabet sans caractères ambigus, hashés SHA-256 (justifié à cette entropie).
- **Audit log Auth/User** structuré (16 types d'événements définis), rate limiting modélisé.
- **Limites de taille de body** : `MAX_BODY_SIZE = 1 Mo`, exception `RequestEntityTooLarge` levée au-delà ; quota séparé pour les uploads multipart.
- **Validation d'uploads** : extension + MIME type whitelistés via configuration, taille max appliquée.
- **`autoescape` Jinja2 activé** sur les templates HTML par défaut. Les seuls usages de `| safe` sont sur des fragments HTML produits par d'autres templates Jinja eux-mêmes échappés (flash) ou par `html.escape()` explicite (form_errors). Pas de XSS détecté.

### 5.2 🔴 PBKDF2 sous-dimensionné

`core/security/hashing.py` ligne 17 :

```python
ITERATIONS = 260_000  # OWASP 2023 : minimum 210 000 pour PBKDF2-SHA256
```

**Le commentaire est inexact.** L'OWASP Password Storage Cheat Sheet (révision 2023 et 2024) recommande **600 000 itérations minimum** pour PBKDF2-HMAC-SHA256. La valeur 210 000 correspond à une recommandation antérieure datée. La valeur 260 000 actuelle est en-dessous du minimum recommandé.

**Sévérité :** modérée à élevée selon que ce code reste utilisé en production.

**Impact concret :** ce module est encore appelé par :

- `mvc/controllers/auth_controller.py` (l'auth controller par défaut du repo)
- `cmd/security/init_users.py`, `cmd/security/hash.py`
- `forge_cli/starters/data/suivi-comportement-eleves/files/scripts/create_auth_user.py`

Donc concrètement, tout projet créé avec le squelette par défaut hash en PBKDF2-260K.

**Correction recommandée (par ordre de préférence) :**

1. Migrer définitivement vers Argon2 partout (l'API existe déjà dans `core/auth/password.py`).
2. À défaut, monter `ITERATIONS` à **600 000** et mettre en place un re-hash transparent à la prochaine connexion (similaire à ce que fait `password_needs_rehash` dans le module Argon2).
3. Corriger le commentaire et la documentation README.

### 5.3 🔴 Incohérence de hachage entre CLI et auth controller par défaut

**Scénario reproduisible :**

1. Le développeur installe Forge et lance `forge auth:user:create --email a@b.fr` → `forge_cli/auth.py` ligne 481 importe `from core.auth.password import hash_password` → le mot de passe est haché en **Argon2**.
2. Le développeur lance ensuite l'application : `mvc/controllers/auth_controller.py` ligne 5 importe `from core.security.hashing import verifier_mot_de_passe` → la vérification utilise **PBKDF2**.
3. À la connexion : `verifier_mot_de_passe(password, hash_argon2)` essaie de parser `"<sel_hex>:<hash_hex>"` mais reçoit un hash Argon2 au format `$argon2id$...` → `ValueError` capturée → retourne `False`.
4. **L'utilisateur ne peut jamais se connecter, sans erreur explicite.**

**Sévérité :** élevée — bug fonctionnel silencieux affectant le workflow primaire d'un nouveau projet.

**Correction recommandée :** unifier sur Argon2 dans le contrôleur par défaut. Le starter `utilisateurs-auth` le fait déjà correctement (`from core.auth import verify_password`) — il faut aligner le `mvc/` par défaut sur cette approche.

### 5.4 🔴 Génération de code CRUD potentiellement vulnérable à l'injection SQL

`forge_cli/entities/make_crud.py` génère des fonctions de modèle avec ce pattern (lignes 717-727 et 752-757) :

```python
for col, val in (filters or {}).items():
    if val is not None and val != "":
        clauses.append(col + " = ?")            # ⚠️ col concaténé sans validation
        params.append(val)
if clauses:
    cursor.execute("SELECT COUNT(*) AS total FROM {table} WHERE "
                   + " AND ".join(clauses), params)
```

La **valeur** est paramétrisée (`?`), mais le **nom de la colonne** est concaténé directement. Si un contrôleur utilisateur passe `filters` en provenance du `request.body` ou des `request.params` sans whitelist, un attaquant peut injecter du SQL via la clé.

**Note :** le tri (`sort_col`) est correctement protégé par un `_ALLOWED_SORT` whitelist dans le code généré. Le même mécanisme manque pour les filtres.

**Sévérité :** modérée. La vulnérabilité dépend du code applicatif ; un contrôleur prudent peut éviter le problème, mais le framework devrait par défaut empêcher la classe entière de bugs.

**Correction recommandée :** générer également un `_ALLOWED_FILTERS = frozenset({...})` au moment de la génération CRUD, et valider chaque clé de `filters` contre ce set avant de la concaténer. Lever une exception explicite sinon.

### 5.5 🔴 Sessions in-memory bloquantes en production multi-process

`core/security/session.py` stocke les sessions dans un dict Python en mémoire de processus (`_sessions: dict = {}`). Le commentaire en haut du fichier le documente clairement :

> *« Limites assumées en V1 : sessions perdues au redémarrage, pas de partage entre workers, pas de scaling horizontal. »*

C'est un choix assumé pour la pédagogie. **Cependant**, le `README` recommande explicitement la mise en production derrière Nginx (« En production derrière Nginx, Forge écoute en HTTP local et Nginx termine TLS »). Or :

- Si Forge tourne en single-process derrière Nginx, c'est OK.
- Mais il n'y a aucune protection pour empêcher plusieurs workers (par ex. `gunicorn -w 4 app:server` adapté). Si quelqu'un lance plusieurs workers, **les sessions ne sont pas partagées** : chaque utilisateur voit son authentification disparaître selon le worker qui répond.

**Sévérité :** élevée pour une mise en production réelle, faible en dev.

**Correction recommandée :**

1. Documenter de façon **bien plus visible** dans le README et la doc déploiement que l'application doit tourner en single-process.
2. Idéalement, fournir un backend de session optionnel basé sur fichiers ou MariaDB (la table existe déjà dans la stack pour `auth_tokens`, c'est extensible).

### 5.6 🟠 Configuration TLS minimale dans `app.py`

```python
ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_ctx.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)
```

Aucun `set_ciphers`, aucun `minimum_version`. Python pose des défauts raisonnables (TLS 1.2+ depuis Python 3.10), mais une configuration explicite serait plus défensive :

```python
ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM")
```

**Sévérité :** mineure (le README précise que la production utilise Nginx pour TLS).

### 5.7 🟡 CSP sans nonce

La CSP par défaut est `script-src 'self'`. C'est strict, ce qui est bien, mais cela cassera dès que :

- Un script inline est utilisé (HTMX hyperscript, scripts Alpine, snippets de tracking, etc.).
- Le développeur veut configurer Stripe/Mapbox/Cloudflare Turnstile, etc.

Et le `CHANGELOG.md` mentionne déjà `forge js:init htmx` / `alpine` — donc la doctrine front pousse vers des patterns qui demanderont d'élargir la CSP.

**Recommandation :** prévoir un mécanisme de nonce CSP (générable depuis la session) et un helper Jinja `{{ csp_nonce() }}`. Sinon, documenter explicitement que les utilisateurs devront override le header.

---

## 6. Qualité du code

### 6.1 Forces

- **Style cohérent** : noms en français pour le code legacy, anglais pour le nouveau code Auth/User. Convention claire.
- **Docstrings systématiques** sur les modules et classes principales, en français.
- **Validation des contrats** par dataclasses immutables (`@dataclass(frozen=True)`) dans toute la pile `core/auth/` — bonne pratique défensive.
- **Pas d'imports circulaires apparents** dans les modules audités.
- **Effets de bord à l'import minimisés** : `core/forge.py` est un registre de configuration explicite, `config.py` ne fait pas de connexion réseau, le pool DB est lazy.
- **TODO/FIXME quasi inexistants dans le code de production** : 26 occurrences au total, dont la quasi-totalité dans `cmd/` (templates de génération obsolètes).
- **Pas de secrets en dur** : `env/example` ne contient que des squelettes vides ou des valeurs neutres. `.gitignore` exclut correctement `env/dev`, `env/prod`, `cert.pem`, `key.pem`.

### 6.2 🟠 Pas de typage statique systématique

- Les modules récents (`core/auth/*`) utilisent `from __future__ import annotations` et annotent leurs fonctions correctement.
- Les modules anciens (`core/security/session.py`, `core/security/hashing.py`, `core/database/db.py`, etc.) sont peu ou pas typés.
- Aucun outil de vérification de types statique configuré (pas de `mypy.ini`, pas de `pyrightconfig.json`).
- Aucun linter en CI (pas de `ruff`, `flake8`, `black`, `isort`).

**Recommandation :** ajouter `ruff` (rapide, peu intrusif) et `mypy --ignore-missing-imports` en mode permissif au CI, puis durcir progressivement.

### 6.3 🟠 Performance i18n sous-optimale

`core/i18n/translator.py::trans()` lit le catalogue JSON depuis le disque **à chaque appel** :

```python
def trans(key, locale=None, translations_dir="translations"):
    catalog = load_catalog(locale, translations_dir)  # ← lecture disque + json.loads
    value = catalog.get(key)
    ...
```

Sur un template Jinja qui appelle `trans("foo")` 50 fois, c'est 50 ouvertures de fichier + 50 parses JSON par requête. Pour un catalogue de quelques Ko ce n'est pas catastrophique mais c'est inutilement coûteux et facilement corrigeable.

**Recommandation :** ajouter un cache module-level (`@functools.lru_cache(maxsize=None)` sur `load_catalog`, avec invalidation explicite). Voire un cache TTL en dev pour permettre le reload des traductions sans redémarrage.

### 6.4 🟡 Doublons d'API non documentés

- Deux décorateurs `login_required` (dans `core/auth/session.py`) et `require_auth` (dans `core/security/decorators.py`) avec des comportements légèrement différents (`401` vs `302` par défaut, possibilité de redirect_to vs login_url constant).
- Deux mécanismes de RBAC : `core/security/rbac.py` (basé sur les rôles dans la session) et `core/auth/user_rbac.py` + `authorization.py` (contrats utilisateur structurés).

Aucune doc ne dit lequel choisir quand. Aligné avec le point 4.2.1.

### 6.5 🟡 Versioning de l'application dans `app.py`

```python
"""
app.py - Point d'entrée — Forge 1.2.0a1
"""
```

Le docstring de `app.py` mentionne « Forge 1.2.0a1 », alors que `pyproject.toml` déclare `version = "2.0.0"`. Détail cosmétique mais signal d'une mise à jour incomplète.

---

## 7. Tests

### 7.1 Forces

- **179 fichiers de tests, ~51 K LOC.** Ratio test/code applicatif ≈ 1.9:1, exceptionnel.
- **Couverture par domaine très large** :
  - Auth : 33 fichiers (login, MFA, OIDC, RBAC, recovery, reset, session, tokens, user, audit, rate limit…)
  - CRUD : `test_make_crud.py` (1559 lignes), `test_make_crud_media.py` (1118), `test_entity_list_filter.py` (650)…
  - Modules : 7 fichiers
  - Starters : `test_starter_communes_sejours.py` (1618 lignes), `test_starter_cli.py` (1260)
  - Workflow, i18n, uploads, templating, packaging, profiles, migrations…
- **CI matricielle** sur Python 3.11 → 3.14, avec build du package et `mkdocs build --strict`.
- **Audits de consolidation présents et structurés** (`docs/history/audits/consolidation-*.md`) — ce qui est très rare et témoigne d'une démarche qualité explicite.
- **Conftest propre** : isolation correcte des sessions et compteurs de rate-limit entre tests, fixtures session-scoped pour la config kernel.

### 7.2 🟡 Zones moins bien couvertes

- Pas de tests de **charge / concurrence**. La nature multi-thread du serveur (`ThreadingHTTPServer`) avec sessions en mémoire mériterait au moins un test de stress simple sur les sessions partagées.
- Pas de tests d'**intégration end-to-end HTTP réels** (lancement du serveur + requêtes via `requests`). Les tests passent par `FakeRequest`. C'est plus rapide et déterministe, mais ne couvre pas les bugs de niveau handler/SSL/headers.
- L'audit `docs/history/audits/consolidation-tests-001.md` mentionne lui-même que le « non-écrasement du code utilisateur est couvert de façon diffuse, sans fichier de test dédié ».

### 7.3 🟡 Tests probablement lents sur l'ensemble

51 K LOC de tests sur 179 fichiers en CI sur 4 versions Python = potentiellement plusieurs minutes de CI par push. Pas d'évidence de parallélisation (`pytest-xdist`). À envisager si le temps de CI devient un frein.

---

## 8. Performance

### 8.1 Points neutres

- Architecture single-process synchrone : choix assumé, plafonne le débit mais reste cohérent avec le périmètre cible (apps de petite/moyenne taille derrière Nginx).
- Pool MariaDB lazy avec taille configurable — bonne pratique.

### 8.2 🟠 Améliorations facilement réalisables

1. **Cache i18n** (cf. 6.3).
2. **Compilation des regex de routes au démarrage** : déjà fait (regex compilées dans `RouteEntry.__init__`).
3. **Cache des catalogues de traduction et des templates Jinja** : Jinja gère son cache par défaut, OK.
4. **Headers de cache statiques** : déjà bien gérés (`max-age=3600` en dev, `max-age=604800, immutable` en prod).
5. **Body parsing eager pour multipart** : `_parse_multipart` lit le body entier en mémoire avant parsing. Pour des uploads de plusieurs Mo c'est sous-optimal mais le cap `MAX_BODY_SIZE` limite l'impact.

### 8.3 🟡 Pas d'observabilité out-of-the-box

- Pas de métriques exposées (nb requêtes, latence, erreurs).
- Pas de format de log structuré configurable (JSON), uniquement texte.
- Le logging est simple : `logger.info(...)` + traceback sur erreur.

Pas critique pour le périmètre déclaré, mais à anticiper si le framework vise des déploiements production sérieux.

---

## 9. Documentation et conventions

### 9.1 Forces

- `README.md` : 26 KB, très détaillé. Couvre installation pipx, installation manuelle, doctrine framework/app, profils, CSS, prérequis.
- `CHANGELOG.md` : structuré (Ajouté / Modifié / Limites connues), historique préservé jusqu'à la 1.4.
- `CHARTE_DOC.md`, `CONTRIBUTING.md` : présents.
- `docs/` : MkDocs Material, structure thématique (audits, starters, modules, profiles, etc.).
- Audits internes (`docs/history/audits/`) : démarche qualité visible et tracée.

### 9.2 🟠 Incohérences documentaires

- **README dit PBKDF2, code utilise Argon2** (cf. 4.2.1).
- **README dit version 2.0.0, app.py dit 1.2.0a1**, autres fichiers à vérifier.
- Le `cmd/README.md` qualifie le dossier de « historique pour Forge 1.1.0 » alors qu'on est en 2.0.0.
- L'audit existant `docs/history/audits/consolidation-tests-001.md` mentionne « 168 fichiers de tests, 4824 tests passés » — désormais 179 fichiers. Pas grave mais à actualiser ou dater.

### 9.3 🟡 Pas de guide de contribution sécurité

Pas de `SECURITY.md` à la racine, pas de procédure de divulgation responsable. Pour un framework qui s'auto-positionne sur la sécurité (CSRF, headers, etc.), ce serait utile.

---

## 10. Conformité aux pratiques modernes

| Pratique | Statut |
|---|---|
| HTTPS / HSTS | ✅ |
| CSRF | ✅ |
| XSS protection (autoescape Jinja) | ✅ |
| SQL injection (paramétrisation) | ✅ |
| Path traversal | ✅ |
| Session fixation | ✅ |
| Argon2id pour mots de passe | ✅ (disponible) / ⚠️ (pas par défaut dans le squelette) |
| MFA (TOTP) | ✅ |
| Recovery codes | ✅ |
| Rate limiting | ✅ |
| Audit log | ✅ |
| OIDC | ✅ |
| RBAC | ✅ |
| CSP stricte | ✅ |
| Tests automatisés | ✅✅ |
| CI multi-version | ✅ |
| Type hints | 🟡 (partiel) |
| Linter | ❌ |
| Type checker statique | ❌ |
| SECURITY.md | ❌ |
| Dependency scanning automatique | ❌ |
| Sessions distribuées | ❌ |
| Observabilité (metrics) | ❌ |

---

## 11. Tableau récapitulatif des problèmes

| # | Problème | Sévérité | Catégorie | Effort |
|---|---|---|---|---|
| 1 | PBKDF2 à 260 K itérations (sous OWASP 600 K) | 🔴 | Sécurité | XS |
| 2 | Incohérence Argon2 (CLI) vs PBKDF2 (auth controller par défaut) | 🔴 | Sécurité / Architecture | S |
| 3 | Génération CRUD : clés de filtres concaténées sans whitelist | 🔴 | Sécurité | S |
| 4 | Sessions in-memory non documentées comme bloquant multi-process | 🔴 | Architecture / Doc | S (doc) — XL (impl backend alternatif) |
| 5 | Double pile auth `core/security` + `core/auth` non clarifiée | 🟠 | Architecture | L |
| 6 | Dossier `cmd/` legacy toujours livré sans deprecation warning | 🟠 | Architecture | S |
| 7 | i18n lit le catalogue JSON à chaque appel `trans()` | 🟠 | Performance | XS |
| 8 | Configuration TLS minimale dans `app.py` (pas de min_version explicite) | 🟠 | Sécurité défensive | XS |
| 9 | Pas de typage statique systématique, pas de `ruff`/`mypy` en CI | 🟠 | Qualité | M |
| 10 | README mentionne PBKDF2 alors que la stack est Argon2 | 🟠 | Doc | XS |
| 11 | Doublons d'API (`login_required` vs `require_auth`, deux RBAC) | 🟡 | Architecture / Doc | M |
| 12 | CSP sans mécanisme de nonce | 🟡 | Sécurité défensive | S |
| 13 | Modules monolithiques (`oidc.py` 1011 LOC, `mfa.py` 799 LOC) | 🟡 | Qualité | L |
| 14 | Pas de SECURITY.md ni procédure de divulgation | 🟡 | Doc | XS |
| 15 | `app.py` docstring mentionne « Forge 1.2.0a1 » | 🟡 | Doc / Cosmétique | XS |
| 16 | Pas de tests d'intégration HTTP end-to-end | 🟡 | Tests | M |
| 17 | Pas d'observabilité (metrics, logs structurés) | 🟡 | Ops | M |

**Légende sévérité :** 🔴 critique avant prod / 🟠 important / 🟡 mineur ou amélioration

**Légende effort :** XS (< 1h), S (1h-1j), M (1-3j), L (3-10j), XL (> 10j)

---

## 12. Recommandations priorisées

### Sprint 1 — Avant promotion 2.0.0 vers production (~ 2-3 jours)

1. **Fixer l'incohérence d'authentification** (#2). Migrer `mvc/controllers/auth_controller.py` vers `core.auth.verify_password` (Argon2). Ajouter un test d'intégration end-to-end qui crée un user via la CLI puis se connecte via l'application.
2. **Corriger ou déprécier PBKDF2** (#1, #10). Soit monter à 600K avec mécanisme de re-hash transparent, soit supprimer le module et tout migrer sur Argon2 (préféré). Mettre à jour le tableau du README.
3. **Whitelister les clés de filtres dans le CRUD généré** (#3). Générer un `_ALLOWED_FILTERS` au moment de la génération CRUD, valider chaque clé avant concaténation.
4. **Documenter explicitement la limitation multi-process** (#4). Bloc en évidence dans le README et dans la doc de déploiement, idéalement avec un `assert` au démarrage si le nombre de workers est détectable.

### Sprint 2 — Hygiène qualité (~ 1 semaine)

5. **Décider du sort du dossier `cmd/`** (#6). Soit le supprimer complètement, soit ajouter `warnings.warn(DeprecationWarning, ...)` au top de chaque module. Mettre à jour `cmd/README.md`.
6. **Cache i18n** (#7). Quelques lignes avec `lru_cache`.
7. **Linter + format en CI** (#9). Ajouter `ruff` minimal (rules par défaut) et `black --check` au workflow GitHub Actions.
8. **TLS défensif** (#8). 3 lignes dans `app.py`.

### Sprint 3 — Architecture moyen terme (~ 2-3 semaines)

9. **Clarifier la stratégie auth** (#5, #11). Document de design ADR (Architecture Decision Record) : « `core/auth/` est désormais l'API officielle, `core/security/` est en compatibilité ascendante jusqu'à Forge 3.0 ». Aligner les starters. Aligner le README.
10. **Backend de session pluggable** (#4 — partie impl). Permettre `forge.configure(session_backend="memory" | "file" | "mariadb")`.
11. **Découper les modules monolithiques** (#13). Sous-package `core/auth/oidc/`.
12. **Mécanisme de nonce CSP** (#12).

### Sprint 4 — Améliorations continues

13. **SECURITY.md** (#14).
14. **Tests d'intégration HTTP end-to-end** (#16) avec un fixture qui démarre `app.py` sur port aléatoire.
15. **Métriques / observabilité** (#17) : exposition d'un endpoint `/health` et `/metrics` (format Prometheus) côté framework.

---

## 13. Risques résiduels après corrections

| Risque | Mitigation actuelle | Reste à faire |
|---|---|---|
| Multi-tenant accidentel via sessions partagées | Sessions in-memory, single-process | Documenter strictement, fournir backend pluggable |
| Compromission d'un hash PBKDF2 ancien | Comparaison temps constant | Migration des hashes à la prochaine connexion |
| Génération CRUD avec filtres applicatifs trop permissifs | `_ALLOWED_SORT` whitelist | Étendre aux filtres |
| OIDC mal configuré → redirect open | Validation des `redirect_uri` | Tests d'intégration avec mocks IdP réels |
| DoS via uploads | Cap `UPLOAD_MAX_SIZE` | Quotas par utilisateur ? |

---

## 14. Verdict final

**Forge 2.0.0 est un framework Python MVC sérieux, soigné et largement au-dessus de la moyenne pour son périmètre déclaré.**

La discipline de tests, la séparation framework/application, la couverture des fondamentaux sécurité (CSRF, headers, path traversal, SQL paramétrisé, Argon2 disponible, MFA, OIDC, RBAC, audit log, rate limit) et la démarche d'audit interne explicite (`docs/history/audits/`) en font un projet remarquable, en particulier pour un travail individuel.

Les **4 points 🔴 identifiés sont tous corrigeables en moins d'une semaine cumulée**. Une fois traités, le framework peut raisonnablement être proposé comme prêt pour des mises en production réelles dans son périmètre cible (applications web petite/moyenne, single-process derrière Nginx).

Le principal sujet de fond pour la suite de l'évolution est **la clarification de la stratégie d'authentification** (point 5 du tableau) : trancher entre maintenir les deux piles avec une frontière claire ou migrer vers `core/auth/` exclusivement. Sans cette décision, la dette continuera de croître à chaque nouveau starter ou contrôleur.

**Note globale (subjective) : 4 / 5.** Avec les correctifs Sprint 1, on passe à 4.5 / 5.

---

*Audit généré le 9 mai 2026. Les références aux numéros de ligne et aux commits sont valables pour le commit `435ffa9` de l'archive auditée.*
