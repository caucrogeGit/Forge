# ADR-004 — Périmètre du `core/` minimal strict

## Statut

Acceptée

---

## Contexte

Forge a grandi organiquement. Le `core/` contient aujourd'hui :

- Les primitives générales du framework (HTTP, routing, templating, DB, sessions,
  forms, uploads, mail, sécurité de base) — **légitimes dans le core/**.
  > **Amendement ADR-019** : l'**upload générique** (`core/uploads/` : écriture,
  > storage, service de fichiers, rate-limit) a depuis été **extrait** vers
  > l'opt-in `forge-mvc-files`. Seule la **validation pure** de fichier reste
  > dans le core (`core/forms`), car `FileField` en dépend. Voir ADR-019.
- Des modules spécialisés qui répondent à des besoins avancés ou métier :
  - `core/auth/mfa.py` — MFA TOTP et codes de récupération
  - `core/auth/experimental/oidc.py` — socle OIDC partiel
  - `core/auth/user_rbac.py`, `core/auth/user_rbac_resolver.py` — RBAC fin
  - `core/workflow/` — moteur de workflow applicatif
  - `core/stats/` — statistiques orientées événements
  - `core/auth/audit.py` — audit log via Python logger

Ces modules spécialisés violent le Principe 8 de la charte : le `core/` ne
doit contenir que les primitives générales nécessaires au fonctionnement d'un
framework web.

Le test de légitimité est : *"Si je retire cette brique du `core/`, est-ce
qu'une app Forge basique peut encore tourner ?"*. Pour MFA, OIDC, RBAC fin,
workflow et stats : oui. Ces briques appartiennent donc à des modules.

L'audit de la phase 14.1 a confirmé que le `core/` est surchargé, et que
plusieurs modules ont des tensions de périmètre (OIDC partiel, audit
logging-only, workflow non finalisé).

---

## Décision

**Le `core/` de Forge 3.0 est réduit à ses primitives générales.**

Les 5 modules suivants seront extraits du `core/` vers des distributions
PyPI séparées (voir ADR-005) :

| Module actuel | Distribution cible | Ticket |
|---|---|---|
| `core/auth/mfa.py` + MFA | `forge-mvc-mfa` | `MFA-EXTRACT-001` |
| ~~`core/auth/experimental/oidc.py`~~ | ~~`forge-mvc-oidc`~~ supprimé | `OIDC-REMOVE-OR-EXTRACT-001` ✅ |
| `core/auth/user_rbac.py` + RBAC fin | `forge-mvc-rbac` | `RBAC-EXTRACT-001` |
| `core/workflow/` | `forge-mvc-workflow` | `WORKFLOW-EXTRACT-001` |
| `core/stats/` | `forge-mvc-stats` | `STATS-EXTRACT-001` |

Ce qui reste dans `core/` après extraction :

- `core/http/` — Request, Response, helpers
- `core/routing/` — Router, groupes, middlewares
- `core/app/application.py` — pipeline + dispatch
- `core/forge.py` — configuration du noyau
- `core/templating/` — contrat Renderer, template_manager
- `core/database/` — db (fetch_one, fetch_all, execute, insert)
- `core/sessions/` — SessionStore contractuel + 3 implémentations
- `core/forms/` — Form, Field, validation (dont la validation de fichier, ADR-019)
- ~~`core/uploads/`~~ — **extrait vers `forge-mvc-files`** (ADR-019) ; ne reste que des shims transitoires jusqu'à `CORE-DROP-UPLOADS-001`
- `core/mail/` — transports, templates mail
- `core/auth/` (primitives) — password, session, user (sans MFA, RBAC fin)
- `core/security/` — CSRF, CSP, headers, hashing
- `core/modules/` — chargement, registry, manifest
- `core/mvc/` — BaseController, pagination, validation basique

---

## Conséquences

- Les 5 extractions feront l'objet de tickets dédiés en phase 14.3.
- Chaque extraction inclura une période de dépréciation avec aliases dans le
  `core/` (re-exports avec `DeprecationWarning`) selon la règle C de la charte.
- L'OIDC (partiel, expérimental) a été supprimé du dépôt (`OIDC-REMOVE-OR-EXTRACT-001`).
  Décision finale : suppression. Le code reste dans l'historique git.
  Si OIDC est repris, un ticket dédié `OIDC-IMPLEMENT-COMPLETE-001` partira
  d'une page blanche.
- Les starters qui dépendent de ces modules devront déclarer explicitement
  la distribution correspondante dans leurs dépendances.

---

## Décision complémentaire — Périmètre de core/auth/ résiduel (AUTH-EXTRA-EXTRACT-001)

Ticket G2 de la Phase G a évalué si trois sous-modules de `core/auth/` méritaient
une extraction vers un package opt-in `forge-mvc-auth-extra` :

| Sous-module | Lignes | Fonctionnalité |
|---|---|---|
| `core/auth/rate_limit.py` | 398 | Anti-brute-force en mémoire processus |
| `core/auth/audit.py` | 314 | Émission d'événements auth vers Python logging |
| `core/auth/reset.py` | 211 | Demande et réinitialisation de mot de passe |

**Décision : ces trois modules restent dans `core/auth/` de manière définitive.**

Rationale :

1. **Dépendance core → core impossible à externaliser** — `core/security/hashing.py`
   importe `core.auth.rate_limit` pour le rate-limit des opérations de hachage.
   Extraire `rate_limit` dans un opt-in créerait une dépendance d'une primitive
   fondamentale du core sur un module facultatif — violation exactement inverse du
   Principe 8.

2. **audit utilisé par les modules opt-in** — `forge-mvc-mfa` consomme
   `core.auth.audit` (lazy imports). Ce module doit rester disponible sans
   installation d'extras. Un opt-in qui dépend d'un autre opt-in viole le
   principe de briques indépendantes.

3. **reset est spécifique à Auth/User** — aucun usage externe à `core/auth/`
   prévisible ; généricité insuffisante pour justifier un package séparé.

4. **4 packages opt-in déjà existants** (MFA, RBAC, Workflow, Stats) — l'ajout
   d'un cinquième opt-in demande une justification forte d'usage externe indépendant.
   Ce critère n'est pas rempli.

Cette décision est définitive sauf nouvelle évidence (adoption externe de ces
modules hors du contexte Forge). Voir ticket `AUTH-EXTRA-EXTRACT-001`.

---

## Alternatives considérées

**Garder tout dans core/ mais mieux documenter les limites.** Abandonné :
viole le Principe 8 de la charte. La documentation ne résout pas le problème
de couplage.

**Extraire vers un monorepo séparé.** Abandonné : augmente la friction de
développement. Le monorepo hybride (ADR-005) offre le meilleur compromis.

**Extraire rate_limit/audit/reset vers forge-mvc-auth-extra.** Abandonné :
crée une dépendance `core/security/ → opt-in` (rate_limit) et
`forge-mvc-mfa → forge-mvc-auth-extra` (audit) — voir section ci-dessus.
