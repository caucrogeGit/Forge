# Audit — BASE-CONTROLLER-SURFACE-AUDIT-001

## Objectif

Réaliser un audit ciblé de la surface publique de `BaseController`
(`core/mvc/controller/base_controller.py`) pour :

- identifier clairement quelles méthodes sont canoniques, legacy ou à surveiller ;
- détecter les dépendances encore présentes vers l'API dépréciée `core.security.session` ;
- préparer la documentation officielle de l'API (ticket `BASE-CONTROLLER-API-DOC-001`) ;
- lister les tickets futurs nécessaires.

Cet audit ne modifie aucun fichier runtime.

---

## Méthode

Commandes exécutées :

```bash
grep -RInE 'class BaseController|def |current_user|is_authenticated|get_user|get_session|session|flash|redirect|render|json|response|request|core\.security\.session|core\.auth\.session' \
  core/mvc mvc/controllers forge_cli/starters tests docs

# Lecture directe du fichier source
cat core/mvc/controller/base_controller.py
cat core/security/session.py        # fonctions importées par BaseController
cat core/mvc/controller/registry.py # fournisseurs Jinja2
```

Fichiers audités :

- `core/mvc/controller/base_controller.py` — source principale
- `core/security/session.py` — module importé par BaseController
- `core/mvc/controller/registry.py` — fournisseurs de contexte Jinja
- `mvc/controllers/` — contrôleurs générés dans l'application référence
- `forge_cli/starters/data/*/files/mvc/controllers/` — contrôleurs des starters

---

## Synthèse

`BaseController` expose **18 méthodes statiques**. Toutes sont canoniques à
l'exception de `current_user()` qui délègue à l'API dépréciée `get_user()`
de `core.security.session`.

Le fichier importe quatre symboles de `core.security.session` :

| Symbole importé | Statut dans core.security.session |
|---|---|
| `get_session_id` | **Non déprécié** |
| `get_session` | **Non déprécié** |
| `set_flash` | **Non déprécié** |
| `get_user` | **Déprécié** — `DeprecationWarning` émis |

Le seul risque immédiat est `current_user()` → `get_user()`.
Les trois autres symboles sont stables dans leur module legacy actuel mais
restent à surveiller si ce module est supprimé à terme.

---

## Surface publique de BaseController

| Méthode | Rôle | Statut | Dépendances internes | Décision |
|---|---|---|---|---|
| `render()` | Génère une réponse HTML via Jinja2 | CANONIQUE | `csrf_token()`, registry Jinja | À documenter |
| `redirect()` | Génère une réponse 302 | CANONIQUE | `set_flash()` (optionnel) | À documenter |
| `redirect_with_flash()` | POST-Redirect-GET avec message flash | CANONIQUE | `set_flash()`, `redirect()` | À documenter |
| `redirect_to_route()` | Redirige via une route nommée | CANONIQUE | router via `_cfg("router")` | À documenter |
| `not_found()` | Génère une réponse 404 | CANONIQUE | aucune | À documenter |
| `bad_request()` | Génère une réponse 400 | CANONIQUE | aucune | À documenter |
| `forbidden()` | Génère une réponse 403 | CANONIQUE | aucune | À documenter |
| `validation_error()` | Génère une réponse 422 | CANONIQUE | `render()` | À documenter |
| `server_error()` | Génère une réponse 500 | CANONIQUE | aucune | À documenter |
| `set_flash()` | Stocke un message flash en session | CANONIQUE | `core.security.session.set_flash`, `get_session_id` | À surveiller |
| `csrf_token()` | Retourne le token CSRF de la session | CANONIQUE | `core.security.session.get_session_id`, `get_session` | À surveiller |
| `current_user()` | Retourne l'utilisateur courant en session | LEGACY | `core.security.session.get_user` — **déprécié** | À migrer |
| `include()` | Rendu d'un partial Jinja2 | CANONIQUE | `template_manager` | À documenter |
| `json()` | Génère une réponse JSON | CANONIQUE | aucune | À documenter |
| `body()` | Extrait les données POST (dict plat) | CANONIQUE | `request.body` | À documenter |
| `json_body()` | Extrait le body JSON parsé | CANONIQUE | `request.json_body` | À documenter |
| `render_form()` | Raccourci render + form_context | CANONIQUE | `form_context()`, `render()` | À documenter |
| `form_context()` | Construit le contexte d'un formulaire | CANONIQUE | `csrf_token()` | À documenter |

