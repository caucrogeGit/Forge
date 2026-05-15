# ADR-001 — Stratégie d'authentification Forge 2.x

!!! warning "ADR historique — Forge 2.x"

    Cet ADR documente la stratégie d'authentification telle qu'elle a été décidée
    pour Forge 2.x. Son contenu est conservé pour trace décisionnelle et n'est
    **pas** mis à jour pour refléter l'état actuel de Forge 3.0.

    Pour l'état actuel, consulter :

    - [`docs/auth.md`](../auth.md) — documentation utilisateur d'authentification
    - [ADR-004 — Périmètre du noyau](004-core-perimeter.md) — séparation core/modules opt-in

    Les références à des modules `core.security.rbac`, `core.auth.mfa`, etc.
    dans cet ADR sont **historiques** (modules extraits en `forge-mvc-rbac`,
    `forge-mvc-mfa`, etc. depuis Forge 2.5).

## Statut

Acceptée (Forge 2.x — historique)

---

## Contexte

Forge 1.x a introduit `core/security/` comme premier socle d'authentification :
hachage PBKDF2, sessions nommées en français, décorateurs `require_auth`/`require_csrf`,
RBAC générique (`Role`, `Permission`).

À partir de la Phase 4.5, Forge a développé `core/auth/` comme pile moderne :
Argon2id, `AuthUser`, sessions typées, `@login_required`, MFA TOTP, OIDC, RBAC utilisateur,
audit, rate limiting, tokens génériques, vérification email, reset mot de passe, codes de
récupération, helpers Jinja.

À la sortie de Forge 2.0.0, les deux piles coexistent :

- `core.auth` expose l'API officielle complète pour les nouveaux projets.
- `core.security` contient des briques fonctionnelles encore utilisées par certains
  contrôleurs MVC générés (`mvc/controllers/auth_controller.py`,
  `mvc/controllers/mfa_challenge_controller.py`, `mvc/helpers/flash.py`).

Cette coexistence crée une incohérence : des flux générés par la CLI Auth utilisent
Argon2id via `core.auth.password`, alors que `mvc/controllers/auth_controller.py`
continue à appeler `core.security.hashing.verifier_mot_de_passe` (PBKDF2).

En résumé : core.auth est l'API officielle Forge 2.x pour les nouveaux projets ;
core.security est le legacy à maintenir sans le supprimer avant Forge 3.0.

Avant de corriger le code, Forge doit formaliser sa doctrine.

---

## Décision

**1. `core.auth` est l'API officielle d'authentification pour les nouveaux projets Forge 2.x.**

Tout nouveau code, nouveau générateur, nouveau starter et toute nouvelle documentation
Forge 2.x doit référencer `core.auth` et non `core.security`.

**2. Argon2id est le format officiel pour les nouveaux mots de passe.**

`core.auth.password.hash_password` produit des hashes Argon2id. C'est le seul format
recommandé pour les projets Forge 2.x.

**3. `core.security.hashing` reste maintenu temporairement comme couche de compatibilité legacy.**

Les fonctions `hacher_mot_de_passe`, `verifier_mot_de_passe`, `enregistrer_tentative` et
`est_limite` de `core.security.hashing` restent disponibles sans modification.
Elles ne sont pas dépréciées au sens technique — aucun warning runtime n'est ajouté dans
ce ticket.

**4. Les hashes PBKDF2 existants doivent rester vérifiables.**

Aucune base de données ne sera migrée automatiquement sans action explicite. Un projet
utilisant des hashes PBKDF2 stockés doit pouvoir continuer à les vérifier via
`core.security.hashing.verifier_mot_de_passe`.

**5. Les nouveaux projets ne doivent plus utiliser PBKDF2.**

La documentation, les exemples et les générateurs de Forge 2.x ne font plus référence à
`hacher_mot_de_passe` ni à PBKDF2 comme choix recommandé.

**6. La migration automatique PBKDF2 → Argon2id sera traitée dans un ticket séparé.**

Le ticket `AUTH-HASH-MIGRATION-001` décrira le mécanisme de rehachage transparent
(vérifier PBKDF2, rehacher en Argon2id à la prochaine connexion réussie). Ce mécanisme
n'est pas implémenté dans ce ticket.

**7. `core.security.hashing` ne sera pas supprimé avant Forge 3.0.**

La suppression ou la dépréciation officielle (avec warning) de `core.security.hashing`
est hors scope de Forge 2.x. Elle sera planifiée dans la roadmap Forge 3.0.

**8. `core.security.session`, `core.security.decorators` et `core.security.rbac` restent
maintenus sans modification.**

Ces modules sont utilisés par `mvc/helpers/flash.py` et `mvc/controllers/`. Leur
alignement vers `core.auth` est un chantier distinct (`AUTH-DEFAULT-ALIGN-001`,
`AUTH-LEGACY-BOUNDARY-001`).

---

## Conséquences

- Les projets générés via `forge make:crud` et `forge auth:init` peuvent temporairement
  utiliser des APIs différentes selon leur version de génération.
- Un projet entièrement nouveau doit utiliser `core.auth` exclusivement.
- Un projet migrant depuis Forge 1.x peut continuer à utiliser `core.security` le temps
  de sa migration.
