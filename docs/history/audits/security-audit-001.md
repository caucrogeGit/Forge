# Audit SECURITY-AUDIT-001 — Sécurité globale Forge

**Date :** 9 mai 2026  
**Version Forge :** 2.2.0  
**Commit de référence :** `d6ca263`

---

## Objectif

Réaliser un audit de sécurité transverse de Forge 2.2.0 sur dix domaines :
CSRF, cookies/sessions, headers HTTP, uploads, Auth/RBAC/MFA/OIDC, journalisation des erreurs,
SQL/migrations, templates/XSS, fichiers statiques, déploiement.

L'audit est **descriptif uniquement** — aucune correction n'est apportée dans ce ticket.
Les lacunes identifiées font l'objet de tickets de suivi.

---

## Résumé exécutif

Forge 2.2.0 présente un niveau de sécurité **satisfaisant pour un framework web Python sans ORM**.
Les protections fondamentales sont en place : CSRF opt-out, cookies sécurisés, headers HTTP complets,
requêtes SQL paramétrées, autoescape Jinja2 actif, anti-traversal sur les fichiers statiques et les médias.

Les **risques majeurs identifiés** sont :
1. CSRF jamais vérifié dans un vrai cycle HTTP (tests unitaires uniquement).
2. Journalisation des événements d'authentification non branchée (`core/auth/audit.py` existe mais n'est pas appelé).
3. Cookies de session avec `Secure` — mais émis sans restriction de domaine ni `__Host-` prefix.
4. CSP sans directives `img-src`, `font-src`, `connect-src` explicites (couvertes par `default-src 'self'`, mais non explicites).
5. HSTS émis même sur les réponses HTTP (dev) — inoffensif mais incorrect.

Aucune vulnérabilité critique n'a été détectée dans le code core audité.

---

## Méthode d'audit

Lecture manuelle des fichiers sources :

| Fichier / Zone | Objet de la lecture |
|---|---|
| `core/security/middleware.py` | CSRF, AuthMiddleware |
| `core/security/session.py` | Session ID, rotation, CSRF token |
| `core/security/csp.py` | Construction de la CSP |
| `core/http/router.py` | Opt-out CSRF, routes publiques |
| `core/application.py` | Dispatch, ordre des middlewares, gestion 500 |
| `core/http/response.py` | Structure de la réponse HTTP |
| `app.py` | `_send_response`, headers de sécurité, static, media |
| `core/uploads/validators.py` | Whitelist extensions, MIME, taille |
| `core/uploads/storage.py` | Normalisation chemins, UUID, `open("xb")` |
| `core/runtime_error_logger.py` | Journalisation en dev |
| `integrations/jinja2/renderer.py` | `autoescape`, environnement Jinja2 |
| `mvc/views/layouts/*.html` | Usages de `\| safe` |
| `mvc/helpers/flash.py` + `mvc/views/components/alert.html` | Chaîne flash → HTML |
| `mvc/controllers/auth_controller.py` | Login, Set-Cookie, rate limit |
| `mvc/controllers/mfa_challenge_controller.py` | Set-Cookie après MFA |
| `core/auth/__init__.py`, `rate_limit.py`, `audit.py` | Contrats Auth/rate limit/audit |
| `forge_cli/entities/crud/model_builder.py` | SQL généré paramétré |
| `forge_cli/entities/crud/views_builder.py` + `forge_cli/public_form.py` | CSRF dans les formulaires générés |
| `docs/deployment.md` | Documentation déploiement |

---

## Périmètre audité