---

## Méthodes canoniques

Les 17 méthodes suivantes sont canoniques — elles ne dépendent pas d'une
API dépréciée et sont utilisées directement dans les starters et l'application
de référence :

`render`, `redirect`, `redirect_with_flash`, `redirect_to_route`, `not_found`,
`bad_request`, `forbidden`, `validation_error`, `server_error`, `set_flash`,
`csrf_token`, `include`, `json`, `body`, `json_body`, `render_form`,
`form_context`.

Note : `set_flash()` et `csrf_token()` importent depuis `core.security.session`
des fonctions non-dépréciées (`get_session_id`, `get_session`, `set_flash`).
Ces fonctions sont stables mais vivent dans un module qui a été partiellement
déprécié. Elles sont classées À_SURVEILLER.

---

## Méthodes legacy ou à surveiller

### `current_user()` — LEGACY / À_MIGRER

```python
@staticmethod
def current_user(request):
    """Retourne l'utilisateur courant stocké en session."""
    return get_user(request)
```

- Délègue à `core.security.session.get_user(request)`.
- `get_user()` émet un `DeprecationWarning` :
  ```
  core.security.session.get_user() is deprecated;
  use core.auth.session.current_user(request, user_loader) instead.
  ```
- L'API canonique est `core.auth.session.current_user(request, user_loader)` qui
  requiert un `user_loader(user_id) -> AuthUser | dict` applicatif.
- `BaseController.current_user()` est **absent de tous les starters** après 9.1.
- Elle **n'est pas utilisée** dans les contrôleurs générés `mvc/controllers/`.
- Elle est exposée mais non utilisée dans le code actif — c'est une méthode
  orpheline qui émet des warnings si appelée.

Ticket futur suggéré : `BASE-CONTROLLER-CURRENT-USER-MIGRATE-001`.

### `set_flash()` / `csrf_token()` — À_SURVEILLER

Ces méthodes utilisent `get_session_id` et `get_session` depuis
`core.security.session`. Ces fonctions spécifiques **ne sont pas dépréciées**,
mais elles vivent dans le module legacy. Elles resteront stables tant que ce
module n'est pas supprimé.

Si `core.security.session` devait être supprimé à terme, ces méthodes
nécessiteraient une migration vers `core.sessions.manager`.

---

## Usages dans les contrôleurs

### `mvc/controllers/` (application de référence)

| Contrôleur | Méthodes BaseController utilisées |
|---|---|
| `home_controller.py` | `render()` |
| `auth_controller.py` | `render()`, `redirect()` |
| `mfa_challenge_controller.py` | `render()`, `redirect()` |

Point à surveiller : `mvc/controllers/mfa_challenge_controller.py` importe
`authenticate_session` depuis `core.security.session` — API dépréciée.
Ce n'est pas une méthode de `BaseController` mais un import direct dans le
contrôleur applicatif. Ticket futur suggéré : `MVC-MFA-CHALLENGE-MIGRATE-001`.

### Jinja context providers (pattern opt-in)

`render()` itère sur les fournisseurs de contexte enregistrés via
`register_jinja_context_provider()`. Le module `forge-mvc-rbac` enregistre
`make_auth_jinja_context_with_can` qui injecte `current_user`, `is_authenticated`
et `can` dans le contexte Jinja. Ce mécanisme est **canonique** et ne passe pas
par `BaseController.current_user()`.

---

## Usages dans les starters

