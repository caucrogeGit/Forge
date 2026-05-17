# Audit — PUBLIC-API-DUPLICATES-SCAN-001

**Ticket** : `PUBLIC-API-DUPLICATES-SCAN-001`  
**Phase** : 8.5 — Clôture Phase 8  
**Date** : 2026-05-17  
**Version auditée** : 1.0.0b3 (commit bf67ad4 + TESTS-BEHAVIOR-FIRST-001)

---

## Objectif

Réaliser un inventaire ciblé des doublons d'API publique dans Forge.

- Identifier les API canoniques, legacy, compatibilité temporaire et doublons.
- Classer chaque cas par statut.
- Proposer des tickets futurs pour les cas qui nécessitent une action.
- Ne pas supprimer ni modifier d'API publique dans ce ticket.

---

## Méthode

### Commandes exécutées

```bash
# Détection des patterns de dépréciation, alias, compatibilité
grep -RInE '__all__|deprecated|DeprecationWarning|legacy|canonical|alias|compat|backward' \
  core/ forge_cli/ packages/

# Inventaire des points d'entrée publics
find core/ forge_cli/ packages/ -name "__init__.py" | sort
cat core/auth/__init__.py
cat core/security/session.py
cat core/security/decorators.py
cat core/security/middleware.py
cat core/security/hashing.py
cat core/auth/session.py
cat core/modules/__init__.py
cat core/mail/__init__.py
cat core/sessions/__init__.py
cat packages/forge-mvc-rbac/forge_mvc_rbac/__init__.py
cat packages/forge-mvc-mfa/forge_mvc_mfa/__init__.py

# Recherche de doublons par famille
grep -RInE 'def (require_role|user_has_role|require_permission|require_user_permission)' core/
grep -RInE 'def (login_required|require_auth|authenticate_user|login_user|logout_user|is_authenticated|current_user)' core/
grep -RInE 'def (hash_password|verify_password|record_attempt|is_rate_limited)' core/
grep -nE 'command\s*==\s*["\x27]' forge.py
```

### Familles examinées

1. Auth / Session
2. CSRF
3. Routes / Modules
4. RBAC (core léger vs opt-in)
5. Hachage / Rate limit
6. Mail
7. CLI
8. Packaging

### Critères de classification

