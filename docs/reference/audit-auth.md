# Audit Auth — Journalisation des événements d'authentification

`log_auth_event()` est la fonction centrale pour journaliser les événements d'authentification dans Forge. Elle émet des messages via le logger Python `forge.auth.audit`, sans jamais accéder à la base de données et sans jamais propager d'exception.

### Niveaux de log

| Niveau | Événements |
|--------|-----------|
| `WARNING` | `login.failed`, `mfa.challenge.failed`, `mfa.revalidation.failed`, `user.disabled` |
| `INFO` | Tous les autres (`login.success`, `logout`, `mfa.challenge.success`, etc.) |

### Données jamais journalisées

Les champs `password`, `password_hash`, `token`, `raw_token`, `access_token`, `refresh_token`, `id_token`, `secret`, `totp_secret`, `recovery_code`, `code_verifier` sont systématiquement retirés des métadonnées avant journalisation par `sanitize_auth_audit_metadata()`.

### Branchement dans les contrôleurs

`auth_controller.py` et `mfa_challenge_controller.py` appellent `log_auth_event()` sur chaque transition :

- `login.success` — connexion validée
- `login.failed` — mauvais identifiant ou mot de passe
- `user.disabled` — tentative sur un compte désactivé
- `logout` — déconnexion
- `mfa.challenge.success` — code MFA valide
- `mfa.challenge.failed` — code MFA invalide

### Configuration du logger

```python
import logging
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logging.getLogger("forge.auth.audit").addHandler(handler)
logging.getLogger("forge.auth.audit").setLevel(logging.INFO)
```

### Tests

`tests/test_auth_audit_controller.py` couvre 33 cas : niveaux INFO/WARNING, absence de données sensibles dans les logs, présence de `user_id` et `ip`, comportement des contrôleurs préservé, silence en cas d'erreur interne.

## Cookies de session — Attributs de sécurité

Tous les cookies `session_id` émis par Forge portent `HttpOnly`, `SameSite=Strict`, `Secure` et `Path=/`. Le flag `Secure` est toujours actif quelle que soit la valeur de `app_env`.

| Point d'émission | Action | Attributs |
|---|---|---|
| GET `/login` | Création de session | `HttpOnly; SameSite=Strict; Secure; Path=/` |
| POST `/login` (succès) | Rotation de session_id | `HttpOnly; SameSite=Strict; Secure; Path=/` |
| POST `/login` (MFA) | Conservation de la session | `HttpOnly; SameSite=Strict; Secure; Path=/` |
| POST `/login/mfa` (succès) | Rotation de session_id | `HttpOnly; SameSite=Strict; Secure; Path=/` |
| POST `/logout` | Expiration du cookie | `HttpOnly; SameSite=Strict; Secure; Path=/; Max-Age=0` |

### Contenu et stockage

La valeur du cookie est un token hexadécimal opaque de 64 caractères (`secrets.token_hex(32)`). Aucune donnée utilisateur ne transite dans le cookie. Les données de session sont stockées côté serveur uniquement.

### Protection contre la fixation de session

`authentifier_session()` génère un nouveau `session_id` à chaque login et supprime l'ancien. Le cookie pré-authentification ne peut pas être réutilisé après connexion.

### Logout

Le logout émet `session_id=; Max-Age=0` (expiration côté client) et appelle `supprimer_session()` (invalidation côté serveur). Les mêmes attributs de sécurité sont conservés sur la réponse de logout.

### Comportement dev / prod

Le flag `Secure` est présent en dev et en prod. Forge suppose un accès HTTPS ou proxy TLS dans tous les environnements.

### Limites

- Nom du cookie : `session_id` (pas de préfixe `__Host-`).
- Forge ne gère qu'un seul cookie de session par requête.
- `SameSite=Strict` peut bloquer le cookie lors d'un accès depuis un lien externe — adaptez à `Lax` si nécessaire dans votre application.

### Tests

`tests/test_security_cookies.py` couvre 39 cas : attributs de tous les points d'émission, contenu du cookie, données de session côté serveur, fixation de session, durée d'expiration, comportement `Secure` en dev et prod, absence de cookie CSRF séparé.

## Headers HTTP de sécurité

Forge émet les headers de sécurité suivants sur **toutes** les réponses (200, 302, 404, 403, fichiers statiques) via `RequestHandler._send_response()` dans `app.py`.

| Header | Valeur | Rôle |
|---|---|---|
| `X-Frame-Options` | `DENY` | Bloque le chargement dans un iframe |
| `X-Content-Type-Options` | `nosniff` | Interdit le MIME-sniffing |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS pendant 1 an |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limite les données referer cross-origin |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` | Désactive les API navigateur sensibles |
| `Content-Security-Policy` | `default-src 'self'; style-src 'self'; script-src 'self'[nonce]; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'` | Restreint les sources de contenu |

### Content-Security-Policy

La CSP est construite par `core/security/csp.py`. Par défaut, sans nonce :

```
default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'
```

Avec `APP_CSP_NONCE_ENABLED=true`, chaque requête reçoit un nonce unique et
`script-src` inclut `'nonce-<valeur>'` — les scripts inline portant ce nonce
sont autorisés sans `unsafe-inline`.

La CSP ne contient jamais `unsafe-inline` ni `unsafe-eval`.

| Directive | Valeur | Effet |
|---|---|---|
| `default-src` | `'self'` | Tout charger uniquement depuis l'origine |
| `style-src` | `'self'` | CSS depuis l'origine uniquement |
| `script-src` | `'self'` [`'nonce-...'`] | JS depuis l'origine ou avec nonce |
| `img-src` | `'self' data:` | Images locales et encodées en `data:` URI (SVG inline, avatars, placeholders) |
| `frame-ancestors` | `'none'` | Refuse l'inclusion en iframe |
| `object-src` | `'none'` | Refuse `<object>`, `<embed>`, `<applet>` (plugins legacy) |
| `base-uri` | `'none'` | Refuse la modification de `<base>` (empêche le détournement des URLs relatives) |
| `form-action` | `'self'` | Limite la destination des `<form action>` à l'origine (défense anti-exfiltration via formulaires injectés) |