| Starter | Méthodes utilisées | Méthodes absentes |
|---|---|---|
| `utilisateurs-auth` | `render()`, `redirect()` | `current_user()`, `set_flash()`, `not_found()` |
| `suivi-comportement-eleves` | `render()`, `redirect()`, `not_found()`, `csrf_token()` | `current_user()` |
| `carnet-contacts` | `render()`, `redirect()`, `not_found()`, `validation_error()`, `csrf_token()` | `current_user()` |
| `communes-sejours` | `render()`, `redirect()`, `not_found()`, `validation_error()`, `redirect_with_flash()` | `current_user()` |
| `auth-mfa` | `render()`, `redirect()` | `current_user()` |

**`BaseController.current_user()` n'est utilisée dans aucun starter.**

Les starters post-9.1 utilisent directement `get_authenticated_user_id(request)`
depuis `core.auth.session`, suivi de `get_user_by_id(user_id)` depuis le modèle.
C'est le pattern canonique recommandé.

---

## Risques identifiés

| Élément | Risque | Statut | Ticket futur |
|---|---|---|---|
| `BaseController.current_user()` | Appelle `get_user()` déprécié, émet `DeprecationWarning` si utilisée | LEGACY / À_MIGRER | `BASE-CONTROLLER-CURRENT-USER-MIGRATE-001` |
| Import `get_user` dans BaseController | Risque si le module `core.security.session` est allégé | À_SURVEILLER | Inclus dans ticket ci-dessus |
| `mvc/controllers/mfa_challenge_controller.py` | Appelle `authenticate_session()` déprécié directement | À_MIGRER | `MVC-MFA-CHALLENGE-MIGRATE-001` |
| `set_flash()` / `csrf_token()` via `core.security.session` | Non-déprécié actuellement, mais module legacy | À_SURVEILLER | À réévaluer si module legacy est supprimé |

Aucun risque bloquant pour la documentation ou la publication.
`BaseController.current_user()` étant inutilisée dans le code actif et les
starters, elle n'affecte pas le runtime en l'état.

---

## Recommandations

**R1** — Documenter l'API dans `BASE-CONTROLLER-API-DOC-001` en excluant
`current_user()` de la liste des méthodes recommandées, ou en la documentant
explicitement comme dépréciée.

**R2** — Ouvrir `BASE-CONTROLLER-CURRENT-USER-MIGRATE-001` après
`BASE-CONTROLLER-API-DOC-001` pour migrer `current_user()` vers
`core.auth.session.current_user(request, user_loader)`. La difficulté est que
la signature canonique requiert un `user_loader` applicatif — cette migration
change l'interface publique et doit être versionnée.

**R3** — Ouvrir `MVC-MFA-CHALLENGE-MIGRATE-001` pour migrer
`mvc/controllers/mfa_challenge_controller.py` de `authenticate_session()` vers
`login_user()` + `regenerate()` (même pattern que le starter auth-mfa normalisé
en 9.1).

---

## Tickets futurs suggérés

| Ticket | Description | Priorité |
|---|---|---|
| `BASE-CONTROLLER-CURRENT-USER-MIGRATE-001` | Migrer `BaseController.current_user()` de `get_user()` vers `core.auth.session.current_user(request, user_loader)` | Après 10.2 |
| `MVC-MFA-CHALLENGE-MIGRATE-001` | Migrer `mvc/controllers/mfa_challenge_controller.py` de `authenticate_session()` vers `login_user()` + `regenerate()` | Après 10.2 |

Ces tickets ne sont pas ouverts dans cette phase.

---

## Conclusion

`BaseController` est dans un état sain : 17 méthodes canoniques sur 18.
Le seul point de migration est `current_user()` qui appelle une API dépréciée
mais est inutilisée dans le code actif. La documentation (10.2) peut présenter
les 17 méthodes canoniques et signaler la situation de `current_user()`.
Aucun blocage pour la documentation officielle ni pour la publication de beta.4.
