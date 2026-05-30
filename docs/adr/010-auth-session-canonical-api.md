# ADR-010 — API canonique auth/session

## Statut

Acceptée

## Date

2026-05-16

---

## Contexte

Forge dispose de deux piles parallèles pour la gestion des sessions et de
l'authentification :

**`core.auth.session`** — API moderne, typée, en anglais :

| Fonction | Rôle |
|---|---|
| `authenticate_user(email, password, user_loader)` | Vérification email + mot de passe via loader applicatif |
| `login_user(request, user)` | Stocke `_auth_user_id` dans la session |
| `logout_user(request)` | Retire `_auth_user_id` de la session |
| `get_authenticated_user_id(request)` | Lit l'identifiant utilisateur typé (`int`) |
| `current_user(request, user_loader)` | Retourne l'`AuthUser` courant |
| `is_authenticated(request)` | Vérifie la présence de `_auth_user_id` |
| `@login_required` | Décorateur contrôleur — 401 ou redirect |

Cette pile est compatible avec `AuthUser`, le protocole `SessionStore` (Phase 3)
et tous les modules opt-in (`forge-mvc-mfa`, `forge-mvc-rbac`).

**`core.security.session`** — API legacy, en français/anglais mixte :

| Fonction | Rôle |
|---|---|
| `create_session()` | Crée une session via le store |
| `get_session(session_id)` | Lit les données de session |
| `delete_session(session_id)` | Supprime une session |
| `regenerate_session(old_session_id)` | Régénère un `session_id` |
| `authenticate_session(session_id, user: dict)` | Authentifie avec un dict FR (`UtilisateurId`, `Login`…) |
| `get_session_id(request)` | Extrait le `session_id` depuis le cookie |
| `is_authenticated(request)` | Vérifie `SESSION_KEY_AUTHENTICATED` dans la session |
| `get_user(request)` | Retourne le dict utilisateur brut |
| `user_has_role(request, role)` | Vérifie un rôle dans le dict utilisateur |
| `set_flash(session_id, message, level)` | Stocke un message flash |
| `get_flash(session_id)` | Lit et supprime le message flash |

Cette pile est utilisée par `mvc/controllers/auth_controller.py`,
`mvc/controllers/mfa_challenge_controller.py`, `mvc/helpers/flash.py`,
`core/security/decorators.py`, `core/security/middleware.py`, plusieurs
starters et certains modules opt-in.

### Interdépendance actuelle

`core.auth.session._resolve_request_session()` appelle en interne
`core.security.session.get_session` / `get_session_id` comme fallback.
`forge-mvc-mfa` importe les deux piles. `forge-mvc-rbac` importe
principalement `core.auth.session`.

### Décision ADR-001 (historique)

ADR-001 a déjà établi que `core.auth` est l'API officielle pour les nouveaux
projets Forge 2.x. ADR-010 formalise cette décision pour la série 1.0.x
(renommée depuis 3.x) et pose le cadre de la transition.

---

## Décision

**1. `core.auth.session` est l'API canonique.**

Tout nouveau code Forge, tout nouveau starter, tout nouveau module opt-in et
toute nouvelle documentation doit référencer `core.auth.session`.

**2. `core.security.session` est l'API legacy.**

Elle reste fonctionnelle et non modifiée jusqu'à la livraison de
`AUTH-SESSION-LEGACY-DEPRECATION-001`. Elle ne doit pas être étendue.

**3. `core.auth.session` expose les fonctions de session bas niveau via `_resolve_request_session`.**

Les opérations HTTP bas niveau (`create_session`, `get_session_id`, `set_flash`,
`get_flash`) restent dans `core.security.session` jusqu'à la déduplication
effective. La décision de quelles fonctions migrer appartient à
`AUTH-SESSION-DEDUP-001`.

**4. Aucun warning n'est émis à l'import de `core.security.session`.**

L'import de `core.security.session` ne doit pas émettre de `DeprecationWarning`.
Les warnings seront ajoutés **uniquement à l'appel** des fonctions legacy, dans
le ticket `AUTH-SESSION-LEGACY-DEPRECATION-001`.

**5. `@login_required` (core.auth.session) remplace `@require_auth` (core.security.decorators).**

`@require_auth` est legacy. Les nouveaux contrôleurs utilisent `@login_required`.

---

## Conséquences

- Le code existant (`mvc/`, starters) continue de fonctionner sans modification.
- Les nouveaux projets générés après cette ADR utilisent `core.auth.session`.
- Les modules opt-in (`forge-mvc-rbac`, `forge-mvc-mfa`) qui importent déjà
  `core.auth.session` sont conformes.
- Les imports `core.security.session` dans `forge-mvc-rbac.rbac` et
  `forge-mvc-mfa.mfa` seront migrés dans `AUTH-SESSION-DEDUP-001`.

---

## Politique de transition

La transition se déroule en quatre tickets :

