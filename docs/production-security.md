# Sécurité en production — Guide Forge

Ce guide rassemble les bonnes pratiques de déploiement sécurisé de Forge.
Il consolide les résultats des audits de sécurité réalisés lors de la Phase 4.5 :
SECURITY-AUDIT-001, SECURITY-CSRF-AUDIT-001, SECURITY-AUTH-AUDIT-001,
SECURITY-COOKIES-001, SECURITY-HEADERS-001, SECURITY-UPLOADS-AUDIT-001 et SECURITY-RBAC-AUDIT-001.

Voir aussi : [Déploiement](deployment.md) · [Auth/User](auth.md) · [RBAC](rbac.md) · [Médias](media.md)

---

## 1. Architecture de production — HTTPS obligatoire

**En production, Forge doit être exécuté derrière un reverse proxy HTTPS.**

```mermaid
flowchart LR
    I(["Internet<br/>HTTPS :443"]) -->|"TLS terminé"| N["Nginx<br/>reverse proxy"]
    N -->|"HTTP local"| F["Forge<br/>Python :8000"]
    F -->|"SQL"| M[("MariaDB<br/>:3306")]
```

Forge inclut un serveur HTTPS Python adapté au développement local
(`APP_SSL_ENABLED=true`, TLS 1.2 minimum). **Ce serveur ne doit pas être exposé
directement à Internet en production.** En mode `prod`, `APP_SSL_ENABLED=false`
est le défaut — Forge écoute en HTTP local, Nginx termine TLS.