| Domaine | Fichiers principaux | Couvert |
|---|---|---|
| CSRF | `middleware.py`, `router.py`, formulaires générés | ✅ |
| Cookies/Sessions | `auth_controller.py`, `mfa_challenge_controller.py`, `session.py` | ✅ |
| Headers HTTP | `app.py` (`_send_response`), `csp.py` | ✅ |
| Uploads | `validators.py`, `storage.py`, `app.py` (`_serve_media`) | ✅ |
| Auth/RBAC/MFA/OIDC | `auth_controller.py`, `core/auth/`, `middleware.py` | ✅ |
| Runtime errors | `runtime_error_logger.py` | ✅ |
| SQL/Migrations | `model_builder.py`, `migrations.py` | ✅ |
| Templates/XSS | `renderer.py`, layouts HTML, `flash.py`, `alert.html` | ✅ |
| Fichiers statiques | `app.py` (`_serve_static`, `_is_safe_static_path`) | ✅ |
| Déploiement | `docs/deployment.md`, `deploy/nginx/forge-app.conf` | ✅ |

---

## Synthèse des risques

| Domaine | Niveau | Résumé |
|---|---|---|
| CSRF | Moyen | Mécanisme solide, mais jamais validé en HTTP réel |
| Cookies/Sessions | Faible | Flags complets ; audit log non branché |
| Headers HTTP | Faible | Stack complète ; HSTS sur HTTP, pas de Permissions-Policy |
| Uploads | Faible | Protections multicouches ; pas de test HTTP multipart |
| Auth/RBAC/MFA/OIDC | Moyen | Mécanismes présents ; audit log non utilisé ; rate limit par IP seul |
| Runtime errors | Aucun | Sécurisé par conception (dev only, pas de valeurs) |
| SQL/Migrations | Faible | Paramétré partout ; `on_delete`/`on_update` par interpolation (validé en amont) |
| Templates/XSS | Faible | Autoescape actif ; chaîne `\|safe` documentée mais subtile |
| Fichiers statiques | Aucun | Anti-traversal par commonpath + realpath |
| Déploiement | Faible | Architecture Nginx recommandée ; config HTTP-only sans TLS par défaut |

---

## CSRF

### État audité

**`core/http/router.py`** — `RouteEntry.csrf = True` par défaut. Le modèle est opt-out (toutes les routes sont protégées sauf déclaration explicite `csrf=False`).

**`core/security/middleware.py`** — `CsrfMiddleware.check()` :
- Lit `csrf_token` depuis `session["csrf_token"]`.
- Compare au champ de formulaire `request.body.get("csrf_token")` ou à l'en-tête `X-CSRF-Token`.
- Retourne `_html("errors/403.html", 403)` en cas d'échec.
- Vérifié **avant** les middlewares d'authentification dans `Application.dispatch()`.

**Formulaires générés** (`forge_cli/entities/crud/views_builder.py`, `forge_cli/public_form.py`) :
tous les formulaires générés incluent :
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

### Zones bien protégées

- Modèle opt-out : par défaut toute la surface POST/PUT/PATCH/DELETE est couverte.
- Vérification avant les middlewares auth : pas de contournement CSRF via une route protégée.
- Token de formulaire et en-tête acceptés : compatible avec les requêtes AJAX.

### Lacunes

- **Jamais testé sur un vrai cycle HTTP.** La validation CSRF est couverte unitairement mais aucun test ne soumet un formulaire réel via le serveur et vérifie le comportement en cas de token absent ou invalide.
- **Starter 2 (bibliothèque) et starter 4 (portfolio)** n'ont pas de build E2E complet — impossible de vérifier que le CSRF est correctement injecté dans tous leurs formulaires.

---

## Cookies et sessions

### État audité

**`mvc/controllers/auth_controller.py`** — Toutes les émissions `Set-Cookie` incluent :
```
session_id=<token>; Path=/; HttpOnly; SameSite=Strict; Secure
```
Sur logout :
```
session_id=; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=0
```

**`mvc/controllers/mfa_challenge_controller.py`** — Même format après rotation post-MFA.

**`core/security/session.py`** :
- `authentifier_session()` effectue une rotation du `session_id` à la connexion (`secrets.token_hex(32)`).
- `regenerer_session()` disponible contre la fixation de session.
- `DUREE_SESSION = 3600` (expire serveur).

### Zones bien protégées

