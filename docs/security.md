# Sécurité et RBAC

!!! tip "Guide production"
    Pour les bonnes pratiques de déploiement sécurisé (checklist, secrets, HTTPS,
    cookies, headers, CSRF, RBAC, uploads, logs), voir
    **[Sécurité en production](production-security.md)**.

!!! info "Auth/User avancée"
    Pour l'authentification complète (login, MFA, OIDC, sessions, audit, CLI admin),
    voir **[Authentification Forge](auth.md)**.

## Socle de sécurité

Forge fournit les briques de sécurité suivantes dans `core/security/` :

| Brique | Fichier | Rôle |
|---|---|---|
| Sessions | `session.py` | Création, rotation, expiration, stockage en mémoire |
| Hachage | `hashing.py` | PBKDF2-HMAC-SHA256, rate limiting sur `/login` |
| Décorateurs | `decorators.py` | `@require_auth`, `@require_csrf`, `@require_role` (déprécié) |
| Middleware | `middleware.py` | `AuthMiddleware`, `CsrfMiddleware` |
| Nonce CSP | `csp.py` | Nonce par requête pour scripts inline contrôlés (`APP_CSP_NONCE_ENABLED`) |

Le RBAC complet (`Role`, `Permission`, `@require_permission`, `make_can`…) est fourni par le module opt-in `forge-mvc-rbac` — il n'y a pas de `rbac.py` dans `core/security/`. Voir [RBAC — Contrôle d'accès](rbac.md).

### TLS du serveur de développement

Le serveur HTTPS intégré à Forge impose explicitement **TLS 1.2 minimum** (`ssl.TLSVersion.TLSv1_2`). Il est destiné au développement local, à la pédagogie et aux tests — pas à la production.

**En production, TLS doit être terminé par Nginx** ou un reverse proxy équivalent. Forge écoute en HTTP local derrière Nginx.

### Nonce CSP

Forge inclut par défaut l'en-tête `Content-Security-Policy` avec `script-src 'self'`. Pour autoriser des scripts inline contrôlés sans affaiblir la CSP avec `unsafe-inline`, activez le mécanisme de nonce :

```dotenv
APP_CSP_NONCE_ENABLED=true
```

```html
<script nonce="{{ csp_nonce() }}">/* script inline autorisé */</script>
```

`unsafe-inline` n'est jamais ajouté automatiquement. Voir [référence API](reference/api.md#coresecurity) pour les détails.

---

## En-têtes de sécurité

Forge applique des en-têtes HTTP de sécurité par défaut sur toutes les réponses (200, 302, 404, fichiers statiques, erreurs). Ces en-têtes sont des garde-fous par défaut — ils ne remplacent pas une configuration de déploiement complète.

### Contrat actuel

| En-tête | Rôle | Valeur | Limite |
|---|---|---|---|
| `X-Frame-Options` | Protection clickjacking | `DENY` | Complété par `frame-ancestors 'none'` en CSP |
| `X-Content-Type-Options` | Blocage MIME sniffing | `nosniff` | — |
| `Strict-Transport-Security` | Forcer HTTPS (HSTS) | `max-age=31536000; includeSubDomains` | Émis même en HTTP local ; la protection réelle requiert HTTPS côté reverse proxy |
| `Referrer-Policy` | Contrôle du referrer | `strict-origin-when-cross-origin` | — |
| `Content-Security-Policy` | Restriction des sources | Voir section CSP | Ne remplace pas une revue des templates |
| `Permissions-Policy` | Restriction des API navigateur | `camera=(), microphone=(), geolocation=(), payment=()` | Ne couvre pas toutes les API navigateur |

### CSP

La valeur par défaut :

```
default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:;
frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'
```

`unsafe-inline` et `unsafe-eval` ne sont jamais ajoutés automatiquement. Pour les scripts inline contrôlés, activer le nonce par requête (`APP_CSP_NONCE_ENABLED=true` — voir section Nonce CSP ci-dessus).

### HSTS

Forge émet `Strict-Transport-Security` sur toutes les réponses, y compris en HTTP local. En développement, cet en-tête est inoffensif mais techniquement redondant. **En production, HTTPS doit être terminé par Nginx** ou un reverse proxy équivalent.