| Ticket | Responsabilité |
|---|---|
| `AUTH-SESSION-CANONICAL-DECISION-001` (ce ticket) | Décision canonique et documentation |
| `AUTH-SESSION-DEDUP-001` | Alignement et déduplication — migration des imports runtime |
| `AUTH-SESSION-LEGACY-DEPRECATION-001` | Ajout des `DeprecationWarning` sur les fonctions legacy |
| `STARTER-AUTH-MODERNIZE-001` | Modernisation du starter auth sur `core.auth.session` |
| `CORE-AUTH-NO-HARDCODED-FIELDS-001` | Suppression des champs applicatifs codés en dur dans le core |

---

## Règle de dépréciation

```
Aucun DeprecationWarning à l'import.
DeprecationWarning uniquement à l'appel des fonctions legacy.
Cette étape appartient exclusivement à AUTH-SESSION-LEGACY-DEPRECATION-001.
```

Cette règle protège les projets qui importent `core.security.session` sans
l'utiliser directement (via des imports intermédiaires dans le core).

---

## Amendement — Dépréciations API legacy (4.3)

**Ticket** : `AUTH-SESSION-LEGACY-DEPRECATION-001`
**Date** : 2026-05-16

Les fonctions legacy suivantes de `core.security.session` émettent désormais un
`DeprecationWarning` à l'appel, avec le chemin canonique à utiliser :

| Fonction dépréciée | API canonique à utiliser |
|---|---|
| `create_session()` | `get_session_store().create()` |
| `authenticate_session(session_id, user)` | `login_user(request, user)` avec `AuthUser` |
| `is_authenticated(request)` | `core.auth.session.is_authenticated(request)` |
| `get_user(request)` | `core.auth.session.current_user(request, user_loader)` |

**Fonctions infrastructure conservées sans warning** : `get_session_id`,
`get_session`, `delete_session`, `regenerate_session`, `user_has_role`,
`set_flash`, `get_flash` — pas d'équivalent canonique direct ou utilisées
en interne par le framework.

**Propriétés garanties** :
- L'import de `core.security.session` n'émet aucun `DeprecationWarning`.
- Les fonctions dépréciées continuent à fonctionner — la migration est
  progressive, non cassante.
- `stacklevel=2` : le warning pointe vers le code appelant.
- `user_has_role` ne cascade pas le warning de `get_user` (refactorisé
  pour lire le store directement).

La suppression effective et la migration des usages applicatifs appartiennent
aux tickets 4.4 (`STARTER-AUTH-MODERNIZE-001`) et suivants.

---

## Amendement — Pont de compatibilité bidirectionnel (4.2b)

**Ticket** : `AUTH-SESSION-COMPATIBILITY-BRIDGE-001`
**Date** : 2026-05-16

La divergence de clés de session (`_auth_user_id` vs `authenticated + user`)
rendait les deux piles mutuellement opaques. Le ticket 4.2b a livré un pont de
lecture bidirectionnel :

**`core.auth.session.get_authenticated_user_id`** reconnaît les sessions legacy :
si `_auth_user_id` est absent mais que `authenticated=True` et `user.id` sont
présents (session créée par `authenticate_session`), l'identifiant est retourné.

**`core.security.session.is_authenticated`** reconnaît les sessions canoniques :
si les clés legacy sont absentes mais que `_auth_user_id` est un entier positif
(session créée par `login_user`), la session est considérée authentifiée.

**Propriétés garanties** :
- Aucune écriture dans la session à la lecture — pas de pollution de clés.
- L'expiration est étendue dans les deux cas.
- Pas d'import circulaire : `core.security.session` utilise la clé littérale
  `"_auth_user_id"` sans importer `core.auth.session`.

Ce pont ferme les constats **FND-AUTH-001** et **FND-AUTH-002** du tracker
post-audit 2026-05.

---

## Ce que cette ADR ne fait pas

- N'aligne pas `mvc/controllers/` sur `core.auth.session`.
- Ne déplace aucune fonction.
- Ne supprime pas `core.security.session`.
- N'ajoute aucun `DeprecationWarning`.
- Ne modifie pas les starters.
- Ne modifie pas les modules opt-in.
- Ne modifie pas le comportement runtime (sessions, authentification, CSRF).
- Ne touche pas MFA, RBAC, CSRF.
- Ne publie aucune version.

---

## Tickets liés

| Ticket | Description | Phase |
|---|---|---|
| `AUTH-SESSION-CANONICAL-DECISION-001` | Ce document | Phase 4.1 |
| `AUTH-SESSION-DEDUP-001` | Déduplication et migration des imports | Phase 4.2 |
| `AUTH-SESSION-LEGACY-DEPRECATION-001` | Warnings legacy à l'appel | Phase 4.3 |
| `STARTER-AUTH-MODERNIZE-001` | Modernisation du starter auth | Phase 4.4 |
| `CORE-AUTH-NO-HARDCODED-FIELDS-001` | Suppression des champs hardcodés | Phase 4.5 |
| `ADR-001` | Décision historique Forge 2.x (référence) | Forge 2.x |
| `AUTH-SESSION-DEDUP-001` (tracker) | Constat FND-AUTH-001 | Audit 2026-05 |