| Statut | Définition |
|---|---|
| `CANONIQUE` | API officielle, seule voie recommandée |
| `LEGACY_DÉPRÉCIÉE` | API conservée avec `DeprecationWarning`, migration documentée |
| `COMPATIBILITÉ_TEMPORAIRE` | Re-export ou pont sans warning, maintenu pour éviter des ruptures immédiates |
| `DOUBLON_DOCUMENTAIRE` | Deux chemins intentionnels documentés (ex. deux niveaux d'abstraction) |
| `DOUBLON_DANGEREUX` | Concurrence non documentée ou risquée |
| `FAUX_POSITIF` | Ressemblance de surface, pas de vrai doublon |
| `À_SURVEILLER` | Pas dangereux maintenant, mais à traiter dans un ticket futur |

### Limites de l'audit

- L'audit couvre `core/`, `forge_cli/`, `packages/` et la documentation publique.
- Les starters (`forge_cli/starters/data/`) ne font pas partie de l'API publique Forge — ils ne sont pas audités comme API.
- Les fonctions privées (préfixe `_`) ne sont pas dans le périmètre.
- L'audit est statique — il ne simule pas de projets applicatifs externes.

---

## Synthèse

| Famille | Statut global | Risque |
|---|---|---|
| Auth / Session | Bien documentée, deprecation en place | Faible |
| CSRF | Une seule implémentation propre | Aucun |
| Routes / Modules | API unifiée, anciens symboles supprimés | Aucun |
| RBAC | Deux niveaux intentionnels documentés | Faible |
| Hachage / Rate limit | Migration documentée, re-exports tracés | Faible |
| Mail | Legacy explicitement labellisée | Faible |
| CLI | Namespace cohérent, pas de doublons | Aucun |
| Packaging | Politique documentée | Aucun |

Aucun doublon dangereux identifié. Deux cas `À_SURVEILLER` : `require_auth` et `require_role` manquent d'un `DeprecationWarning` explicite malgré leur documentation comme legacy.

---

## Familles auditées

### 1. Auth / Session

**API canonique** : `core.auth.session`

Fonctions :
- `authenticate_user(email, password, user_loader)` → `AuthUser | None`
- `login_user(request, user)` → stocke `_auth_user_id` en session
- `logout_user(request)` → retire `_auth_user_id`
- `get_authenticated_user_id(request)` → lit id canonique + pont legacy
- `current_user(request, user_loader)` → charge l'utilisateur
- `is_authenticated(request)` → vérifie `_auth_user_id`
- `login_required(redirect_to=...)` → décorateur

**API legacy** : `core.security.session`

Fonctions avec `DeprecationWarning` :
- `create_session()` → remplacée par `get_session_store().create()`
- `authenticate_session()` → remplacée par `login_user()`
- `is_authenticated()` → remplacée par `core.auth.session.is_authenticated()`
- `get_user()` → remplacée par `current_user()`

Fonctions sans `DeprecationWarning` (utilitaires encore en usage actif) :
- `get_session_id(request)` — utilisée par `CsrfMiddleware`
- `get_session(session_id)` — utilisée par `CsrfMiddleware`
- `delete_session()`, `regenerate_session()`, `set_flash()`, `get_flash()` — utilitaires de session

**Décorateur legacy** : `core.security.decorators`
- `require_auth()` → remplacé par `login_required()` (documenté dans `docs/auth.md`, `docs/deprecation-policy.md`)
- `require_role(role)` → simplifié, remplacé par `forge_mvc_rbac.require_permission` pour les projets RBAC

**Pont de compatibilité** : `get_authenticated_user_id()` reconnaît les sessions legacy (`authenticated + user`) ET les sessions canoniques (`_auth_user_id`). Bididrectionnel depuis AUTH-SESSION-COMPATIBILITY-BRIDGE-001.

**État des constats tracker** : FND-AUTH-001 FERMÉ, FND-AUTH-002 FERMÉ.

---

### 2. CSRF

**API canonique** :
- `core.security.middleware.CsrfMiddleware.check(request)` — vérification central-time
- `core.security.decorators.require_csrf` — décorateur, délègue à `CsrfMiddleware.check()`

Pas de concurrence ni de doublon. `require_csrf` est un wrapper propre sur le middleware.

---

### 3. Routes / Modules

**API canonique** :
- `core.modules.generate_module_routes(name, registry_path, dry_run)` → `ModuleRouteGenerationResult`

Anciens symboles supprimés (ticket MODULE-ROUTES-INJECTION-REMOVE-001) :
- `prepare_module_route_injection` ❌ supprimée
- `_build_injection_block` ❌ supprimée
- `_module_marker` ❌ supprimée
- `MODULE_ROUTES_FILE` ❌ retirée de l'API publique
- `ModuleRoutesAlreadyInjectedError` ❌ supprimée

Constat tracker FND-MODULE-002 FERMÉ.

---

### 4. RBAC

**Deux niveaux intentionnels (documentés dans `docs/production-security.md`)** :

Niveau 1 — Core léger (projets simples) :
- `core.security.decorators.require_role(role)` — vérifie un rôle en session
- `core.security.session.user_has_role(request, role)` — helper interne

Niveau 2 — Opt-in complet (`forge-mvc-rbac`) :
- `require_permission(code)` — décorateur par permission
- `require_user_permission(code)` — décorateur auth + permission
- `auth_user_can(request, code)` — helper programmatique
- `has_permission(user_permissions, code)` — logique pure
- `can(code)` — helper Jinja2

Les deux niveaux co-existent pour des cas d'usage différents. Ce n'est pas un doublon accidentel — c'est un choix architectural documenté (principe "noyau minimal, briques opt-in").

---

### 5. Hachage / Rate limit

**Hachage** :

| Fonction | Module | Statut |
|---|---|---|
| `hash_password(password)` | `core.auth.password` | CANONIQUE (Argon2id) |
| `verify_password(password, hash)` | `core.auth.password` | CANONIQUE (Argon2id) |
| `password_needs_rehash(hash)` | `core.auth.password` | CANONIQUE |
| `verify_password_legacy(password, hash)` | `core.security.hashing` | LEGACY — vérification PBKDF2 uniquement, lecture seule, labellisée |
| `pbkdf2_needs_rehash(hash)` | `core.security.hashing` | LEGACY — toujours True, signal de migration |

**Rate limit** — re-exports dans `core.security.hashing` :

| Nom re-exporté | Nom canonique | Module canonique |
|---|---|---|
| `record_attempt` | `record_login_attempt` | `core.auth.rate_limit` |
| `is_rate_limited` | `is_login_rate_limited` | `core.auth.rate_limit` |
| `MAX_ATTEMPTS` | `LOGIN_MAX_ATTEMPTS` | `core.auth.rate_limit` |
| `RATE_LIMIT_WINDOW` | `LOGIN_RATE_LIMIT_WINDOW` | `core.auth.rate_limit` |

Les re-exports sont documentés dans le module (`HASHING-RATELIMIT-MOVE-001`). Ils maintiennent la compatibilité pour les starters et tests qui importaient depuis `core.security.hashing`.

---

### 6. Mail

| API | Module | Statut |
|---|---|---|
| `Mailer + SmtpTransport` | `core.mail` | CANONIQUE depuis Forge 1.2 |
| `SMTPMailer` | `core.mail.smtp` | LEGACY — docstring : "conservé pour compatibilité ascendante" |

Les deux sont exportés depuis `core.mail.__init__`. `SMTPMailer` n'émet pas de `DeprecationWarning` mais son label legacy est explicite dans la docstring du module.

---

### 7. CLI

Namespace cohérent `namespace:action`. Doublons apparents examinés :

| Commande A | Commande B | Décision |
|---|---|---|
| `forge doctor` | `forge project:check` | FAUX_POSITIF — diagnostics différents : `doctor` = complet (env, DB, SSL, i18n…), `project:check` = structure projet |
| `forge doctor` | `forge auth:doctor` | FAUX_POSITIF — `auth:doctor` est spécifique au sous-système auth |
| `forge doctor` | `forge mail:doctor` | FAUX_POSITIF — `mail:doctor` est spécifique au sous-système mail |
| `forge project:check` | `forge project:audit` | FAUX_POSITIF — `project:audit` est distinct (audit de sécurité) |

Pas de commandes dupliquées. Le pattern `forge doctor` pour le diagnostic global et `forge <ns>:doctor` pour les sous-systèmes est cohérent.

---

### 8. Packaging

| Paquet | Publication | Statut |
|---|---|---|
| `forge-mvc` | PyPI (publié) | CANONIQUE |
| `forge-mvc-mfa` | Source-only | Pre-Alpha — ticket SEC-MFA-SECRET-ENCRYPTION-001 requis avant publication |
| `forge-mvc-rbac` | Source-only | Publiable à beta.5 |
| `forge-mvc-workflow` | Source-only | Publiable à beta.5 |
| `forge-mvc-stats` | Source-only | Publiable à beta.5 |

Politique documentée dans `docs/release-policy.md` (OPTIN-PACKAGES-PUBLICATION-POLICY-001). FND-PKG-001 FERMÉ.

---

## Doublons acceptés

| Famille | API A | API B | Statut | Décision |
|---|---|---|---|---|
| Auth / Session | `core.auth.session.login_required` | `core.security.decorators.require_auth` | LEGACY_DÉPRÉCIÉE | `require_auth` documentée comme legacy dans `docs/auth.md` et `docs/deprecation-policy.md` |
| Auth / Session | `core.auth.session.is_authenticated` | `core.security.session.is_authenticated` | LEGACY_DÉPRÉCIÉE | `core.security.session.is_authenticated` émet `DeprecationWarning` |
| Hachage | `core.auth.password.verify_password` | `core.security.hashing.verify_password_legacy` | LEGACY_DÉPRÉCIÉE | Usage documenté pour migration PBKDF2 → Argon2id |
| Mail | `Mailer + SmtpTransport` | `SMTPMailer` | LEGACY_DÉPRÉCIÉE | `SMTPMailer` labellisée explicitement dans sa docstring |
| Rate limit | `core.auth.rate_limit.record_login_attempt` | `core.security.hashing.record_attempt` | COMPATIBILITÉ_TEMPORAIRE | Re-export documenté (HASHING-RATELIMIT-MOVE-001) |
| RBAC | `core.security.decorators.require_role` | `forge_mvc_rbac.require_permission` | DOUBLON_DOCUMENTAIRE | Deux niveaux intentionnels — core léger vs opt-in complet |

---

## Doublons legacy documentés

| Famille | API legacy | API canonique | Documentation |
|---|---|---|---|
| Auth | `authenticate_session()` | `login_user()` | `docs/auth.md`, `docs/deprecation-policy.md` |
| Auth | `get_user()` | `current_user()` | `docs/auth.md` |
| Auth | `create_session()` | `get_session_store().create()` | `docs/auth.md` |
| Auth | `is_authenticated()` (security.session) | `is_authenticated()` (auth.session) | `docs/auth.md` |
| Hachage | `verify_password_legacy()` | `verify_password()` | Docstring du module, ticket HASHING-PBKDF2-REMOVE-001 |
| Mail | `SMTPMailer` | `Mailer + SmtpTransport` | Docstring du module smtp.py |

---

## Doublons dangereux ou ambigus

Aucun doublon dangereux identifié.

---

## Faux positifs

| Entrée examinée | Raison du faux positif |
|---|---|
| `forge doctor` vs `forge project:check` | Diagnostics différents, pas de recouvrement de responsabilités |
| `forge_mvc_rbac.require_permission` vs `core.security.decorators.require_role` | Deux niveaux d'abstraction intentionnels, documentés |
| `core.modules` — noms alias dans la génération de routes | `alias` est une variable locale de génération, pas une API publique |
| `AUTH_EVENT_MFA_*` dans `core.auth.audit` | Événements d'audit core légitimes — MFA extrait mais les constantes d'audit restent dans core |

---

## Recommandations

### R1 — Ajouter `DeprecationWarning` à `require_auth` et `require_role`

**Priorité** : Basse  
**Contexte** : Ces deux décorateurs sont documentés comme legacy dans `docs/auth.md` et `docs/deprecation-policy.md`, mais n'émettent pas de `DeprecationWarning`. Les utilisateurs qui les importent n'ont pas de signal programmatique.  
**Action** : Ajouter des warnings dans `core/security/decorators.py`.

### R2 — Supprimer ou déprécier `SMTPMailer`

**Priorité** : Basse  
**Contexte** : `SMTPMailer` est labellisée "legacy" mais reste dans `core.mail.__init__`. Un `DeprecationWarning` à l'instanciation signalerait la migration vers `Mailer + SmtpTransport`.  
**Action** : Ajouter warning ou retirer de l'API publique dans un ticket futur.

### R3 — Consolider les utilitaires de session dans `core.security.session`

**Priorité** : Très basse  
**Contexte** : `get_session_id()`, `get_session()`, `set_flash()`, `get_flash()` ne sont pas dépréciées mais sont dans le module legacy `core.security.session`. Elles sont utilisées par `CsrfMiddleware`.  
**Action** : Évaluer si ces utilitaires méritent un module propre (`core.sessions.http`) ou si la dépendance sur `core.security.session` doit rester pour la session 1.0.x.

---

## Tickets futurs suggérés

| Ticket suggéré | Famille | Description | Priorité |
|---|---|---|---|
| `SECURITY-DECORATORS-DEPRECATE-001` | Auth / Session | Ajouter `DeprecationWarning` à `require_auth` et `require_role` dans `core.security.decorators` | Basse |
| `SMTP-MAILER-DEPRECATE-001` | Mail | Ajouter `DeprecationWarning` à `SMTPMailer.__init__` | Très basse |
| `SESSION-UTILITIES-RELOCATE-001` | Sessions | Évaluer le déplacement de `get_session_id`, `get_session`, `set_flash`, `get_flash` hors de `core.security.session` | Très basse |

Ces tickets sont des suggestions. Ils ne sont pas ouverts dans la roadmap dans ce ticket d'audit.

---

## Table de classification complète

| Famille | API A | API B | Statut | Décision | Ticket futur |
|---|---|---|---|---|---|
| Auth | `core.auth.session.login_required` | `core.security.decorators.require_auth` | `À_SURVEILLER` | Documentée legacy mais sans warning programmatique | `SECURITY-DECORATORS-DEPRECATE-001` |
| Auth | `core.auth.session.is_authenticated` | `core.security.session.is_authenticated` | `LEGACY_DÉPRÉCIÉE` | Warning en place, pont bidirectionnel | — |
| Auth | `core.auth.session.current_user` | `core.security.session.get_user` | `LEGACY_DÉPRÉCIÉE` | Warning en place | — |
| Auth | `get_session_store().create()` | `core.security.session.create_session` | `LEGACY_DÉPRÉCIÉE` | Warning en place | — |
| Auth | `core.auth.session.login_user` | `core.security.session.authenticate_session` | `LEGACY_DÉPRÉCIÉE` | Warning en place | — |
| Auth | `core.security.decorators.require_role` | (voir RBAC) | `À_SURVEILLER` | Pas de warning, documenté legacy | `SECURITY-DECORATORS-DEPRECATE-001` |
| CSRF | `CsrfMiddleware.check` | `require_csrf` | `CANONIQUE` | Pas de doublon — wrapper propre | — |
| Modules | `generate_module_routes` | (anciens symboles supprimés) | `FAUX_POSITIF` | API unifiée, aucun concurrent | — |
| RBAC | `core.security.decorators.require_role` | `forge_mvc_rbac.require_permission` | `DOUBLON_DOCUMENTAIRE` | Deux niveaux intentionnels | — |
| Hachage | `core.auth.password.hash_password` | `core.security.hashing.verify_password_legacy` | `FAUX_POSITIF` | Fonctions différentes (création vs vérification legacy) | — |
| Hachage | `core.auth.password.verify_password` | `core.security.hashing.verify_password_legacy` | `LEGACY_DÉPRÉCIÉE` | Usage PBKDF2 pour migration uniquement, labellisé | `HASHING-PBKDF2-DEFINITIVE-REMOVE-001` |
| Rate limit | `core.auth.rate_limit.record_login_attempt` | `core.security.hashing.record_attempt` | `COMPATIBILITÉ_TEMPORAIRE` | Re-export tracé (HASHING-RATELIMIT-MOVE-001) | — |
| Mail | `Mailer + SmtpTransport` | `SMTPMailer` | `À_SURVEILLER` | Labellisée legacy mais sans warning | `SMTP-MAILER-DEPRECATE-001` |
| CLI | `forge doctor` | `forge project:check` | `FAUX_POSITIF` | Diagnostics différents | — |
| Packaging | core vs opt-ins | — | `CANONIQUE` | Politique documentée | — |

---

## Conclusion

L'audit de PUBLIC-API-DUPLICATES-SCAN-001 révèle que Forge est dans un état sain sur la question des doublons d'API publique :

- Les **doublons légitimes** (legacy avec migration) sont tous documentés et, pour la plupart, signalés par des `DeprecationWarning`.
- Les **deux niveaux RBAC** sont un choix architectural documenté.
- Les **anciens symboles de modules** ont été correctement supprimés.
- Les **CLI** suivent un namespace cohérent sans recouvrement de responsabilités.

**Deux cas `À_SURVEILLER`** : `require_auth` et `require_role` dans `core.security.decorators` manquent d'un `DeprecationWarning` malgré leur documentation comme legacy. Ce n'est pas dangereux mais c'est un signal programmatique absent. Des tickets futurs ciblés (`SECURITY-DECORATORS-DEPRECATE-001`, `SMTP-MAILER-DEPRECATE-001`) pourront combler ces lacunes dans une phase ultérieure.

Aucune action immédiate requise. La Phase 8 peut être considérée comme clôturée.