### Limites

Ces en-têtes ne remplacent pas :

- la configuration HTTPS et TLS du reverse proxy ;
- une revue de sécurité des templates applicatifs ;
- une politique de déploiement sécurisé complète (voir [Sécurité en production](production-security.md)).

Forge ne promet pas une sécurité complète par défaut. Les en-têtes fournis sont des garde-fous raisonnables, testés et verrouillés comme contrat public (`SECURITY-HEADERS-DOC-LOCK-001`).

### Ce que Forge n'émet pas encore

- `Cross-Origin-Resource-Policy` et `Cross-Origin-Opener-Policy` ne sont pas émis par défaut.
- `Permissions-Policy` ne liste pas toutes les API navigateur disponibles.

---

## Service de fichiers — défense symlinks (UPLOADS-SYMLINK-DEFENSE-001)

Les fichiers publics servis par Forge (route `/static/...` par `app.py`, route
`/media/...` via [`core.uploads.serve_media_file`](https://github.com/caucrogeGit/Forge/blob/main/core/uploads/manager.py))
**ne doivent pas traverser de symlinks**. Les chemins sont résolus via
`os.path.realpath()` / `Path.resolve()` puis vérifiés par `os.path.commonpath()` :
toute cible résolue hors de la racine autorisée (`static/`, `storage/uploads/`)
fait échouer le check et la requête retourne `403` (statics) ou `404` (media).

Cette défense couvre :

- les symlinks **fichier** dans `static/` ou `storage/uploads/` pointant
  vers un fichier hors racine (`/etc/passwd`, etc.) ;
- les symlinks **répertoire** intermédiaires dans le chemin demandé
  (`uploads/dir_link/secret.txt` où `dir_link → /tmp/secret_dir`) ;
- les `..` classiques de path traversal.

Le contrat est verrouillé par
[`tests/test_uploads_symlink_defense_001.py`](https://github.com/caucrogeGit/Forge/blob/main/tests/test_uploads_symlink_defense_001.py)
(12 tests, dont 3 garde-fous source-level sur `app.py`).

---

## RBAC — documentation complète

La documentation complète du RBAC Forge (rôles, permissions, décorateurs,
helper Jinja, génération CRUD, chaîne de confiance) se trouve dans
**[RBAC — Contrôle d'accès](rbac.md)**.

### Résumé rapide

```python
from forge_mvc_rbac import require_permission, has_permission, make_can

# Protéger une route serveur
@staticmethod
@require_permission("posts.edit")
def edit(request): ...

# Vérifier une permission dans le code
if has_permission(request, "posts.edit"):
    ...

# Helper Jinja — injecté automatiquement par BaseController.render(request=request)
# {% if can("posts.edit") %} ... {% endif %}
```

Injecter les permissions après authentification :

```python
utilisateur = {
    "UtilisateurId": row["id"],
    "Login": row["login"],
    "roles": ["admin"],
    "permissions": ["posts.edit", "posts.delete", "users.view"],
}
nouveau_id = authentifier_session(session_id, utilisateur)
```

---

## Store de session configurable

Forge accepte un store de session explicite via :

```python
import core.forge as forge
forge.configure(session_store=my_store)
```

Le store doit implémenter le protocole `SessionStore` (`core.sessions.contract`) :
`create`, `get`, `set`, `replace`, `delete`, `regenerate`, `authenticate`,
`touch_expiry`, `set_flash`, `get_flash`.

Le store par défaut est `MemorySessionStore` (mono-processus, sessions perdues au
redémarrage). Passer `None` réinitialise à ce comportement par défaut.

Trois backends sont disponibles dans `core.sessions` :
`MemorySessionStore`, `FileSessionStore`, `MariaDbSessionStore`.
Leur documentation complète est traitée dans le ticket SESSIONS-STORE-CONTRACT-DOC-001.

---

## Ce que Forge ne fait pas

- Pas d'ORM complet pour les permissions.
- Pas de gestion automatique des politiques (`deny by default` reste à l'application).
- Pas de cache de permissions distribué.
- Pas de hiérarchie de rôles automatique.
- Pas de liaison `user ↔ rôle ↔ permission` dans le core (appartient à l'application).