La configuration Nginx générée par `forge deploy:init` expose un bloc HTTP :
ajouter un bloc `listen 443 ssl` avec `ssl_certificate` / `ssl_certificate_key`
(Let's Encrypt + Certbot recommandé) avant la mise en production.

Pourquoi HTTPS est obligatoire pour Forge :

- Les cookies de session portent l'attribut `Secure` — ils ne sont transmis que via HTTPS.
- HSTS (`Strict-Transport-Security`) est émis sur toutes les réponses — le navigateur
  refusera les connexions HTTP après la première visite.
- La CSP, Referrer-Policy et Permissions-Policy ont leur plein effet uniquement sur HTTPS.

---

## 2. Cookies de session

Résultats confirmés par SECURITY-COOKIES-001.

### Attributs appliqués

Tout cookie de session Forge est émis avec le préfixe `__Host-` :

```
Set-Cookie: __Host-session_id=<jeton opaque>; Path=/; HttpOnly; SameSite=Strict; Secure
```

| Attribut | Valeur | Garantie |
|---|---|---|
| `HttpOnly` | oui | JavaScript ne peut pas lire le cookie |
| `SameSite` | `Strict` | Cookie non transmis sur les requêtes cross-origin |
| `Secure` | oui | Cookie non transmis en HTTP clair |
| `Path` | `/` | Portée globale sur l'application |
| Valeur | jeton opaque (UUID hex) | Aucune donnée sensible dans le cookie |

`Secure` est actif en développement et en production. C'est un choix délibéré :
il force l'utilisation de HTTPS même en local et évite toute régression
si `app_env` est mal configuré.

### Durée et rotation

- Durée de session : `DUREE_SESSION = 3600` secondes (1 heure), gérée côté serveur.
- À la déconnexion, `Max-Age=0` invalide le cookie immédiatement.
- Au login, `authentifier_session()` effectue une **rotation de session** :
  l'ancien identifiant de session est révoqué et un nouveau est émis — protection
  contre la fixation de session.

### Ce qui n'est pas en session

Aucun mot de passe, hash, token MFA, email ni donnée personnelle sensible n'est
stocké dans le cookie ou en session côté serveur. La session contient uniquement :
`id`, `login`, `roles`, `permissions`, `authentifie`, `expire_a`, `csrf_token`.

### Limites connues

- `SameSite=Strict` peut bloquer la transmission du cookie sur les liens entrants
  depuis des sites tiers (ex. e-mail, notification externe). À documenter dans
  les applications qui nécessitent ce flux.

---

## 3. Headers HTTP de sécurité

Résultats confirmés par SECURITY-HEADERS-001.

### Stack complète

Les headers suivants sont émis sur **toutes** les réponses HTTP (200, 302, 404,
403, fichiers statiques, réponses `/media`) par `RequestHandler._send_response()` :

| Header | Valeur | Rôle |
|---|---|---|
| `X-Frame-Options` | `DENY` | Interdit l'inclusion dans un iframe |
| `X-Content-Type-Options` | `nosniff` | Interdit le MIME-sniffing |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS 1 an, tous sous-domaines |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit l'envoi du Referer |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` | Désactive les API sensibles |
| `Content-Security-Policy` | voir ci-dessous | Politique de contenu |
| `Cache-Control` | `no-store` sur routes auth | Interdit la mise en cache des pages sensibles |

### Content-Security-Policy

CSP par défaut (sans nonce) :

```
default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:;
font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self';
form-action 'self'
```

- `unsafe-inline` et `unsafe-eval` ne sont jamais ajoutés automatiquement.
- `frame-ancestors 'none'` bloque tout framing (renforce `X-Frame-Options: DENY`).
- Nonce optionnel pour scripts inline contrôlés : `APP_CSP_NONCE_ENABLED=true`.

```dotenv
APP_CSP_NONCE_ENABLED=true
```

```html
<script nonce="{{ csp_nonce() }}">/* script inline autorisé */</script>
```

### Cache-Control sur les routes auth

Depuis **SECURITY-CACHE-001**, les routes d'authentification reçoivent
automatiquement `Cache-Control: no-store` :

| Route | Méthode | No-store |
|---|---|---|
| `/login` | GET | ✅ |
| `/login` | POST | ✅ |
| `/login/mfa` | GET | ✅ |
| `/login/mfa` | POST | ✅ |
| `/logout` | POST | ✅ |

Le header est ajouté dans `_send_response()` (app.py) si le chemin est dans
`_AUTH_NO_STORE_PATHS` et si la réponse ne fixe pas déjà `Cache-Control`.
Les fichiers statiques conservent leur propre `Cache-Control: max-age=…`.

### Limites connues

- CSP sans `img-src`, `font-src`, `connect-src` explicites distincts :
  couverts par `default-src 'self'` mais non listés séparément.
- HSTS est émis même en HTTP local (développement) : inoffensif mais techniquement
  redondant.

---

## 4. CSRF

Résultats confirmés par SECURITY-CSRF-AUDIT-001.

### Mécanisme

La protection CSRF est activée par défaut via `CsrfMiddleware`. Le token est
généré à la création de session et stocké en session côté serveur.

- Méthodes protégées : `POST`, `PUT`, `PATCH`, `DELETE`.
- Méthodes exemptées : `GET`, `HEAD`, `OPTIONS`.
- Token transmis via le champ de formulaire `csrf_token` ou le header `X-CSRF-Token`.

### Validation

Token absent → `403`. Token invalide → `403`. Token d'une autre session → `403`.

```html
<!-- Dans chaque formulaire POST -->
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

```javascript
// Requête AJAX
fetch('/api/action', {
    method: 'POST',
    headers: { 'X-CSRF-Token': document.querySelector('[name=csrf_token]').value },
    body: JSON.stringify(data)
});
```

### Opt-out explicite

Une route ou un groupe peut désactiver la vérification CSRF avec `csrf=False`.
Ce paramètre est **explicite** — aucune route n'est exempte sans déclaration.

Les routes `public=True` restent protégées par CSRF sauf si `csrf=False`
est également spécifié.

### Method override

Forge gère le method override `POST → DELETE/PUT/PATCH` via `_method`. Le token
CSRF est vérifié **sur la méthode finale** après override. Un formulaire HTML
DELETE/PUT/PATCH doit inclure le token.

---

## 5. Authentification et audit

Résultats confirmés par SECURITY-AUTH-AUDIT-001.

### Journalisation des événements

`log_auth_event()` (module `core.auth.audit`) est branché dans
`auth_controller.py` et `mfa_challenge_controller.py`. Logger :
`forge.auth.audit`.

| Événement | Niveau | Déclencheur |
|---|---|---|
| `login.success` | INFO | Connexion réussie |
| `login.failed` | WARNING | Mot de passe incorrect |
| `user.disabled` | WARNING | Tentative de connexion sur compte désactivé |
| `logout` | INFO | Déconnexion |
| `mfa.challenge.success` | INFO | Challenge MFA validé |
| `mfa.challenge.failed` | WARNING | Code MFA incorrect |

### Données absentes des logs

Aucun mot de passe, hash, token MFA ni donnée sensible n'est émis dans les
messages de log. `sanitize_auth_audit_metadata()` filtre les champs interdits
avant emission. En cas d'erreur interne dans le logger, `log_auth_event()`
avale silencieusement l'exception pour ne pas perturber le flux d'authentification.

### Configuration des logs en production

Configurer un handler `forge.auth.audit` dans le système de logging Python
pour rediriger les événements vers le fichier de log applicatif ou syslog :

```python
import logging

handler = logging.FileHandler("/var/log/forge-app/auth.log")
handler.setLevel(logging.INFO)
logging.getLogger("forge.auth.audit").addHandler(handler)
logging.getLogger("forge.auth.audit").setLevel(logging.INFO)
```

Les logs d'audit ne sont pas configurés automatiquement par Forge —
la politique de log appartient à l'application.

### Rate limiting

Une protection anti-bruteforce est active sur `/login` via `core.auth.rate_limit`.
Les paramètres de seuil sont configurables dans l'application.

Une protection anti-abus est active sur les routes d'upload via `core.uploads.rate_limit`.
Par défaut : 10 uploads par IP par fenêtre glissante de 60 secondes.
Les compteurs sont **isolés** des compteurs de connexion.

---

## 6. RBAC — Contrôle d'accès

Résultats confirmés par SECURITY-RBAC-AUDIT-001.

### Deux systèmes coexistants

| Système | API | Source des permissions |
|---|---|---|
| Historique | `@require_permission(code)` | `request.permissions` (injection serveur) |
| Auth/User | `@require_user_permission(code)` | `user_roles → roles → permissions` (DB) |

Les deux systèmes sont **étanches** : `request.permissions` n'influence pas
`@require_user_permission`, et le `user_id` Auth/User n'influence pas
`@require_permission`.

### Principe fondamental : protection serveur obligatoire

**Le masquage UI (`{% if can() %}`) n'est pas une barrière de sécurité.**
Il améliore l'ergonomie mais ne remplace pas le décorateur serveur.

```python
# ✅ Protection serveur — obligatoire pour la sécurité
@staticmethod
@require_permission("posts.delete")
def delete(request, post_id):
    ...

# ✅ Masquage UI — optionnel, améliore l'UX
# {% if can("posts.delete") %}
#   <button>Supprimer</button>
# {% endif %}
```

### Helpers Jinja `can()`

`make_can(request)` (système historique) et `make_auth_jinja_can(request)`
(système Auth/User) retournent un callable `can(permission) → bool`.

- Retourne toujours un `bool` (jamais `None`).
- Avale silencieusement toute exception (échec DB, permission invalide).
- Retourne `False` pour un utilisateur anonyme, un code vide, un code sans point.

```jinja2
{# Masquage conditionnel côté UI — n'est pas une protection serveur #}
{% if can("posts.edit") %}
  <a href="/posts/{{ post.id }}/edit">Modifier</a>
{% endif %}
```

### Limite connue — boutons CRUD sans guard UI

Les templates CRUD générés par `make:crud` (table partielle, vue show) affichent
les boutons **Modifier** et **Supprimer** sans `{% if can() %}` conditionnel.
La protection serveur est présente (`@require_permission` dans le contrôleur
généré si `rbac.permissions` est déclaré), et depuis **CRUD-RBAC-UI-001**
(livré), les templates générés incluent également des guards `{% if can() %}`
autour de ces boutons quand `rbac.permissions` est déclaré dans la définition.

---

## 7. Uploads et médias

Résultats confirmés par SECURITY-UPLOADS-AUDIT-001.

### Architecture de validation

Tout upload transite par la chaîne :
`validate_upload_metadata()` → `save_bytes()` → `normalize_media_path()`.

### Anti-path-traversal

`normalize_media_path()` + `os.path.commonpath()` bloquent les accès hors racine.
La racine absolue `storage/uploads/` est vérifiée sur chaque accès.

Chemins refusés : `/etc/passwd`, `../secret`, `images/../../secret`,
null bytes, URLs (`https://...`), chemins Windows absolus.

### Extensions interdites (liste non exhaustive)

`.php`, `.py`, `.html`, `.js`, `.svg`, `.sh`, `.exe`, `.env` — toute extension
hors liste blanche est refusée. Liste blanche par défaut : `jpg`, `jpeg`, `png`,
`webp`, `pdf`.

### Noms de fichiers

`secure_filename()` retire le chemin (basename uniquement), remplace les
caractères spéciaux. `generate_unique_filename()` ajoute un UUID hex — impossible
de prédire le nom du fichier en base ou d'écraser un fichier existant.

### Route `/media`

GET `/media/<path>` est contrôlé par `serve_media_file()`. Le path traversal
via l'URL est bloqué avant toute lecture. Les fichiers sont servis uniquement
depuis `storage/uploads/`.

**Ne jamais servir `storage/` directement via Nginx** sans passer par la route
`/media` de Forge — le filtrage anti-traversal ne s'appliquerait pas.

### Rate limiting upload

`core.uploads.rate_limit` implémente une fenêtre glissante en mémoire, thread-safe.

Usage minimal dans un contrôleur :

```python
from core.uploads.rate_limit import is_upload_rate_limited, record_upload_attempt

def upload_avatar(request):
    if is_upload_rate_limited(request.ip):
        body = json.dumps({
            "success": False,
            "error": {"code": "rate_limited", "message": "Trop d'uploads."},
        }).encode()
        return Response(429, body, "application/json")
    record_upload_attempt(request.ip)
    # ... traitement normal
```

| Constante | Valeur par défaut | Rôle |
|---|---|---|
| `UPLOAD_MAX_PAR_FENETRE` | 10 | Uploads autorisés par IP par fenêtre |
| `UPLOAD_FENETRE_SECONDES` | 60 | Durée de la fenêtre glissante (secondes) |

### Limites connues

- Pas de validation de signature binaire (magic bytes) : un fichier dangereux
  avec une extension et un Content-Type valides est accepté.
  Ticket futur : intégrer `python-magic` si nécessaire.
- Tests E2E multipart couverts par `test_e2e_upload_http.py` via `Application.dispatch()`
  (quasi-E2E, sans serveur TCP). Magic bytes non testés (ticket futur).
- Pas de scan antivirus intégré.

---

## 8. Logs runtime (mode développement)

Forge écrit les erreurs runtime dans :

```
storage/logs/errors.dev.jsonl   ← erreurs structurées JSON (une par ligne)
storage/logs/errors.dev.md      ← rapport lisible par humain
```

Ces fichiers sont **réservés au mode développement**. Ils contiennent les
tracebacks Python complets — **ne jamais les exposer publiquement**.

En production :

- Ne pas versionner `storage/logs/`.
- Ne pas servir `storage/` directement via Nginx.
- Configurer `.gitignore` : `storage/logs/` doit être exclu.
- Forge ne produit pas de fichier JSONL de logs en mode `prod`. La gestion
  des erreurs production (syslog, Sentry, ELK) est à la charge de l'application.

---

## 9. Secrets et fichiers sensibles

### Fichiers à ne jamais versionner

```
env/prod          → variables de production (DB, secrets)
env/dev           → variables de développement
storage/logs/     → logs runtime contenant des tracebacks
storage/uploads/  → fichiers uploadés par les utilisateurs
.git/             → historique Git (peut contenir des secrets commités)
```

Vérifier `.gitignore` :

```gitignore
env/prod
env/dev
storage/logs/
storage/uploads/
*.pem
*.key
```

### Variables sensibles

Ne jamais mettre de mot de passe, clé privée ou secret dans le code source.
Toujours passer par `env/prod` chargé via `EnvironmentFile=` dans le service systemd.

Variables critiques :

```dotenv
DB_APP_PWD=<mot_de_passe_fort>
DB_ADMIN_PWD=<mot_de_passe_admin_mariadb>
SSL_KEYFILE=<chemin_clé_privée>
```

### Permissions fichiers

Recommandations pour un déploiement Linux :

```bash
# Projet appartient à l'utilisateur applicatif (ex. forge-app)
chown -R forge-app:forge-app /srv/mon-projet/

# env/prod lisible uniquement par l'utilisateur applicatif
chmod 600 /srv/mon-projet/env/prod

# Clé privée TLS
chmod 600 /srv/mon-projet/key.pem

# storage/ accessible en écriture par l'application uniquement
chmod 750 /srv/mon-projet/storage/
chmod 750 /srv/mon-projet/storage/uploads/
chmod 700 /srv/mon-projet/storage/logs/
```

---

## 10. Base de données — principe de moindre privilège

Forge utilise deux comptes MariaDB :

| Compte | Variable | Droits requis |
|---|---|---|
| Compte applicatif | `DB_APP_LOGIN` / `DB_APP_PWD` | `SELECT`, `INSERT`, `UPDATE`, `DELETE` sur la base applicative uniquement |
| Compte admin | `DB_ADMIN_LOGIN` / `DB_ADMIN_PWD` | `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE` — migrations uniquement |

Le compte applicatif **ne doit pas avoir de droits DDL** (`CREATE`, `DROP`, `ALTER`).
Le compte admin n'est utilisé que par `forge db:init` et `forge db:apply`.

```sql
-- Créer le compte applicatif avec droits limités
GRANT SELECT, INSERT, UPDATE, DELETE ON mon_projet_db.* TO 'app_user'@'localhost' IDENTIFIED BY 'mot_de_passe';
FLUSH PRIVILEGES;
```

### Tests E2E MariaDB

Les tests E2E MariaDB (`test_e2e_mariadb.py`) ne s'exécutent que si
`FORGE_E2E_MARIADB=1` est défini. Le nom de la base **doit commencer par
`forge_e2e_`** — vérification appliquée pour empêcher l'exécution accidentelle
sur une base de production.

**Ne jamais pointer les tests E2E vers une base de production.**

---

## 11. Configuration dev / prod

| Paramètre | Développement | Production |
|---|---|---|
| `APP_ENV` | `dev` | `prod` |
| `APP_SSL_ENABLED` | `true` (optionnel) | `false` (Nginx termine TLS) |
| `APP_DEBUG` | (absent = erreurs visibles) | désactiver l'affichage d'erreurs |
| Logs runtime JSONL | `storage/logs/errors.dev.jsonl` | non produits |
| `DB_APP_LOGIN` | compte de dev | compte applicatif restreint |
| Session store | Mémoire (défaut) | Fichier ou MariaDB recommandé |

En production, Forge doit être lancé avec `--env prod` (ou `APP_ENV=prod` dans
`env/prod`) pour désactiver les comportements de développement.

---

## 12. Checklist production sécurisée

```
Infrastructure
──────────────
[ ] HTTPS actif via reverse proxy (Nginx)
[ ] Certificat TLS valide (Let's Encrypt / CA interne)
[ ] Domaine configuré dans Nginx (server_name)
[ ] Port 8000 non exposé publiquement (firewall)

Application
───────────
[ ] APP_ENV=prod dans env/prod
[ ] APP_SSL_ENABLED=false (Nginx termine TLS)
[ ] Secrets hors Git (env/prod dans .gitignore)
[ ] Mot de passe DB fort et non par défaut

Cookies et sessions
────────────────────
[ ] Cookies Secure compatibles HTTPS (actif par défaut)
[ ] Session store persistant configuré (Fichier ou MariaDB)
[ ] Durée session adaptée aux besoins métier

Sécurité applicative
─────────────────────
[ ] CSRF actif (défaut — ne pas désactiver sans raison)
[ ] Headers sécurité présents sur toutes les réponses (défaut)
[ ] RBAC : routes protégées par décorateurs serveur (@require_permission)
[ ] Auth audit : handler de log configuré (forge.auth.audit)
[ ] Rate limiting login actif
[ ] Rate limiting upload actif (core.uploads.rate_limit)

Fichiers et stockage
─────────────────────
[ ] storage/ non exposé directement via Nginx
[ ] storage/uploads servi uniquement via route /media
[ ] storage/logs non accessible publiquement
[ ] Permissions fichiers restreintes (env/prod chmod 600)

Base de données
────────────────
[ ] Compte applicatif sans droits DDL
[ ] Compte admin utilisé uniquement pour les migrations
[ ] Base de test forge_e2e_* séparée de la production

Maintenance
────────────
[ ] Sauvegardes DB planifiées
[ ] Rotation des logs prévue
[ ] Procédure de mise à jour documentée
```

---

## 13. Dettes et tickets futurs

| Ticket | Domaine | Description |
|---|---|---|
| `SECURITY-CACHE-001` | Headers | ~~`Cache-Control: no-store` absent sur pages HTML authentifiées~~ livré |
| `SECURITY-COOKIES-HOST-PREFIX-001` | Cookies | ~~Ajouter le préfixe `__Host-` sur le cookie `session_id`~~ livré |
| `CRUD-RBAC-UI-001` | RBAC | ~~Ajouter `{% if can() %}` sur boutons Modifier/Supprimer dans templates CRUD générés~~ livré |
| `E2E-UPLOAD-HTTP-001` | Uploads | ~~Tests multipart HTTP réels (cycle POST complet)~~ livré |
| `SECURITY-UPLOAD-RATE-LIMIT-001` | Uploads | ~~Rate limit sur les uploads~~ livré |

---

*Guide consolidé lors de DEPLOY-PROD-SECURITY-DOC-001 (Phase 4.5 sécurité avancée).*