- `HttpOnly` : pas accessible via JavaScript.
- `SameSite=Strict` : protection CSRF redondante côté cookie.
- `Secure` : cookie transmis en HTTPS seulement.
- Rotation à la connexion et au challenge MFA.
- Invalidation explicite (Max-Age=0) à la déconnexion.
- IDs session générés avec `secrets.token_hex(32)` (256 bits d'entropie).

### Lacunes

- **Gestion des flags par contrôleur.** Les attributs `HttpOnly; SameSite=Strict; Secure` sont dupliqués manuellement dans chaque contrôleur qui émet un cookie. Aucun helper centralisé — un futur contrôleur personnalisé pourrait omettre ces flags sans warning.
- **Pas de `Max-Age` sur la création initiale.** Le cookie de session est un cookie de session navigateur (expire à la fermeture). Une durée explicite alignée sur `DUREE_SESSION` serait plus défensive.
- **Pas de `__Host-` ou `__Secure-` préfixe.** Ces préfixes imposent `Secure` et `Path=/` au niveau du navigateur, offrant une protection supplémentaire contre les sous-domaines compromis.
- **Journalisation Auth non branchée.** `core/auth/audit.py` définit `AuthAuditEvent` et les helpers de journalisation, mais `auth_controller.py` ne les appelle pas. Les événements de connexion réussie ou échouée ne sont pas enregistrés.

---

## Headers HTTP

### État audité

**`app.py` — `_send_response()`** — Headers émis sur **toutes** les réponses :

| Header | Valeur |
|---|---|
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | via `csp.py` |

**`core/security/csp.py`** — CSP de base :
```
default-src 'self'; style-src 'self'; script-src 'self'[{nonce}]; frame-ancestors 'none'
```

### Zones bien protégées

- Stack de headers de sécurité complète et systématique (toutes les réponses).
- `frame-ancestors 'none'` redondant avec `X-Frame-Options: DENY` — bonne défense en profondeur.
- `script-src` avec nonce optionnel via `APP_CSP_NONCE_ENABLED`.
- `'unsafe-inline'` absent de la CSP.

### Lacunes

- **HSTS émis en mode HTTP.** En développement (sans TLS), `Strict-Transport-Security` est envoyé inutilement. Bien que non dangereux en local, c'est techniquement incorrect et peut gêner les tests.
- **Pas de `Permissions-Policy`.** Aucun contrôle des API navigateur (caméra, microphone, géolocalisation) — la valeur restrictive `Permissions-Policy: geolocation=(), microphone=(), camera=()` serait une bonne pratique.
- **CSP sans directives explicites `img-src`, `font-src`, `connect-src`.** Techniquement couvert par `default-src 'self'`, mais une CSP stricte préfère les directives explicites pour éviter les surprises si `default-src` évolue.
- **Pas de `Cache-Control: no-store` sur les routes authentifiées.** Les réponses privées pourraient être mises en cache par le navigateur ou un proxy intermédiaire.

---

## Uploads / Médias

### État audité

**`core/uploads/validators.py`** :
- Whitelist d'extensions (images, docs, PDF, vidéo, audio).
- Validation du type MIME par lecture des magic bytes.
- Limite de taille configurable (`UPLOAD_MAX_SIZE`).

**`core/uploads/storage.py`** :
- `secure_filename()` : suppression des caractères dangereux par regex (`[^a-zA-Z0-9._-]`), basename uniquement.
- `normalize_media_path()` : bloque `..`, `//`, chemins absolus, URL schemes.
- `media_path_to_storage_path()` : `os.path.commonpath` comme double vérification anti-traversal.
- Nom de fichier stocké : UUID (`uuid4()`) — supprime toute information d'origine.
- `open("xb")` : création exclusive (pas d'écrasement possible par race condition).

### Zones bien protégées

- Défense en profondeur : validation → normalisation → UUID → commonpath.
- Pas de nom de fichier utilisateur dans le stockage final.
- Pas d'exécution possible (fichiers servis via `_serve_media` avec Content-Type détecté).

### Lacunes

- **Aucun test de cycle HTTP complet.** Aucun test ne soumet un vrai formulaire `multipart/form-data` au serveur et vérifie le rejet de MIME spoofing, la limite de taille ou le retour URL.
- **Racine de stockage non documentée hors webroot.** La sécurité des uploads dépend que `UPLOAD_ROOT` pointe vers un dossier hors de `static/`. La documentation de déploiement ne le précise pas explicitement.

---

## Auth / RBAC / MFA / OIDC

### État audité

**Rate limiting** — `core/security/hashing.py` : `est_limite(request.ip)` vérifié à la soumission du formulaire de login. Retourne 429 si la limite est atteinte. `enregistrer_tentative(request.ip)` loggé sur chaque échec.

**Session** — Rotation à la connexion et après challenge MFA. `@login_required` via `core/security/decorators.py`.

**RBAC** — Protection à trois niveaux : route (`requires_auth`), template (`can("permission")`), SQL (filtrage des données retournées).

**MFA** — TOTP (`core/auth/mfa.py`) + codes de récupération (`core/auth/mfa.py`). Challenge MFA (`mvc/controllers/mfa_challenge_controller.py`) + revalidation pour actions sensibles.

**OIDC** — `core/auth/oidc.py` : state + nonce + PKCE (code verifier/challenge) pour le flux Authorization Code. Association compte local / compte externe.

**Exposition Jinja** — `AuthJinjaUser` : dataclass sérialisée sans champ `password_hash`, sans token secret.

### Zones bien protégées

- Modèle opt-in : `@login_required` explicite, routes publiques déclarées (`public=True`).
- Argon2id pour le hachage (`core/auth/password.py`) + repli PBKDF2 legacy.
- PKCE sur OIDC empêche le code interception attack.
- `sanitize_jinja_user()` : filtre les champs dangereux avant exposition aux templates.
- Rate limiting opérationnel sur le login.

### Lacunes

- **Journalisation Auth non branchée.** `core/auth/audit.py` fournit `AuthAuditEvent` et les primitives de log, mais `auth_controller.py` n'importe ni ne appelle ces fonctions. Les connexions réussies, les échecs et les déconnexions ne sont pas journalisées.
- **Rate limiting par IP uniquement.** Le module `core/auth/rate_limit.py` (nouveau contrat) coexiste avec `core/security/hashing.py` (ancien rate limit IP) — migration incomplète. Pas de rate limiting par email/login, pas de blocage distribué possible.
- **Flux OIDC sans contrôleur MVC livré.** `core/auth/oidc.py` est complet, mais aucun `oidc_controller.py` dans `mvc/controllers/`. L'intégration OIDC est laissée au développeur — risque d'implémentation incorrecte.
- **Aucun test de login/logout/MFA via HTTP réel.** `test_auth_cli_to_login_e2e.py` couvre 6 tests CLI. Aucun test ne démarre le serveur HTTP et soumet un formulaire de connexion réel.

---

## Journalisation des erreurs runtime

### État audité

**`core/runtime_error_logger.py`** :
- Activé uniquement si `APP_ENV == "dev"`.
- Logue : méthode HTTP, chemin, query params, clés du corps POST (pas les valeurs), type de contenu.
- N'inclut pas : cookies, en-têtes `Authorization`, valeurs des champs de formulaire.
- Silence silencieux sur erreur d'écriture (`except Exception: pass`).

### État

**Aucune lacune critique.** La journalisation des erreurs runtime est conçue pour être sûre en dev et inactive en production.

---

## SQL / Migrations

### État audité

**`forge_cli/entities/crud/model_builder.py`** — Toutes les requêtes SQL générées utilisent des placeholders `?` :

```python
f'SELECT_BY_ID = "SELECT * FROM {table} WHERE {pk_col} = ?"'
f'INSERT       = "INSERT INTO {table} ({insert_cols}) VALUES ({insert_placeholders})"'
f'UPDATE       = "UPDATE {table} SET {update_set} WHERE {pk_col} = ?"'
f'DELETE       = "DELETE FROM {table} WHERE {pk_col} = ?"'
```

Les appels `cursor.execute(SQL_CONSTANT, (valeur,))` — pas d'interpolation de données utilisateur.

**`forge_cli/entities/relations.py`** — Construction SQL des FK :
```python
f"    ON DELETE {relation.on_delete}",
f"    ON UPDATE {relation.on_update}",
```
Ces valeurs sont validées par le schéma JSON des entités avant usage (whitelist dans `validation.py`).

### Zones bien protégées

- Toutes les requêtes CRUD générées sont paramétrées — pas d'injection SQL possible par les données utilisateur.
- SQL de schéma (`CREATE TABLE`, FK) : noms de tables et colonnes viennent des entités JSON validées, pas de l'entrée HTTP.

### Lacunes

- **`migration:diff` non testé en conditions réelles.** La comparaison entité JSON / colonnes MariaDB réelles n'est jamais exécutée en CI standard.
- **MariaDB opt-in.** Les tests d'application SQL réelle restent derrière `FORGE_E2E_MARIADB=1`. Une régression de SQL généré (type incompatible, contrainte FK) n'est pas détectée en CI.

---

## Templates / XSS

### État audité

**`integrations/jinja2/renderer.py`** :
```python
autoescape=select_autoescape(["html"])
```
L'autoescape est activé pour tous les templates `.html`. Toute variable `{{ var }}` est échappée sauf si explicitement marquée `Markup`.

**`mvc/views/layouts/base.html`, `admin.html`, `public.html`** :
```html
{{ flash_html | safe }}
```
`flash_html` est produit par `render_flash_html()` → `template_manager.render("components/alert.html", {"message": ..., "type": ...})`. Dans `alert.html`, `{{ message }}` est rendu sans `|safe` — le message flash est donc échappé au moment du rendu. Le résultat HTML de ce rendu est ensuite marqué `|safe` pour éviter le double échappement du `<div>`.

**`core/workflow/jinja.py`** :
```python
return Markup(f'<span class="{classes}">{escape(label)}</span>')
```
Usage correct : HTML statique + `escape()` sur la variable.

**`core/mail/templates.py`** :
```python
autoescape=jinja2.select_autoescape(enabled_extensions=["html", "htm"])
```
Autoescape actif pour les templates de mail.

### Zones bien protégées

- Autoescape Jinja2 actif — protection XSS par défaut.
- Chaîne `flash_html | safe` est sûre : le contenu utilisateur est échappé au niveau du template `alert.html`.
- Les badges workflow utilisent `escape()` explicitement.
- Les templates de mail sont également protégés.

### Lacunes

- **Chaîne de confiance `|safe` implicite.** L'usage de `|safe` sur `flash_html` dans les trois layouts repose sur la garantie que `render_flash_html()` n'expose jamais de contenu non échappé. Si un développeur modifie `flash.py` pour retourner du HTML construit par f-string sans `escape()`, la XSS est possible sans warning.
- **Aucun test de rendu avec données réelles via HTTP.** Les vues CRUD générées ne sont jamais chargées dans un contexte HTTP réel — une injection dans un champ de formulaire retourné en vue `edit` ne serait détectée qu'en test manuel.

---

## Fichiers statiques

### État audité

**`app.py` — `_serve_static()`** :
```python
filepath = os.path.realpath(os.path.join(STATIC_DIR, path.removeprefix("/static/")))
if not _is_safe_static_path(STATIC_DIR, filepath):
    # → 403
```

**`_is_safe_static_path()`** :
```python
return os.path.commonpath([static_dir, filepath]) == static_dir
```
Utilise `os.path.realpath()` pour résoudre les symlinks **avant** la comparaison — les symlinks hors de `static/` sont bloqués.

**Tests** — `tests/test_serve_static.py` valide : traversal `../`, dossier sibling (`staticold/`), chemin parent, cas Windows multi-drive.

### État

**Aucune lacune.** La protection anti-traversal est correcte, testée, et utilise `commonpath` (pas `startswith`).

---

## Déploiement

### État audité

**`docs/deployment.md`** :
- Architecture recommandée : Nginx (TLS) → Forge (HTTP local) → MariaDB.
- Checklist `forge deploy:init` + `forge deploy:check` + systemd.
- Avertissement explicite contre l'exposition directe à Internet.

**`deploy/nginx/forge-app.conf` généré** :
```nginx
server {
    listen 80;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header X-Forwarded-Proto $scheme;
    ...
}
```

### Zones bien protégées

- Recommandation claire : ne pas exposer Forge directement.
- `forge deploy:check` valide les variables critiques (`DB_APP_HOST`, `DB_NAME`, etc.).
- Headers de sécurité gérés par Forge (pas besoin de les dupliquer dans Nginx).
- `systemd` avec `User=www-data` — principe de moindre privilège.

### Lacunes

- **Config Nginx HTTP-only par défaut.** La configuration générée écoute sur le port 80 sans bloc HTTPS. La documentation indique comment ajouter TLS mais ne le génère pas — risque de déploiement sans HTTPS.
- **`APP_ENV=prod` non vérifié par `forge deploy:check`.** Si un déploiement part en `APP_ENV=dev`, le runtime error logger est actif, les messages d'erreur sont plus verbeux.
- **Permissions des fichiers `env/prod` non documentées.** Le fichier contient secrets DB, APP_SECRET, etc. La documentation ne recommande pas `chmod 600 env/prod`.
- **Pas de mention de rotation des secrets.** `APP_SECRET` (CSRF, session) et les credentials DB n'ont pas de politique de rotation documentée.

---

## Zones bien protégées — synthèse

1. **CSRF opt-out** : toute la surface POST est couverte par défaut.
2. **Set-Cookie** : `HttpOnly; SameSite=Strict; Secure` sur tous les points d'émission connus.
3. **Headers HTTP** : stack complète sur toutes les réponses (`X-Frame-Options`, `HSTS`, `Referrer-Policy`, `CSP`, `X-Content-Type-Options`).
4. **SQL paramétré** : aucune interpolation de données utilisateur dans les requêtes générées.
5. **Jinja2 autoescape** : activé pour tous les templates HTML.
6. **Anti-traversal statique** : `realpath` + `commonpath` + tests dédiés.
7. **Anti-traversal médias** : multicouche (`normalize_media_path` + `commonpath`).
8. **Rate limiting login** : `est_limite(ip)` + `enregistrer_tentative(ip)` + 429.
9. **Hachage argon2id** : algorithme recommandé, avec repli PBKDF2 legacy.
10. **OIDC PKCE + state + nonce** : protection complète du flux Authorization Code.

---

## Zones insuffisantes — synthèse

1. **Journalisation Auth non branchée** — `core/auth/audit.py` non utilisé dans `auth_controller.py`.
2. **CSRF non testé en HTTP réel** — validation uniquement unitaire.
3. **Rate limiting migration incomplète** — coexistence ancien (`hashing.py`) / nouveau (`auth/rate_limit.py`).
4. **OIDC sans contrôleur MVC livré** — intégration laissée au développeur.
5. **Config Nginx HTTP-only par défaut** — TLS non généré.
6. **Permissions `env/prod` non documentées** — risque sur serveur multi-utilisateurs.
7. **Pas de `Permissions-Policy`** — API navigateur non contrôlées.
8. **Pas de `Cache-Control: no-store`** sur les routes authentifiées.

---

## Risques critiques

Aucun risque critique (vulnérabilité exploitable directement) identifié.

---

## Risques moyens

1. **Audit log Auth absent** — En cas d'incident, impossibilité de reconstituer les tentatives de connexion. Ticket : `SECURITY-AUTH-AUDIT-001`.

2. **CSRF non validé en HTTP réel** — La protection peut régresser sans être détectée. Ticket : `SECURITY-CSRF-AUDIT-001` (test E2E CSRF).

3. **OIDC sans contrôleur livré** — Un développeur implémentant le callback OIDC peut commettre des erreurs de sécurité (pas de vérification state/nonce, session non régénérée). Ticket : intégré dans `AUTH-OIDC-CONTROLLER-001` (phase future).

---

## Risques faibles

4. **Rate limiting par IP seulement** — Un attaquant distribuant ses tentatives sur plusieurs IP contourne la protection. Amélioration : rate limit par email/login.

5. **HSTS sur HTTP** — Inoffensif mais incorrect. Conditionner l'émission HSTS à `APP_ENV=prod` ou `APP_SSL_ENABLED=true`.

6. **Cookies sans préfixe `__Host-`** — Protection supplémentaire contre les sous-domaines compromis, applicable si le déploiement n'utilise pas de sous-domaines.

7. **`Permissions-Policy` absent** — Faible impact mais bonne pratique.

8. **`Cache-Control: no-store` absent** — Faible impact si Nginx est correctement configuré ; risque sur les navigateurs sans cache privé.

9. **Config Nginx HTTP-only** — Risque si le déploiement oublie d'ajouter TLS manuellement.

---

## Recommandations

### Priorité 1 — Avant la prochaine release

1. **Brancher `core/auth/audit.py` dans `auth_controller.py`** (`SECURITY-AUTH-AUDIT-001`) — logguer connexion réussie, échec, déconnexion, challenge MFA.
2. **Ajouter un test CSRF sur cycle HTTP réel** (`SECURITY-CSRF-AUDIT-001`) — soumettre un formulaire sans token, vérifier le 403.

### Priorité 2 — Améliorations défensives

3. **Créer un helper centralisé `set_session_cookie(response, session_id)`** — évite la duplication des flags `HttpOnly; SameSite=Strict; Secure` dans chaque contrôleur.
4. **Conditionner HSTS à `APP_ENV != "dev"`** — éviter l'émission sur HTTP.
5. **Ajouter `Permissions-Policy: geolocation=(), microphone=(), camera=()`** dans `_send_response`.
6. **Ajouter `Cache-Control: no-store` sur les réponses des routes non publiques.**
7. **Documenter les permissions `env/prod`** (`chmod 600`) dans `docs/deployment.md`.

### Priorité 3 — Dette sécurité

8. **Unifier le rate limiting** sur `core/auth/rate_limit.py` ; supprimer l'ancienne implémentation dans `core/security/hashing.py`.
9. **Générer un bloc HTTPS dans la config Nginx** ou documenter clairement les commandes certbot.
10. **Ajouter `__Host-` prefix** sur le cookie `session_id` si les sous-domaines ne sont pas utilisés.

---

## Tickets proposés

| Ticket | Priorité | Description |
|---|---|---|
| `SECURITY-CSRF-AUDIT-001` | P1 | Test CSRF sur cycle HTTP réel + documentation |
| `SECURITY-AUTH-AUDIT-001` | P1 | Branchement `core/auth/audit.py` dans `auth_controller.py` |
| `SECURITY-COOKIES-001` | P2 | Helper centralisé `set_session_cookie()` + préfixe `__Host-` |
| `SECURITY-HEADERS-001` | P2 | Permissions-Policy + Cache-Control no-store + HSTS conditionnel |
| `SECURITY-UPLOADS-AUDIT-001` | P2 | Test HTTP multipart d'upload + documentation UPLOAD_ROOT hors webroot |
| `SECURITY-RBAC-AUDIT-001` | P2 | Unification rate limit + contrôleur OIDC MVC |
| `DEPLOY-PROD-SECURITY-DOC-001` | P3 | Documentation TLS Nginx + permissions env/prod + rotation secrets |

---

*Rapport généré dans le cadre du ticket SECURITY-AUDIT-001 — Forge 2.2.0 — 2026-05-09.*