#### Pourquoi ces deux directives explicites

`default-src 'self'` ne couvre pas :

- **`img-src`** sans `data:` bloque les images encodées en base64 (cas légitimes : SVG inline, avatars, placeholders générés par JS). La directive `img-src 'self' data:` les autorise explicitement.
- **`form-action`** n'a pas de fallback sur `default-src` selon la spécification CSP. Sans déclaration, n'importe quelle URL peut être destination d'un `<form>`. La directive `form-action 'self'` ferme ce trou.

### HSTS

`Strict-Transport-Security: max-age=31536000; includeSubDomains` est émis sur
toutes les réponses, y compris en développement local. Forge suppose que toute
configuration (y compris dev) passe par HTTPS ou un proxy TLS (cohérent avec
le flag `Secure` sur les cookies).

### Limites restantes

- `Cache-Control: no-store` absent sur les pages HTML authentifiées (login, admin).
  Le navigateur peut mettre ces pages en cache local. Ticket futur :
  `SECURITY-CACHE-001`.
- La CSP ne liste pas explicitement `font-src` et `connect-src`
  (couverts par `default-src 'self'`). `img-src` et `form-action` sont
  déclarés explicitement (voir section ci-dessus).
- `Permissions-Policy` ne couvre pas exhaustivement toutes les API navigateur
  (gyroscope, accelerometer, usb…). Complément dans un ticket futur si nécessaire.

### Tests

`tests/test_security_headers.py` couvre 44 cas :
- CSP logique (build_csp_header) : 11 tests unitaires sans serveur
- HSTS : 3 tests E2E
- Permissions-Policy : 5 tests E2E
- Headers sur 404 : 6 tests E2E
- Headers sur redirection 302 : 6 tests E2E
- Headers sur fichiers statiques : 7 tests E2E
- Valeurs CSP et Referrer-Policy : 5 tests E2E

## Uploads et médias — Sécurité

### Architecture

Tout fichier uploadé transite par la chaîne : `validate_upload_metadata()` → `save_bytes()` → `normalize_media_path()`. Chaque étape est indépendante et peut échouer sans laisser d'état partiel.

### Racine contrôlée

La racine absolue `storage/uploads/` est définie par `UPLOAD_ROOT` dans `config.py`. Tout accès au système de fichiers (lecture, écriture, suppression) passe par `os.path.commonpath()` pour vérifier le confinement. Les chemins persistés en base sont **toujours relatifs** à cette racine.

### Anti-path-traversal (`normalize_media_path`)

Chemins refusés :
- Absolus Unix : `/etc/passwd`
- Absolus Windows : `C:\Windows\…` ou `\\server\share\…`
- URLs : `https://…`, `http://…`, `file://…`
- Traversals : `../secret`, `images/../../secret`
- Null byte : `images/\x00photo.jpg`
- Schémas URI quelconques

Les chemins encodés `%2e%2e` ne sont **pas** URL-décodés — ils sont traités comme des noms de fichiers littéraux (inaccessibles via le filesystem standard).

### Extensions — liste blanche

Par défaut : `jpg`, `jpeg`, `png`, `webp`, `pdf`. Refusées (non dans la liste) : `.php`, `.py`, `.html`, `.js`, `.svg`, `.sh`, `.exe`, `.env`, etc.

La validation porte sur la **dernière extension** du fichier. `photo.php.jpg` est accepté si `.jpg` est autorisé — limite documentée. `photo.jpg.php` est refusé car `.php` n'est pas autorisé.

### MIME

Le MIME est extrait du `Content-Type` fourni par le client. Les paramètres (`; charset=binary`) sont ignorés. La casse est normalisée. **Limite** : Forge ne vérifie pas la signature binaire du fichier (magic bytes). Un fichier dangereux renommé avec une extension autorisée et un Content-Type valide est accepté. Corriger nécessiterait `python-magic` (hors périmètre).

### Taille

Configurable via `UPLOAD_MAX_SIZE` (défaut : 5 Mo). Fichier vide (0 octet) accepté. Taille négative refusée. La vérification de la `Content-Length` HTTP est faite avant le parsing du body.

### Noms de fichiers

`secure_filename()` retire les chemins (basename uniquement), remplace espaces et caractères spéciaux par `_`, supprime les null bytes. `generate_unique_filename()` ajoute un UUID hex — impossible de prédire ou d'écraser un fichier existant.

### Catégories

Les répertoires de catégorie (`images`, `documents`, `tmp`) sont validés par regex `^[A-Za-z0-9_-]+$`. Toute catégorie contenant `/`, `..`, espace ou caractère spécial est refusée.

### Route /media

GET `/media/<path>` → `_serve_media()` → `serve_media_file()` → `normalize_media_path()` → `media_path_to_storage_path()`. Le path traversal via l'URL est bloqué avant toute lecture de fichier.

### Limites restantes

- Pas de test HTTP multipart réel (cycle POST complet). Ticket futur : `E2E-UPLOAD-HTTP-001`.
- Pas de validation de la signature binaire (magic bytes). Limit MIME spoofing documentée.
- Pas de rate limit sur les uploads (DoS upload). Ticket futur si nécessaire.
- Pas de scan antivirus intégré.

### Tests

`tests/test_security_uploads_audit.py` : 65 tests sécurité ciblés.
`tests/test_uploads.py` + `tests/test_media_route.py` : couverture fonctionnelle existante.
