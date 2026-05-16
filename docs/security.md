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
| Décorateurs | `decorators.py` | `@require_auth`, `@require_csrf`, `@require_role` |
| Autorisation | `rbac.py` | `@require_permission`, `has_permission`, `get_request_permissions`, `make_can` |
| Middleware | `middleware.py` | `AuthMiddleware`, `CsrfMiddleware` |
| RBAC | `rbac.py` | Modèles `Role`, `Permission`, normalisation, validation |
| Nonce CSP | `csp.py` | Nonce par requête pour scripts inline contrôlés (`APP_CSP_NONCE_ENABLED`) |

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