- La CLI Auth (`forge auth:init`) doit produire des contrôleurs qui utilisent `core.auth`,
  pas `core.security`. Ce point est vérifié par `AUTH-CLI-LOGIN-E2E-TEST-001`.

---

## Modules officiels Forge 2.x

| Domaine | Module officiel | Fonctions clés |
|---|---|---|
| Mot de passe | `core.auth.password` | `hash_password`, `verify_password` |
| Utilisateur | `core.auth.user` | `AuthUser`, `normalize_auth_user`, `validate_auth_user_contract` |
| Session | `core.auth.session` | `login_user`, `logout_user`, `is_authenticated`, `current_user`, `get_authenticated_user_id`, `@login_required` |
| RBAC utilisateur | `core.auth.user_rbac`, `core.auth.user_rbac_resolver` | association `user_id` ↔ `role_id` |
| Autorisations | `core.auth.authorization` | protection par permission RBAC |
| MFA / TOTP | `core.auth.mfa` | contrat MFA, TOTP, challenge connexion, revalidation |
| OIDC | `core.auth.oidc`, `core.auth.oidc_identity` | OAuth/OIDC avec state, nonce, PKCE |
| Tokens | `core.auth.tokens` | jetons sécurisés génériques à usage limité |
| Email | `core.auth.email` | vérification d'adresse email |
| Reset | `core.auth.reset`, `core.auth.recovery` | reset mot de passe, codes de récupération |
| Rate limiting | `core.auth.rate_limit` | protection anti-bruteforce |
| Jinja | `core.auth.jinja` | `current_user_jinja`, état de connexion dans les templates |
| Audit | `core.auth.audit` | journalisation des événements d'authentification |
| Exceptions | `core.auth.exceptions` | `AuthError`, `InvalidAuthUserError` |

---

## Modules legacy maintenus (core.security)

| Domaine | Module legacy | Fonctions | Note |
|---|---|---|---|
| Mot de passe PBKDF2 | `core.security.hashing` | `hacher_mot_de_passe`, `verifier_mot_de_passe`, `pbkdf2_needs_rehash` | PBKDF2-HMAC-SHA256, 600 000 itérations (renforcé via SECURITY-PBKDF2-HARDENING-001) |
| Rate limiting legacy | `core.security.hashing` | `enregistrer_tentative`, `est_limite` | couplé à `auth_controller.py` |
| Session legacy | `core.security.session` | `creer_session`, `authentifier_session`, `est_authentifie`, `get_session`, `get_session_id`, `get_utilisateur`, `utilisateur_a_role`, `set_flash`, `get_flash` | noms français |
| Décorateurs legacy | `core.security.decorators` | `require_auth`, `require_csrf` | basés sur `core.security.session` |
| RBAC générique | `core.security.rbac` | `Role`, `Permission`, `require_permission`, `has_permission`, `make_can` | compatible avec `core.auth.authorization` |
| Middleware | `core.security.middleware` | CSRF et utilitaires session | partagé |

---

## Règles de migration

Pour un projet souhaitant migrer de `core.security` vers `core.auth` :

1. Remplacer `hacher_mot_de_passe` par `hash_password` et planifier un rehachage progressif
   (ticket `AUTH-HASH-MIGRATION-001`).
2. Remplacer `est_authentifie` / `get_utilisateur` par `is_authenticated` / `current_user`.
3. Remplacer `@require_auth` par `@login_required`.
4. Les hashes PBKDF2 stockés en base restent vérifiables via `core.security.hashing`
   pendant la période de transition.
5. Ne pas supprimer `core.security` tant que tous les hashes PBKDF2 n'ont pas été migrés.

---

## Ce que cette ADR ne fait pas

- Ne modifie aucun fichier Python (`core/`, `mvc/`, starters).
- N'ajoute aucun warning runtime.
- N'implémente aucun mécanisme de migration de hashes.
- Ne supprime pas PBKDF2.
- Ne refond pas la documentation Auth complète.
- Ne change pas les starters existants.

---

## Tickets dépendants

| Ticket | Sujet | Relation |
|---|---|---|
| `AUTH-DEFAULT-ALIGN-001` | Aligner `auth_controller.py` sur `core.auth` | implémentation directe de cette ADR |
| `AUTH-CLI-LOGIN-E2E-TEST-001` | Test E2E du flux login via CLI Auth | vérification que la CLI produit du code `core.auth` |
| `STARTERS-AUTH-AUDIT-001` | Audit des starters utilisant core.security | inventaire des starters à migrer |
| `SECURITY-PBKDF2-HARDENING-001` | Durcissement du code PBKDF2 legacy | si besoin, sans le supprimer |
| `AUTH-HASH-MIGRATION-001` | Rehachage transparent PBKDF2 → Argon2id | mécanisme de migration à la connexion |
| `AUTH-LEGACY-BOUNDARY-001` | Définir la frontière définitive legacy/moderne | préciser ce qui reste dans `core.security` |
| `CMD-LEGACY-DEPRECATION-001` | Dépréciation officielle des commandes legacy | prépare Forge 3.0 |
