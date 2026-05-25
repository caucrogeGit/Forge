# Roadmap Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette roadmap concerne uniquement **Forge**, le framework MVC Python : cœur, CLI, générateurs, modules, starters, documentation, tests et publication.

Forge Design est désormais traité dans une roadmap séparée.

> **Note** : Ce document contient l'historique de développement interne pré-publication.
> La version publique actuelle est **Forge 1.0.0-beta.9**.

---

## État actuel — Forge 1.0.0-beta.9

**Tag courant : `v1.0.0-beta.9` (2026-05-24)**

Précédent : v1.0.0-beta.8 (2026-05-22), v1.0.0-beta.7 (2026-05-22), v1.0.0-beta.6 (2026-05-21), v1.0.0-beta.5 (2026-05-17), v1.0.0-beta.3 (2026-05-16), v1.0.0-beta.2 (2026-05-16), v1.0.0-beta.1 (2026-05-15), v3.0.5 (2026-05-14), v3.0.4 (2026-05-14), v3.0.3 (2026-05-14), v3.0.2 (2026-05-13), v3.0.1 (2026-05-12), v3.0.0 (2026-05-12).

**Statut : v1.0.0-beta.9 publiée (core + 5 opt-ins). Phase B9 close : sécurité (cryptography, compare_digest, X-Real-IP), WSGI production encadrée, sessions renforcées, opt-in media en CI, dédomainisation core, landing rafraîchie, sweep documentaire. Bloc B9-C : 12 tickets CLI déjà clos.**

> Note historique : Forge 1.5.0 marquait la fin du socle initial (Phases 0–4 RBAC).
> Les phases 4.5 à 10 ont abouti à Forge 2.0.0, puis à Forge 2.0.1 (corrections critiques)
> et Forge 2.0.2 (cohérence documentaire). La Phase 14 (refonte vers 3.0) a reconstruit
> le cœur minimal, extrait les modules officiels (`forge-mvc-mfa`, `forge-mvc-rbac`,
> `forge-mvc-workflow`, `forge-mvc-stats`) et migré l'API publique en anglais (ADR-003),
> aboutissant à Forge 2.10.0 puis à la release candidate 3.0.0rc1, puis au tag stable v3.0.0.
> Voir le [journal d'avancement détaillé](../history/forge-roadmap-history-2.0.md).

| Phase | Domaine | État |
|---|---|---|
| Phase 0 | Stabilisation Forge 1.2.1 | validée |
| Phase 1 | Media v2 complet | validée côté serveur |
| Phase 2 | Migrations SQL versionnées | validée et stabilisée en 1.4.0 |
| Phase 3 | Socle front léger : Tailwind, JS optionnel, i18n, templates | validée en 1.5.0 |
| Phase 4 | Permissions fines / RBAC | validée en 1.5.0 |
| Phase 4.5 | Auth/User avancée et sécurité moderne | validée côté socle post-1.5.0 |
| Phase 5 | Relations avancées et CRUD enrichi | terminée |
| Phase 6 | Pages publiques génériques | terminée |
| Phase 7 | Workflow, statistiques et modules | pleinement close |
| Phase 8 | Starter Communes & Séjours | terminée |
| Phase 9 | Profils de projet | terminée |
| Phase 9.5 | Consolidation Forge avant publication | terminée |
| Phase 10 | Publication Forge 2.0 | terminée — v2.0.0 publié |
| Phase 1 post-2.0 | Corrections critiques | terminée — v2.0.1 livré |
| Phase 2 post-2.0 | Cohérence documentaire | terminée — v2.0.2 livré |

**Consolidation post-audit renforcé (Forge 3.0.3)** : 11 tickets de
qualité documentaire et technique livrés suite à un audit renforcé
de 3.0.2 (voir [`audit-renforce-3.0.2-001`](../history/audits/audit-renforce-3.0.2-001.md)).

Aucune rupture d'API publique. Voir `CHANGELOG.md` section [3.0.3]
pour le détail.

Dernière validation — Forge 1.0.0-beta.4 (BETA-4-RELEASE-001) :

- `pytest` : **10 166 passed, 3 skipped** (post-1.0.0-beta.4) ;
- `python -m compileall -q .` : **OK** ;
- `mkdocs build --strict` : **OK** ;
- `git diff --check` : **OK**.

Pour l'état détaillé du Scénario C, voir
[Scénario C — Consolidation 3.0.2](#scenario-c-consolidation-302).

---

## Phase 0 — Baseline d'audit (post-1.0.0-beta.1)

**Objectif** : figer officiellement la baseline d'audit avant toute correction
post-audits. Ce n'est pas une version de release.

| Ticket | Description | État |
|---|---|---|
| AUDIT-BASELINE-LOCK-001 | Figer la baseline d'audit (commit + tag non-release) | **livré** |
| AUDIT-FINDINGS-TRACKER-001 | Créer le tracker détaillé des constats | **livré** |
| ADR-009-STABILITY-POLICY-TERRAIN-001 | Créer l'ADR de politique de stabilité terrain | **livré** |

**Baseline** : commit `d611636`, tag `baseline/audit-2026-05-15`.
**Document de référence** : [`docs/history/audits/audit-baseline-2026-05-15.md`](../history/audits/audit-baseline-2026-05-15.md).

---

## Phase 1 — Corrections documentaires (post-audit)

**Objectif** : traiter les constats documentaires prioritaires issus du tracker
post-audit. Aucune modification de runtime, CLI, générateurs ou packaging.

| Ticket | Description | État |
|---|---|---|
| DOCS-OPTIN-INSTALL-CONTRACT-001 | Clarifier le contrat d'installation des opt-ins | **livré** |
| VERSION-COHERENCE-1.0-001 | Aligner les références de version publiques avec la trajectoire 1.0 | **livré** |
| ROADMAP-PUBLIC-VERSION-CLEANUP-001 | Nettoyer la roadmap publique pour la trajectoire 1.0 beta | **livré** |
| README-RUNTIME-DEPS-CLEANUP-001 | Clarifier les dépendances runtime du core (retrait PyOTP) | **livré** |
| PYPI-CLASSIFIER-BETA-ALIGN-001 | Aligner le classifier PyPI avec le statut bêta réel | **livré** |
| PACKAGE-LOCK-DOC-001 | Documenter le verrouillage packaging avant Phase 2 | **livré** |

---

## Phase 2 — Infrastructure de release (post-audit)

**Objectif** : mettre en place l'infrastructure reproductible de validation et de
release. Aboutit à la publication de `1.0.0-beta.2`.

| Ticket | Description | État |
|---|---|---|
| RELEASE-VALIDATION-ENV-LOCK-001 | Documenter l'environnement de validation release | **livré** |
| RELEASE-CHECK-SCRIPT-001 | Créer le script `scripts/release_check.sh` | **livré** |
| BETA-2-RELEASE-001 | Publier `1.0.0-beta.2` | **livré** |

---

## Phase 3 — Sessions configurables (post-audit)

**Objectif** : rendre le store de session explicitement configurable via
`forge.configure(session_store=...)`, sans modifier le comportement par défaut.

| Ticket | Description | État |
|---|---|---|
| SESSIONS-CONFIGURABLE-STORE-001 | Ajouter `forge.configure(session_store=...)` et brancher le store au flux session | **livré** |
| SESSIONS-STORE-CONTRACT-DOC-001 | Documenter le contrat complet et les backends disponibles | **livré** |
| SESSIONS-MEMORY-THREADSAFE-DOC-001 | Documenter la thread-safety de MemorySessionStore | **livré** |

---

## Phase 4 — Déduplication double pile auth/session (post-audit)

**Objectif** : supprimer la double pile `core.auth.session` / `core.security.session`
en formalisant `core.auth.session` comme API canonique, puis en migrant les imports
legacy et en dépréciant les fonctions `core.security.session`.

| Ticket | Description | État |
|---|---|---|
| AUTH-SESSION-CANONICAL-DECISION-001 | Décider et documenter l'API canonique (ADR-010) | **livré** |
| AUTH-SESSION-DEDUP-001 | Aligner les imports runtime sur `core.auth.session` | partiel — analyse livrée, forge_mvc_mfa migré ; migration core bloquée (clés session divergentes) |
| AUTH-SESSION-COMPATIBILITY-BRIDGE-001 | Pont bidirectionnel legacy↔canonique — reconnaissance croisée des sessions | **livré** |
| AUTH-SESSION-LEGACY-DEPRECATION-001 | Ajouter les `DeprecationWarning` sur les fonctions legacy | **livré** |
| STARTER-AUTH-MODERNIZE-001 | Moderniser le starter auth sur `core.auth.session` | **livré** |
| CORE-AUTH-NO-HARDCODED-FIELDS-001 | Supprimer les champs applicatifs codés en dur dans le core | **livré** |

---

## Phase 5 — Consolidation sécurité CSRF (post-audit)

**Objectif** : consolider la gestion CSRF pour qu'il n'existe qu'un chemin de
vérification, avec comparaison constant-time.

| Ticket | Description | État |
|---|---|---|
| CSRF-DEDUP-CONSTANT-TIME-001 | Dédupliquer la validation CSRF et garantir constant-time | **livré** |
| SECURITY-META-NO-CSRF-INEQUALITY-001 | Garde-fou méta anti-régression comparaison naïve CSRF | **livré** |

---

## Phase 6 — Modules : branchement explicite des routes (post-audit)

**Objectif** : supprimer l'injection automatique de routes modules dans les fichiers
applicatifs et imposer un branchement explicite par le développeur.

| Ticket | Description | État |
|---|---|---|
| MODULE-ROUTES-INJECTION-REMOVE-001 | Supprimer l'injection automatique, préserver generate_module_routes | **livré** |
| MODULE-ROUTES-EXPLICIT-DOC-001 | Documenter le contrat explicite des routes modules | **livré** |
| BETA-3-RELEASE-001 | Publication 1.0.0-beta.3 | **livré** |

---

## Phase 7 — Périmètre auth, MFA, RBAC (post-audit)

**Objectif** : clarifier officiellement le périmètre du vocabulaire d'audit auth,
les frontières core / opt-ins, et les politiques de publication et de stockage
des modules opt-in.

| Ticket | Description | État |
|---|---|---|
| AUTH-AUDIT-VOCAB-PERIMETER-001 | Clarifier le périmètre du vocabulaire d'audit MFA/RBAC dans le core | **livré** |
| AUTH-DOCTOR-MFA-MISSING-DEP-WARNING-001 | Avertissement `forge doctor` si MFA utilisé sans forge-mvc-mfa installé | **livré** |
| RBAC-LIGHT-VS-FULL-DOC-001 | Documenter explicitement RBAC léger core vs RBAC complet opt-in | **livré** |
| MFA-SECRET-STORAGE-POLICY-001 | Clarifier et documenter la politique de stockage du secret TOTP | **livré** |
| OPTIN-PACKAGES-PUBLICATION-POLICY-001 | Définir la politique de publication des packages opt-in sur PyPI | **livré** |

---

## Phase 8 — Organisation des tests (post-audit)

**Objectif** : clarifier la structure des tests en séparant les tests méta
(documentaires, roadmap, packaging statique, invariants textuels, frontières
architecturales) des tests comportementaux.

| Ticket | Description | État |
|---|---|---|
| META-TESTS-ROOT-MIGRATION-001 | Déplacer les tests méta de `tests/` vers `tests/meta/` | **livré** |
| META-TESTS-ROTATION-POLICY-001 | Définir la politique de rotation des tests méta redondants | **livré** |
| META-TESTS-PRUNE-001 | Supprimer les tests méta devenus obsolètes | **livré** |
| TESTS-BEHAVIOR-FIRST-001 | Documenter et appliquer la règle behavior-first dans la suite de tests | **livré** |
| PUBLIC-API-DUPLICATES-SCAN-001 | Auditer les doublons dans l'API publique Forge | **livré** |

---

## Phase 9 — Normalisation des frontières linguistiques dans les starters

**État : terminée.**

**Objectif** : aligner les starters historiques sur la convention de frontière
linguistique — le schéma SQL reste français (noms de colonnes), les variables
Python et les contextes de template utilisent des noms canoniques anglais ou
normalisés ; les API dépréciées sont supprimées ; la convention est documentée.

| Ticket | Description | État |
|---|---|---|
| STARTER-LANG-NORMALIZE-001 | Normaliser les frontières SQL/Python dans les starters actifs | **livré** |
| STARTER-CONVENTIONS-DOC-001 | Documenter les conventions de langage des starters dans le guide auteur | **livré** |

---

## Trajectoire officielle — 1.0.0 stable

Conforme à [`ADR-009`](../adr/009-stability-policy-terrain.md) (politique de stabilité terrain) :

```text
1.0.0-beta.1  ← point de départ (baseline/audit-2026-05-15)
1.0.0-beta.2  ← corrections post-audit (Phase 1)
1.0.0-beta.3  ← corrections post-audit (Phase 2)
1.0.0-beta.4  ← corrections post-audit (Phase 3)
1.0.0-beta.5  ← corrections post-audit (Phase 4) + publication opt-ins
1.0.0-beta.6  ← bêta consolidée = T0 tests terrain
1.0.0-beta.7  ← corrections terrain (Phase 10-11) + publication opt-ins supplémentaires
1.0.0-beta.8  ← consolidation media/mfa + chiffrement TOTP Fernet (Phase 12) — PyPI complet
1.0.0-beta.9  ← corrections sécurité + WSGI + docs (Phase B9 — en cours)
→ tests terrain : 2 mois minimum
→ 1.0.0-rc1   ← release candidate
→ 1.0.0       ← stable
```

`1.0.0-beta.6` marque le T0 officiel des tests terrain (ADR-009).
Un passage en stable ne peut intervenir qu'après terrain validé et RC publiée.

---

## Socle livré en Forge 1.5.0

Forge 1.5.0 fournit un socle MVC complet :

- modèle canonique JSON ;
- projections SQL et Python générées ;
- CLI Forge ;
- migrations SQL ;
- CRUD généré ;
- CSRF ;
- formulaires ;
- médias ;
- mail ;
- RBAC ;
- Tailwind ;
- HTMX optionnel ;
- i18n ;
- templates publics/admin ;
- documentation MkDocs ;
- starters historiques 1 à 4.

---

## Phase 3 — Socle front léger

**État : validée en Forge 1.5.0.**

Objectif : générer des interfaces modernes sans basculer vers une SPA lourde.

| Ticket | État | Résultat |
|---|---|---|
| CSS-001 | terminé | Tailwind clarifié comme CSS officiel |
| FRONT-001 | terminé | `static/js/app.js` ajouté |
| FRONT-002 | terminé | `forge js:init htmx` |
| FRONT-003 | terminé | `forge js:init alpine` |
| FRONT-004 | terminé | `forge js:init htmx-alpine` |
| FRONT-005 | terminé | `{% block scripts %}` dans les layouts |
| FRONT-006 | terminé | HTMX documenté |
| FRONT-007 | terminé | Alpine.js documenté |
| I18N-001 à I18N-009 | terminé | i18n simple livrée |
| TPL-001 à TPL-007 | terminé | templates publics/admin et composants Jinja |

Règle : le HTML serveur reste la base. HTMX et Alpine améliorent l’expérience, mais ne remplacent pas MVC.

---

## Phase 4 — Permissions fines / RBAC

**État : validée en Forge 1.5.0.**

| Ticket | État | Résultat |
|---|---|---|
| AUTH-RBAC-001 | terminé | modèles génériques `Role` et `Permission` |
| AUTH-RBAC-002 | terminé | décorateur `@require_permission(...)` |
| AUTH-RBAC-003 | terminé | helper Jinja `can(...)` |
| AUTH-RBAC-004 | terminé | protection déclarative des routes CRUD |
| AUTH-RBAC-SEC-001 | terminé | audit de sécurité RBAC |
| AUTH-RBAC-DOC-001 | terminé | documentation RBAC |

Décision structurante : le core RBAC ne crée pas de table `user_roles`. Cette table appartient à la brique Auth/User optionnelle.

---

## Phase 4.5 — Auth/User avancée et sécurité moderne

**État : validée côté socle post-1.5.0.**

Objectif : fournir une identité utilisateur fiable et optionnelle, exploitable par RBAC.

| Ticket | État | Objectif |
|---|---|---|
| AUTH-USER-001 | terminé | contrat utilisateur minimal |
| AUTH-USER-002 | terminé | table `users` optionnelle |
| AUTH-PASSWORD-001 | terminé | hash et vérification de mot de passe |
| AUTH-SESSION-001 | terminé | login/logout/session |
| AUTH-SESSION-002 | terminé | `current_user`, `is_authenticated`, `@login_required` |
| AUTH-TOKEN-001 | terminé | jetons sécurisés |
| AUTH-EMAIL-001 | terminé | vérification email |
| AUTH-RESET-001 | terminé | demande de reset password |
| AUTH-RESET-002 | terminé | reset password effectif |
| AUTH-MFA-001 | terminé | contrat MFA |
| AUTH-MFA-002 | terminé | TOTP |
| AUTH-MFA-003 | terminé | codes de récupération |
| AUTH-MFA-004 | terminé | challenge MFA à la connexion |
| AUTH-MFA-005 | terminé | revalidation MFA actions sensibles |
| AUTH-OIDC-001 | terminé | contrat OIDC |
| AUTH-OIDC-002 | terminé | login OIDC avec state, nonce, PKCE |
| AUTH-OIDC-003 | terminé | association compte local / OIDC |
| AUTH-USER-RBAC-001 | terminé | table `user_roles` optionnelle |
| AUTH-USER-RBAC-002 | terminé | permissions RBAC depuis utilisateur connecté |
| AUTH-USER-JINJA-001 | terminé | utilisateur courant dans Jinja |
| AUTH-USER-CLI-001 | terminé | diagnostics CLI Auth/User |
| AUTH-ADMIN-001 | terminé | administration CLI utilisateurs minimale |
| AUTH-ADMIN-002 | terminé | activation/désactivation utilisateur |
| AUTH-ADMIN-003 | terminé | attribution des rôles |
| AUTH-AUDIT-001 | terminé | journalisation auth |
| AUTH-RATE-LIMIT-001 | terminé | anti-bruteforce minimal |
| AUTH-DOC-001 | terminé | documentation Auth avancée |
| AUTH-SECURITY-AUDIT-001 | terminé | audit global Auth/User |
| AUTH-ADMIN-ROLE-CLI-001 | terminé | cohérence commandes CLI rôles utilisateur |

Limites repoussées :

- WebAuthn / passkeys ;
- SAML / SSO entreprise ;
- OAuth multi-provider avancé ;
- gestion utilisateurs multi-tenant ;
- invitations utilisateurs ;
- profils métiers avancés.

---

## Phase 5 — Relations avancées et CRUD enrichi

**État : terminée.**

### 5.1 Relations avancées

| Ticket | État | Objectif |
|---|---|---|
| REL-M2M-001 | terminé | déclaration `many_to_many` |
| REL-M2M-002 | terminé | génération table pivot SQL |
| REL-M2M-003 | terminé | sélection multiple |
| REL-M2M-004 | terminé | affichage list/show |
| REL-PIVOT-001 | terminé | pivot enrichi |
| REL-ORDERED-001 | terminé | relations ordonnées hors média |

### 5.2 CRUD enrichi

| Ticket | État | Objectif |
|---|---|---|
| CRUD-SEARCH-001 | terminé | recherche simple |
| CRUD-FILTER-AUDIT-001 | terminé | audit filtres |
| CRUD-FILTER-001 | livré | filtres déclaratifs existants |
| CRUD-SORT-001 | terminé | tri sécurisé |
| CRUD-PAGINATION-001 | terminé | pagination serveur |
| CRUD-EMPTY-AUDIT-001 | terminé | audit états vides |
| CRUD-EMPTY-001 | terminé | états vides contextuels |
| CRUD-RELATION-FIELD-AUDIT-001 | terminé | audit champs relationnels |
| CRUD-RELATION-FIELD-001 | couvert | champs relationnels déjà couverts |
| CRUD-HTMX-AUDIT-001 | terminé | audit HTMX CRUD |
| CRUD-HTMX-PARTIALS-001 | terminé | partials CRUD |
| CRUD-HTMX-001 | terminé | recherche HTMX |
| CRUD-HTMX-002 | terminé | pagination HTMX |
| CRUD-HTMX-003 | terminé | suppression HTMX |
| PHASE-5-DOC-001 | terminé | documentation consolidée Phase 5 |

Règle : le CRUD HTML classique reste la base. HTMX est une amélioration optionnelle.

---

## Phase 6 — Pages publiques génériques

**État : terminée.**

Commandes disponibles :

```bash
forge make:public-page accueil
forge make:public-list Hebergement
forge make:public-show Hebergement
forge make:public-form DemandeSejour
forge make:public-contact
```

| Ticket | État | Objectif |
|---|---|---|
| PUBLIC-PAGE-001 | terminé | page publique simple |
| PUBLIC-LIST-001 | terminé | liste publique |
| PUBLIC-SHOW-001 | terminé | fiche publique |
| PUBLIC-FORM-001 | terminé | formulaire public |
| PUBLIC-CONTACT-001 | terminé | page contact |
| PUBLIC-TEMPLATES-001 | terminé | templates publics |
| PUBLIC-I18N-001 | terminé | compatibilité i18n |
| PUBLIC-MEDIA-001 | terminé | médias publics |
| PHASE-6-DOC-001 | terminé | documentation consolidée Phase 6 |

---

## Phase 7 — Workflow, statistiques et modules

**État : terminée côté socle générique.**

Objectif : ajouter des briques applicatives génériques sans coder le métier Communes & Séjours dans le core.

### 7.1 Workflow générique

| Ticket | État | Objectif |
|---|---|---|
| WORKFLOW-001 | terminé | statuts génériques |
| WORKFLOW-TRANSITIONS-001 | terminé | transitions autorisées |
| WORKFLOW-JINJA-001 | terminé | helpers Jinja |
| WORKFLOW-DOC-001 | terminé | documentation |

### 7.2 Statistiques simples

| Ticket | État | Objectif |
|---|---|---|
| STATS-001 | terminé | événements simples |
| STATS-002 | terminé | table SQL générique |
| STATS-003 | terminé | helper `track_event()` |
| STATS-004 | terminé | consultation admin simple |

Les statistiques Forge reposent sur un tracking explicite, jamais automatique.

### 7.3 Système de modules

| Ticket | État | Objectif |
|---|---|---|
| MODULE-SYSTEM-001 | terminé | structure standard d’un module |
| MODULE-SYSTEM-002 | terminé | `forge module:list` |
| MODULE-SYSTEM-003 | terminé | `forge module:install` |
| MODULE-SYSTEM-004 | terminé | injection propre des routes |
| MODULE-SYSTEM-005 | terminé | installation entities/views/controllers/docs |
| MODULE-SYSTEM-DOC-001 | terminé | documentation complète modules |
| PHASE-7-DOC-001 | terminé | clôture documentation Phase 7 |
| MODULE-ROUTES-RUNTIME-AUDIT-001 | terminé | Option A : `modules/` est runtime officiel pour les routes |
| MODULE-FILES-SECURITY-001 | terminé | symlinks refusés, `file://` ajouté aux URL refusées |
| MODULE-FILES-SAFETY-001 | plus tard | sécurisation installations partielles |

Règle : un module Forge ne doit pas être une boîte noire. Il doit rester lisible, copiable, auditable et modifiable.

---

## Consolidation documentaire avant Phase 8

**État : à faire avant de démarrer fortement le starter Communes & Séjours.**

| Ticket | État | Objectif |
|---|---|---|
| DOC-ROADMAP-SPLIT-001 | terminé | séparer officiellement les roadmaps Forge et Forge Design |
| DOC-VERSION-CONSISTENCY-001 | terminé | harmoniser les références de versions |
| DOC-DEPENDENCIES-001 | terminé | corriger la documentation des dépendances |
| DOC-LICENSE-CONSISTENCY-001 | terminé | aligner la licence |
| DOC-MKDOCS-WARNINGS-001 | optionnel | nettoyer les warnings MkDocs |

---

## Phase 8 — Starter Communes & Séjours

**État : terminée.**

Tous les tickets `STARTER-CS-*` sont livrés. Le starter dispose d’un squelette, d’entités JSON, de médias, de pages publiques, d’un formulaire de demande, de notifications mail, de textes i18n, de données de démonstration et d’une documentation consolidée.

| Ticket | Objectif |
|---|---|
| STARTER-CS-001 | terminé | squelette starter Communes & Séjours |
| STARTER-CS-ENTITIES-001 | terminé | entités JSON |
| STARTER-CS-MEDIA-001 | terminé | déclaration médias sur Hebergement |
| STARTER-CS-PUBLIC-001 | terminé | accueil + liste + fiche publique |
| STARTER-CS-FORM-001 | terminé | formulaire de demande de séjour |
| STARTER-CS-MAIL-001 | terminé | notifications mail visiteur + propriétaire |
| STARTER-CS-I18N-001 | terminé | textes compatibles i18n |
| STARTER-CS-SEED-001 | terminé | fausses données de démonstration |
| STARTER-CS-DOC-001 | terminé | Documentation d’installation du starter Communes & Séjours |

Le starter devra démontrer :

- page d’accueil attractive ;
- liste d’hébergements ;
- fiche hébergement ;
- galerie média ;
- formulaire de demande ;
- mail/log de notification ;
- back-office minimal ;
- données de démonstration.

### 8.1 Transition des starters historiques

**État : décisions prises.**

Les starters 1 et 3 restent des starters officiels. Le starter 2 est conservé mais doit être modernisé côté Auth/User. Le starter 4 devient un démonstrateur historique/legacy. Le starter 5 Communes & Séjours est le démonstrateur avancé principal.

| Statut | Starters |
|---|---|
| Officiel simple | Starter 1 — Contacts |
| À moderniser (Auth/User) | Starter 2 — Utilisateurs / Auth |
| Officiel relationnel | Starter 3 — Carnet de contacts |
| Démonstrateur historique | Starter 4 — Suivi pédagogique |
| Démonstrateur avancé principal | Starter 5 — Communes & Séjours |

| Ticket | Objectif |
|---|---|
| STARTER-LEGACY-AUDIT-001 | terminé | Auditer les starters historiques 1 à 4 |
| STARTER-LEGACY-DECISION-001 | terminé | Décider le statut des starters historiques |
| STARTER-PROFILES-001 | terminé | aligner les starters avec les profils Forge |
| STARTER-CS-REPLACE-001 | terminé | Positionner Communes & Séjours comme démonstrateur avancé principal |
| ROADMAP-STARTER-MODERNIZATION-001 | terminé | Ajouter la Phase 9.1 de modernisation des starters historiques |

---

## Phase 9 — Profils de projet

**État : terminée.**

Objectif : proposer plusieurs profils au moment de créer un projet.

```bash
forge new MonProjet --profile minimal
forge new MonProjet --profile standard
forge new MonProjet --profile dynamic
forge new MonProjet --profile multilingual
```

| Profil | Contenu |
|---|---|
| minimal | Jinja + Tailwind, rien de plus |
| standard | Jinja + Tailwind + composants |
| dynamic | Jinja + Tailwind + HTMX |
| multilingual | Jinja + Tailwind + i18n |

| Ticket | Objectif |
|---|---|
| PROFILE-001 | terminé | Définir les profils officiels |
| PROFILE-002 | terminé | Ajouter option `--profile` à `forge new` |
| PROFILE-003 | terminé | Tests de génération par profil |
| PROFILE-DOC-001 | terminé | Documentation finale des profils |

---

## Phase 9.1 — Modernisation des starters historiques

**État : terminée.**

Objectif : aligner les starters historiques avec Forge actuel sans transformer tous les starters en applications complètes.

Forge dispose maintenant :

- de profils officiels ;
- d'un starter Communes & Séjours comme démonstrateur avancé principal ;
- de décisions claires sur le statut des starters historiques.

Il reste à moderniser ou clarifier les starters historiques avant la consolidation globale.

| Ticket | État | Objectif |
|---|---|---|
| STARTER-MODERNIZATION-PLAN-001 | terminé | Définir précisément les modernisations nécessaires |
| DOC-STARTERS-STRUCTURE-001 | terminé | Réorganiser la documentation des starters dans docs/starters/ |
| DOC-STARTERS-STRUCTURE-002 | terminé | Uniformiser la structure — chaque starter dans son sous-dossier index.md |
| STARTER-AUTH-MODERNIZE-001 | terminé | Aligner le starter Utilisateurs/Auth sur le socle Auth/User post-1.5.0 |
| STARTER-CONTACTS-REFRESH-001 | terminé | Rafraîchir le starter Contacts sans l'alourdir |
| STARTER-CARNET-REFRESH-001 | terminé | Rafraîchir le starter Carnet comme exemple relationnel |
| STARTER-SUIVI-LEGACY-001 | terminé | Marquer clairement le starter Suivi comme historique/legacy |
| STARTER-DOC-INDEX-001 | terminé | Clarifier l'index des starters, leurs statuts et usages recommandés |

Règle : moderniser les starters utiles, conserver les starters simples, marquer legacy ce qui est historique, sans transformer tous les starters en démonstrateurs avancés.

---

## Phase 9.5 — Consolidation Forge avant publication

**État : terminée.**

Objectif : vérifier que Forge est cohérent, stable, documenté et exploitable avant publication.

| Ticket | Objectif |
|---|---|
| CONSOLIDATION-001 | terminé | audit global architecture après Phases 4.5 à 9.1 |
| CONSOLIDATION-CLI-001 | terminé | audit cohérence CLI |
| CONSOLIDATION-DOC-001 | terminé | audit documentation / roadmap / README |
| CONSOLIDATION-TESTS-001 | terminé | audit couverture et zones fragiles |
| CONSOLIDATION-NON-OVERWRITE-001 | terminé | vérifier la préservation du code utilisateur |
| CONSOLIDATION-MODULES-001 | terminé | vérifier le cycle complet des modules |
| CONSOLIDATION-PROFILES-001 | terminé | vérifier la cohérence des profils |
| CONSOLIDATION-FRONT-001 | terminé | vérifier Tailwind / HTMX / Alpine / templates |
| CONSOLIDATION-STARTER-001 | terminé | vérifier que Communes & Séjours démontre Forge sans polluer le core |
| CONSOLIDATION-ROADMAP-001 | terminé | décider ce qui relève de Forge 2.0, Forge Design ou post-roadmap |

### Critères de sortie

Avant publication, Forge doit avoir :

- une CLI cohérente ;
- une documentation alignée avec le code ;
- une roadmap nettoyée ;
- des profils de projet stables ;
- un système de modules stabilisé ;
- un starter démonstrateur fonctionnel ;
- aucune confusion entre framework et application métier ;
- des tests complets verts ;
- une stratégie claire pour Forge 2.0.

Validation finale attendue :

```bash
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
```

---

## Phase 10 — Publication Forge 2.0

**État : terminée.**

Objectif : publier une première version réellement exploitable de Forge.

Nom recommandé :

```text
Forge 2.0 — première version publique exploitable
```

Forge 2.0 devra être :

- installable proprement ;
- documenté ;
- testé ;
- cohérent dans sa CLI ;
- stable sur son socle MVC ;
- capable de générer une application réelle ;
- accompagné d’un starter démonstrateur ;
- clair sur ses limites.

Forge 2.0 ne prétend pas être complet au sens absolu. C’est la première version exploitable comme framework MVC Python.

### Tickets Phase 10

| Ticket | État | Objectif |
|---|---|---|
| PUBLICATION-2.0-PREP-001 | terminé | préparer la publication Forge 2.0 |
| PUBLICATION-2.0-VERSION-001 | terminé | verrouiller la version 2.0.0 (forge.py, pyproject.toml, docs) |
| PUBLICATION-2.0-BUILD-001 | terminé | construire et valider le package Forge 2.0 |
| PUBLICATION-2.0-TAG-001 | terminé | créer et pousser le tag v2.0.0 |
| PUBLICATION-2.0-RELEASE-001 | terminé | créer la release GitHub depuis le tag v2.0.0 |
| PUBLICATION-2.0-POST-RELEASE-001 | terminé | documenter la publication GitHub Forge 2.0.0 |

---

## Projet compagnon — Forge Design

Forge Design dispose désormais de sa propre roadmap.

Il ne fait pas partie du cœur Forge 2.0.

Forge doit d’abord devenir publiable, documenté, testé et exploitable. Forge Design viendra ensuite comme outil graphique séparé capable de produire des templates Forge propres.

Règles :

- Forge Design ne doit jamais devenir une dépendance obligatoire de Forge ;
- Forge Design ne doit pas compenser un manque de stabilité de Forge ;
- Forge Design doit produire du code Forge lisible ;
- Forge Design ne doit pas transformer Forge en éditeur React/Vue.

---

## Phases post-Forge 2.0 — toutes livrées

Ces phases ont été livrées après publication de Forge 2.0 (v2.2.0).

### Phase 4.9 — Contrat de stabilité et production légère

| Ticket | État |
|---|---|
| APP-STABILITY-CONTRACT-001 | **livré** |
| SESSION-STORE-CONTRACT-001 | **livré** |
| SESSION-FILE-STORE-001 | **livré** |
| SESSION-MARIADB-STORE-001 | **livré** |
| RELEASE-2.2.0-001 | **livré** |

### Phase 5 — Expérience développeur (DX)

| Ticket | État |
|---|---|
| DX-DOCTOR-001 | **livré** |
| DX-PROJECT-CHECK-001 | **livré** |
| DX-PROJECT-AUDIT-001 | **livré** |
| DX-ERRORS-001 | **livré** |
| DX-HELP-001 | **livré** |
| DX-RECOVERY-001 | **livré** |

### Phase 5.5 — Debug runtime développeur

| Ticket | État |
|---|---|
| DX-RUNTIME-ERRORS-AUDIT-001 | **livré** |
| DX-RUNTIME-ERRORS-SCHEMA-001 | **livré** |
| DX-RUNTIME-ERRORS-JSONL-001 | **livré** |
| DX-RUNTIME-ERRORS-MD-001 | **livré** |

### Phase 6 — E2E / qualité

| Ticket | État |
|---|---|
| E2E-CLI-001 | **livré** |
| E2E-NON-OVERWRITE-001 | **livré** |
| E2E-STARTER-001 | **livré** |
| E2E-MODULE-001 | **livré** |
| E2E-MARIADB-001 | **livré** |
| QUALITY-COVERAGE-001 | **livré** |

### Phase 7 — Sécurité approfondie

| Ticket | État |
|---|---|
| SECURITY-AUDIT-001 | **livré** |
| SECURITY-CSRF-AUDIT-001 | **livré** |
| SECURITY-AUTH-AUDIT-001 | **livré** |
| SECURITY-COOKIES-001 | **livré** |
| SECURITY-HEADERS-001 | **livré** |
| SECURITY-UPLOADS-AUDIT-001 | **livré** |
| SECURITY-RBAC-AUDIT-001 | **livré** |
| DEPLOY-PROD-SECURITY-DOC-001 | **livré** |

### Phase 8 — Release et compatibilité

| Ticket | État |
|---|---|
| RELEASE-POLICY-001 | **livré** |
| RELEASE-DEPRECATION-001 | **livré** |
| RELEASE-COMPAT-001 | **livré** |
| RELEASE-MIGRATION-GUIDE-001 | **livré** |
| RELEASE-LTS-001 | **livré** |

### Phase 9 — Documentation avancée

| Ticket | État |
|---|---|
| DOC-STRUCTURE-001 | **livré** |
| DOC-15MIN-001 | **livré** |
| DOC-APP-COMPLETE-001 | **livré** |
| DOC-DEPLOY-ADVANCED-001 | **livré** |
| DOC-MODULE-AUTHOR-001 | **livré** |
| DOC-STARTER-AUTHOR-001 | **livré** |
| DOC-CONTRIBUTE-001 | **livré** |

### Phase 10 — API JSON légère

| Ticket | État |
|---|---|
| API-JSON-001 | **livré** |
| API-CONTROLLER-001 | **livré** |
| API-ROUTES-001 | **livré** |
| API-AUTH-001 | **livré** |
| API-DOC-001 | **livré** |

### Bloc post-Phase 10

| Ticket | État |
|---|---|
| LANDING-POST-2.2-REFRESH-001 | **livré** |
| ROADMAP-UNIFIED-001 | **livré** |
| POST-2.2-FINAL-AUDIT-001 | **livré** |
| AUTH-MFA-004 | **livré** |
| AUTH-OIDC-AUDIT-001 | **livré** |
| AUTH-SESSION-HARDENING-001 | **livré** |
| AUTH-ADMIN-UX-001 | **livré** |
| AUTH-DOC-CONSOLIDATION-001 | **livré** |
| PHASE-11-AUTH-CLOSE-001 | **livré** |
| CRUD-RBAC-UI-001 | **livré** |
| SECURITY-CACHE-001 | **livré** |
| SECURITY-COOKIES-HOST-PREFIX-001 | **livré** |
| E2E-UPLOAD-HTTP-001 | **livré** |
| SECURITY-UPLOAD-RATE-LIMIT-001 | **livré** |
| PHASE-12-SECURITY-UX-CLOSE-001 | **livré** |
| CRUD-FILTER-001 | **livré** |
| CRUD-FILTER-HTMX-001 | **livré** |
| CRUD-FILTER-DOC-001 | **livré** |

### Clôture Phase 11 — Auth avancée / durcissement applicatif

La Phase 11 consolide le parcours Auth Forge :
MFA branché dans le login (session complète seulement après code valide),
parcours OIDC audité et limites documentées, sessions durcies (validation stricte
du format `session_id`), CLI admin clarifiée avec convention `Erreur:` / `Conseil:`,
événements d'audit admin ajoutés, documentation Auth/RBAC/MFA/OIDC consolidée.

### Clôture Phase 12 — Dettes sécurité et UX applicative

La Phase 12 ferme les dettes sécurité et UX identifiées après les audits :
RBAC UI aligné avec les permissions serveur (guards `{% if can() %}` dans les
templates CRUD générés), cache des pages auth durci (`Cache-Control: no-store`
sur `/login`, `/login/mfa`, `/logout`), cookie de session préfixé `__Host-session_id`,
cycle upload multipart testé en quasi-E2E via `Application.dispatch()`, et
rate limiting upload ajouté (`core.uploads.rate_limit`, fenêtre glissante en mémoire,
10 uploads / 60 s / IP).

---

## Phase 12 — Dettes sécurité et UX applicative (close)

| Ticket | Sujet | État |
|---|---|---|
| CRUD-RBAC-UI-001 | boutons CRUD conditionnels par permission | livré |
| SECURITY-CACHE-001 | Cache-Control no-store sur pages auth | livré |
| SECURITY-COOKIES-HOST-PREFIX-001 | cookie de session préfixé `__Host-` | livré |
| E2E-UPLOAD-HTTP-001 | tests upload multipart quasi-E2E | livré |
| SECURITY-UPLOAD-RATE-LIMIT-001 | rate limiting uploads | livré |
| PHASE-12-SECURITY-UX-CLOSE-001 | clôture Phase 12 | livré |

---

## Phase 13 — CRUD avancé / expérience applicative

| Ticket | Sujet | État |
|---|---|---|
| CRUD-FILTER-001 | filtres déclaratifs CRUD (`list.filter=true`) | livré |
| CRUD-FILTER-HTMX-001 | intégration HTMX des filtres CRUD | livré |
| CRUD-FILTER-DOC-001 | consolidation documentation filtres CRUD | livré |
| CRUD-BULK-ACTIONS-AUDIT-001 | audit faisabilité actions groupées CRUD | livré |
| CRUD-BULK-DELETE-001 | suppression groupée CRUD (cases, confirmation, CSRF, RBAC) | livré |
| CRUD-SORT-001 | tri de colonnes CRUD (whitelist, HTMX, href) | livré |
| CRUD-HTMX-001 | consolidation HTMX CRUD (cible unique, cohérence) | livré |
| CRUD-EXPORT-AUDIT-001 | audit faisabilité export CSV CRUD | livré |
| CRUD-EXPORT-CSV-001 | export CSV minimal CRUD (route, modèle, contrôleur, lien, tests) | livré |
| PHASE-13-CRUD-CLOSE-001 | clôture Phase 13 CRUD avancé | livré |
| RELEASE-2.3.0-001 | release Forge 2.3.0 (tag v2.3.0, wheel, pipx) | livré |

Phase ouverte à la suite de la clôture de la Phase 12.
CRUD-FILTER-001 valide formellement la convention `list.filter=true`, les tests
et la documentation.
CRUD-FILTER-HTMX-001 améliore l'intégration HTMX : lien Réinitialiser visible
dès qu'un filtre ou une recherche est active, lien avec attributs HTMX progressifs,
fallback `method="get"` conservé, aucun JavaScript ajouté.
CRUD-FILTER-DOC-001 consolide la documentation des filtres dans reference.md :
types supportés/refusés, compatibilité HTMX, garanties SQL, limites explicites.
CRUD-BULK-ACTIONS-AUDIT-001 audite la faisabilité des actions groupées : routes
dédiées, CSRF automatique, RBAC réutilisé, IDs paramétrés SQL, pas de JS ni de
HTMX dans la première version. Recommande CRUD-BULK-DELETE-001 en premier.

Tous les tickets Phase 13 sont livrés. Phase 13 **close**.

### Clôture Phase 13 — CRUD avancé / expérience applicative

La Phase 13 consolide les CRUD générés Forge : filtres déclaratifs (`list.filter=true`),
compatibilité HTMX progressive (cible unique `#crud-results`, `hx-push-url`, fallbacks),
tri sécurisé par whitelist (`_ALLOWED_SORT`), suppression groupée minimale (cases à cocher,
confirmation, CSRF, RBAC, SQL paramétrée), export CSV filtré (`_EXPORT_LIMIT=1000`,
`_csv_escape`, `Cache-Control: no-store`), protections SQL systématiques, RBAC optionnel
et documentation associée dans `docs/reference.md`.

---

## Phase 14 — Refonte vers Forge 3.0

**État : terminée — historique (v2.4.0 → v2.10.0 → v3.0.0, puis renommée 1.0.0-beta.1 à la publication PyPI).**

Objectif : reconstruire Forge avec un cœur minimal strict, une API publique
anglophone, un packaging multi-distributions PyPI et des modules officiels
physiquement extraits du dépôt principal.

### Phase 14.1 — Durcissement pré-refonte

Tickets de sécurité, sessions, audit et statistiques livrés dans Forge 2.4.0 avant
le début des extractions.

| Ticket | Objectif |
|---|---|
| SESSIONS-CONTRACT-001 | contrat `SessionStore` pluggable, 3 backends |
| SEC-MFA-RATELIMIT-001 | rate-limit par utilisateur sur challenge et revalidation MFA |
| SEC-MFA-TOTP-REPLAY-001 | anti-replay TOTP conforme RFC 6238 §5.2 |
| MFA-SESSION-PERSISTENCE-001 | correction persistance sessions sur backends désérialisés |
| SEC-CSP-HARDEN-001 | durcissement CSP (`object-src`, `base-uri`) |
| SEC-CSP-COMPLETENESS-001 | complétion CSP (`img-src data:`, `form-action`) |
| AUTH-AUDIT-RESILIENCE-001 | `safe_log_auth_event`, compteur d'échecs observable |
| AUTH-AUDIT-PROPAGATE-001 | propagation des exceptions dans `log_auth_event` |
| SEC-MFA-REVALIDATION-IDENTITY-001 | vérification identité dans la revalidation MFA |
| SEC-MFA-SECRET-NAMING-001 | renommage `secret_hash` → `totp_secret` |
| STATS-GENERIC-EVENTS-001 | suppression constantes d'événements nommés (`PAGE_VIEW`, etc.) |
| SQL-EXAMPLES-CANONICAL-001 | API canonique `core.database.db` dans les modèles applicatifs |
| OIDC-SCOPE-CLARIFY-001 | OIDC déplacé dans `core.auth.experimental`, shims dépréciés |

### Phase 14.2 — Infrastructure Forge 3.0

Adoption formelle de la charte et mise en place du packaging multi-distributions.

| Ticket | Objectif |
|---|---|
| PACKAGING-MULTI-DIST-001 | infrastructure `packages/` — 5 distributions PyPI indépendantes |
| CHARTER-V2-ADOPTION-001 | charte philosophique v2 + ADR-003 à 007 |

### Phase 14.3 — Reconstruction du cœur minimal

Extractions physiques, suppressions et reconstruction — de v2.5.0 à v2.10.0.

| Ticket | Objectif |
|---|---|
| MFA-EXTRACT-001 | extraction `core/auth/mfa*` → `forge-mvc-mfa` |
| OIDC-REMOVE-OR-EXTRACT-001 | suppression OIDC (implémentation incomplète) |
| WORKFLOW-EXTRACT-001 | extraction `core/workflow/` → `forge-mvc-workflow` |
| STATS-EXTRACT-001 | extraction `core/stats/` → `forge-mvc-stats` |
| RBAC-EXTRACT-001 | extraction RBAC → `forge-mvc-rbac` |
| MODULES-EXPLICIT-ROUTES-001 | `forge module:routes` sans écriture dans `mvc/routes.py` |
| HASHING-PBKDF2-REMOVE-001 | suppression création PBKDF2 (`hacher_mot_de_passe`) |
| CMD-LEGACY-REMOVE-001 | suppression définitive du dossier `cmd/` legacy |
| LANG-MIGRATION-001 | API publique en anglais — ADR-003 (17 symboles) |
| AUTH-AUDIT-CLARIFY-ARCHITECTURE-001 | documentation architecture audit auth — ADR-008 |
| EXTRACTION-CLEANUP-SHIMS-001 | suppression shims compat MFA |
| CLAUDE-MD-UPDATE-001 | refonte CLAUDE.md en briefing IA durable |
| TESTS-CLASSIFY-001 | réorganisation tests en `tests/meta/` et `tests/release/` |
| DOCS-CONSOLIDATE-ROADMAPS-001 | consolidation roadmaps — 3 fichiers archivés (ticket courant) |

### Phase 14.4 — Clôture pré-3.0

*(Phase 14.4 close — tag v3.0.0 livré, renommé 1.0.0-beta.1 à la publication PyPI.)*

| Ticket | Objectif |
|---|---|
| DOCS-REFERENCE-SPLIT-001 | mise à jour des références documentaires après consolidation |

### Déférés post-3.0

| Ticket | Raison du report |
|---|---|
| HASHING-PBKDF2-DEFINITIVE-REMOVE-001 | attendre la migration complète des hashes existants |
| PACKAGING-SRC-LAYOUT-001 | réorganiser le layout source dans `packages/` |
| TESTS-CLASSIFY-DEEP-001 | découpage fin `unit/integration/generation` — priorité basse |
| OIDC-IMPLEMENT-COMPLETE-001 | ré-implémenter OIDC complet (échange de code, JWT/JWKS) |

---

## Phases futures possibles

Ces phases ne font pas encore l'objet de tickets actifs. Elles prolongent Forge
au-delà de la version 1.0.0 stable.

| Phase | Contenu |
|---|---|
| Phase 15 — Forge Design | outil graphique séparé pour générer des templates Forge |
| Phase 16 — Auth avancée | WebAuthn/passkeys, SAML, SSO entreprise |
| Phase 17 — API JSON v2 | API JSON complète, versionnée, OpenAPI |
| Phase 18 — Multi-tenant | infrastructure mutualisée optionnelle |

---

Interdictions maintenues :

- pas d’ORM complet ;
- pas de paiement intégré au cœur ;
- pas de réservation avancée intégrée au cœur ;
- pas de SaaS multi-tenant ;
- pas de marketplace plugins ;
- pas de SPA React/Vue/Svelte intégrée ;
- pas de transformation de Forge en framework API pur.

---

## Conclusion actualisée

> **Note historique** — cette section documente l'état à la clôture de la Phase 13
> et au lancement de la Phase 14 (refonte vers 3.0). La version publique actuelle
> est **Forge 1.0.0-beta.1**. Pour la trajectoire active, voir la section
> "Trajectoire officielle — 1.0.0 stable" ci-dessus.

La roadmap Forge est désormais centrée sur un objectif clair :

```text
Faire de Forge une première version publiable et exploitable.
```

Forge Design sort de cette roadmap et devient un projet compagnon séparé.

**Forge 2.2.0 était la version courante à la clôture de la Phase 13.**

- Release v2.0.0 : https://github.com/caucrogeGit/Forge/releases/tag/v2.0.0
- Release v2.0.1 : https://github.com/caucrogeGit/Forge/releases/tag/v2.0.1
- Release v2.0.2 : https://github.com/caucrogeGit/Forge/releases/tag/v2.0.2
- Release v2.1.0 : https://github.com/caucrogeGit/Forge/releases/tag/v2.1.0
- Release v2.2.0 : https://github.com/caucrogeGit/Forge/releases/tag/v2.2.0

Phases 0–10 et phases post-2.0 (4.9, 5, 5.5, 6, 7, 8, 9, 10) terminées. Phase 4.5 Auth/User complète. Phase 11 Auth avancée / durcissement applicatif close (AUTH-MFA-004, AUTH-OIDC-AUDIT-001, AUTH-SESSION-HARDENING-001, AUTH-ADMIN-UX-001, AUTH-DOC-CONSOLIDATION-001, PHASE-11-AUTH-CLOSE-001). Phase 12 Dettes sécurité et UX applicative close (CRUD-RBAC-UI-001, SECURITY-CACHE-001, SECURITY-COOKIES-HOST-PREFIX-001, E2E-UPLOAD-HTTP-001, SECURITY-UPLOAD-RATE-LIMIT-001, PHASE-12-SECURITY-UX-CLOSE-001). Phase 13 CRUD avancé en cours — CRUD-FILTER-001 livré, CRUD-FILTER-HTMX-001 livré, CRUD-FILTER-DOC-001 livré, CRUD-BULK-ACTIONS-AUDIT-001 livré (audit : route `/bulk-delete`, CSRF automatique, RBAC réutilisé, IDs paramétrés, pas de JS ni HTMX initialement, recommande CRUD-BULK-DELETE-001). CRUD-BULK-DELETE-001 livré (cases à cocher, confirmation, CSRF, RBAC, `_parse_bulk_ids`, SQL paramétrée `IN(?)`, 60 tests, docs). CRUD-SORT-001 livré (whitelist `_ALLOWED_SORT`, validation sort/direction, liens de tri HTMX + fallback href, réinitialisation page, conservation q/filtres, 42 tests, docs). CRUD-HTMX-001 livré (audit consolidation : cible unique `#crud-results`, swap `innerHTML`, `hx-push-url` cohérents sur pagination/tri/filtres/reset, fallbacks HTML présents, suppression groupée intentionnellement classique, 59 tests, docs). CRUD-EXPORT-AUDIT-001 livré (audit export CSV : route `GET /{plural}/export.csv`, export filtré avec limite 1000, RBAC via `index`, protection injection CSV, headers `Content-Type`+`Content-Disposition`+`Cache-Control`, pas de HTMX, ticket suivant `CRUD-EXPORT-CSV-001`). CRUD-EXPORT-CSV-001 livré (export CSV généré : `_EXPORT_LIMIT=1000`, `find_{plural}_for_export`, `_csv_escape`, `export_csv`, route `GET /export.csv`, lien `<a href>` classique sans HTMX, headers corrects, RBAC via `index`, 66 tests). Phase 13 CRUD avancé close (PHASE-13-CRUD-CLOSE-001) — 9 tickets livrés : filtres déclaratifs, HTMX consolidé, tri sécurisé, suppression groupée, export CSV. RELEASE-2.3.0-001 livré — Forge 2.3.0 taggé, wheel construite, version figée avant refonte profonde. Roadmap unifiée en vigueur.

Prochaine priorité immédiate *(note historique — état à la clôture de la Phase 13)* :

```text
FORGE-DESIGN-ROADMAP-001
```

Décision : Forge reste le moteur. Communes & Séjours est le démonstrateur avancé. Forge Design sera construit ensuite comme projet compagnon séparé.

### Formule de continuité

Forge doit rester :

- petit dans son cœur ;
- riche par ses briques ;
- clair dans ses générateurs ;
- fortement documenté ;
- très testé.

Une fonctionnalité peut être ambitieuse, mais elle ne doit pas alourdir inutilement le cœur du framework ni rendre son fonctionnement opaque.

---

## Historique de consolidation post-3.0

Tickets livrés pendant les phases de stabilisation 3.0 → 3.0.1, avant le
Scénario C de consolidation 3.0.2.

### Phase G — Architecture et nettoyage

| Ticket | Description courte | État |
|---|---|---|
| G1 SESSIONS-LANG-ALIGN-001 | Migration clés session FR→EN | **livré** |
| G2 AUTH-EXTRA-EXTRACT-DECISION-001 | Décision non-extraction `core/auth/` résiduel | **livré** |
| G3 DOCS-RELEASE-SECTION-AUDIT-001 | Consolidation doc release | **livré** |
| G4 DOCS-V1-V2-TERMINOLOGY-001 | Sweep terminologies V1/V2 obsolètes | **livré** |
| G5 DOCS-GETTING-STARTED-CONSOLIDATE-001 | Consolidation getting-started | **livré** |
| G6 PACKAGING-FORGE-MODULE-001 | Restructuration `forge.py` → package `forge/` | **livré** |
| G7 STARTER-AUTH-MFA-PROFILE-001 | Starter auth-mfa + page profil | **livré** |
| G8 CLI-AUTH-INIT-OIDC-SQL-001 | Retrait SQL OIDC du core | **livré** |
| SESSION-LIMITS-STATUS-AUDIT-001 | Limites MemorySessionStore formalisées | **livré** |

### Phase pré-release v3.0.1

| Ticket | Description courte | État |
|---|---|---|
| PR1 DOCS-CLI-COMMANDS-REFERENCE-001 | Doc CLI complète (53 commandes) | **livré** |
| PR2 DOCS-INSTALLATION-WINDOWS-001 | Guide installation Windows (WSL2) | **livré** |
| PR3 LANDING-SEARCH-BAR-001 | Barre de recherche landing | **livré** |
| PR4 LANDING-POSITIONNEMENT-VISIBILITY-001 | Positionnement + compteur visible | **livré** |
| PR5 DOCS-RELEASE-LOCAL-STARTERS-COUNT-001 | Doc release-local + starters 5 et 6 | **livré** |
| RELEASE-3.0.1-PATCH-STABLE-001 | Bump coordonné + tag v3.0.1 | **livré** |

**Total : 15 tickets livrés en 3.0.1.**

Voir `CHANGELOG.md` section [3.0.1] pour le détail.

---

## Scénario C — Consolidation 3.0.2

Cycle de consolidation production-ready basé sur trois audits convergents
(statique, dynamique, stratégique). Objectif : faire de Forge 3.0.2 une
release vraiment publiable PyPI, avec architecture propre, packaging
fonctionnel et documentation à jour.

### Bloquants techniques (5 tickets)

| Ticket | Description courte | État |
|---|---|---|
| T1 PYTEST-REPRODUCIBLE-001 | pytest reproductible sur clone frais | **livré** |
| T2 PACKAGING-SRC-LAYOUT-001 | Nettoyage divergence pyotp + artefacts build | **livré** |
| T2b PACKAGING-WHEEL-CONTENT-001 | Wheel publiable (894 KB vs 3 KB vide) | **livré** |
| T3 MFA-PRODUCTION-DECISION-001 | MFA Pre-Alpha retiré de `[all]` | **livré** |
| T4 MFA-SECRET-HASH-DEPRECATION-RESOLVE-001 | Retrait définitif `secret_hash` | **livré** |

### Architecture (2 tickets)

| Ticket | Description courte | État |
|---|---|---|
| T14 CORE-RBAC-PLUGIN-MECHANISM-001 | Mécanisme plugin push pour contexte Jinja | **livré** |
| T15 OIDC-EXCEPTIONS-CLEANUP-001 | Retrait 4 exceptions OIDC orphelines | **livré** |

### Documentation (6 tickets)

| Ticket | Description courte | État |
|---|---|---|
| T5 CHANGELOG-3.0.1-3.0.2-001 | Sections [3.0.1] et [3.0.2] du CHANGELOG | **livré** |
| T7 DOCS-3.0.1-VERSION-SWEEP-001 | Sweep mentions obsolètes (2.x, v3.0.0) | **livré** |
| T8 STABILITY-CONTRACT-3.0-REFRESH-001 | Contrat de stabilité refondu pour 3.x | **livré** |
| T9 CLAUDE-MD-3.0.2-REFRESH-001 | Briefing IA bumpé en 3.0.x | **livré** |
| T17 ADR-TITLES-3.0-REFRESH-001 | Décision : conserver titres ADR historiques | **livré** |
| T19 SESSION-KEYS-DOCSTRING-001 | Correction docstring "avant Forge 3.1" | **livré** |

### Reste à faire (9 tickets)

| Ticket | Description courte | État |
|---|---|---|
| T6 ROADMAP-3.0.1-3.0.2-001 | Mise à jour de cette roadmap | **livré** |
| T10 STARTER-6-DOC-001 | Documentation du starter 6 (auth-mfa) | à faire |
| T11 FORGE-HELP-COVERAGE-001 | Couverture des aides `forge --help` | **livré** |
| T12 PACKAGE-LOCK-SYNC-001 | Sync versions entre 5 pyproject | **livré** |
| T13 MFA-SECURITY-CLARIFY-001 | Clarification sécurité MFA Pre-Alpha | **livré** |
| T16 TESTS-RENAME-OBSOLETE-001 | Renommage tests obsolètes | caduc |
| T20 DOCS-FORGE-2X-SWEEP-001 | Sweep final mentions Forge 2.x dans doc | **livré** |
| T21 RELEASE-VALIDATION-GIT-001 | Validation git pré-release | **livré** |
| T22 RELEASE-3.0.2-PATCH-STABLE-001 | Bump coordonné + tag v3.0.2 | **livré** |

**Total Scénario C : 22 tickets (20 livrés, 2 caducs).**

Note : T18 (CI-COMMENTS-CLEANUP-001) initialement prévu a été intégré dans T2b
(PACKAGING-WHEEL-CONTENT-001). T16 (TESTS-RENAME-OBSOLETE-001) caduc — les renommages
avaient déjà été appliqués avant le Scénario C.

Voir `CHANGELOG.md` section [3.0.2] pour le détail.

---

## Historique de consolidation post-2.0

Tickets livrés pendant les phases de stabilisation (v2.0.0 → v2.2.0), avant les phases 5–10.

| Ticket | Phase | État |
|---|---|---|
| POST-2.0-DOC-CLEANUP-001 | Phase 2 post-2.0 | **livré** |
| POST-2.0-ROADMAP-RESTRUCTURE-001 | Phase 2 post-2.0 | **livré** |
| SECURITY-MD-001 | Phase 2 post-2.0 | **livré** |
| DEPENDENCY-SCAN-001 | Phase 2 post-2.0 | **livré** |
| RELEASE-CHECKLIST-001 | Phase 2 post-2.0 | **livré** |
| CMD-LEGACY-DEPRECATION-001 | Phase 3 post-2.0 | **livré** |
| AUTH-LEGACY-BOUNDARY-001 | Phase 3 post-2.0 | **livré** |
| CRUD-GENERATOR-SPLIT-001 | Phase 3 post-2.0 | **livré** |
| I18N-CACHE-001 | Phase 3 post-2.0 | **livré** |
| QUALITY-RUFF-001 | Phase 3 post-2.0 | **livré** |
| MODULE-LIFECYCLE-DOC-001 | Phase 3 post-2.0 | **livré** |
| MODULE-REMOVE-001 | Phase 3 post-2.0 | **livré** |

---

## Scénario D — Mini-consolidation post-audit ChatGPT 3.0.3

Suite à un retour d'audit externe sur la 3.0.3, 4 anomalies de cohérence
de release ont été identifiées et seront corrigées en 3.0.4 :

| Ticket | Description | État |
|---|---|---|
| ROADMAP-3.0.3-CURRENT-STATE-001 | Roadmap reflète l'état courant | **livré** |
| RELEASE-TESTS-CURRENT-VERSION-001 | Tests de release lisent la version depuis pyproject | **livré** |
| DEV-INSTALL-CONTRACT-FIX-001 | Ordre canonique `pip install -e .` + requirements-dev | **livré** |
| PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001 | Distinction runtime/test core-only dans charte | **livré** |

**Total : 4 tickets livrés en 3.0.4.**

Voir `CHANGELOG.md` section [3.0.4] pour le détail.

---

## Scénario E — Landing clickable (3.0.5)

| Ticket | Description | État |
|---|---|---|
| LANDING-ARTICLES-CLICKABLE-001 | 21 articles landing wrappés dans `<a href>` vers la doc | **livré** |

**Total : 1 ticket livré en 3.0.5.**

Voir `CHANGELOG.md` section [3.0.5] pour le détail.

---

## Patch final — Publication PyPI du core

| Ticket | Description | État |
|---|---|---|
| PYPI-PUBLISH-CORE-3.0.5-001 | Publier `forge-mvc` core sur PyPI, retirer extras non publiés | **livré** |

**Total : 1 ticket livré dans ce patch.**

`pipx install forge-mvc` fonctionne depuis cette version. Les 4 modules opt-in
restent en mode source-only via GitHub jusqu'à `OPTIN-PYPI-PUBLISH-001` (prévu à partir de `1.0.0-beta.5`).

Voir `CHANGELOG.md` section [1.0.0-beta.1] pour le détail.

---

## Phase 10 — Documentation et publication BaseController (close)

**Objectif** : auditer, documenter officiellement la surface publique de
`BaseController`, puis publier beta.4.

| Ticket | Description | État |
|---|---|---|
| BASE-CONTROLLER-SURFACE-AUDIT-001 | Audit de la surface publique de BaseController | **livré** |
| BASE-CONTROLLER-API-DOC-001 | Documentation officielle de l'API BaseController | **livré** |
| BETA-4-RELEASE-001 | Publication de Forge 1.0.0-beta.4 | **livré** |

**Phase 10 clôturée — Forge 1.0.0-beta.4 publié (2026-05-17).**

---

## Phase 11 — Extraction du module forge-mvc-media (close)

**Objectif** : extraire le code média applicatif (`media_repository`, `media_gallery`)
du core vers un module opt-in `forge-mvc-media`, en préservant la compatibilité
du code applicatif existant.

| Ticket | Description | État |
|---|---|---|
| MEDIA-CORE-BOUNDARY-AUDIT-001 | Audit de la frontière core média / module opt-in | **livré** |
| MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001 | Scaffold de `packages/forge-mvc-media/` | **livré** |
| MEDIA-REPOSITORY-MOVE-001 | Déplacer `media_repository` + `media_gallery` vers `forge-mvc-media` | **livré** |
| MEDIA-CRUD-INTEGRATION-OPTIN-001 | Mettre à jour les générateurs CLI pour les imports opt-in | **livré** |
| MEDIA-DOCS-MIGRATION-001 | Mettre à jour `docs/media.md` et `docs/reference/api.md` | **livré** |

---

## Phase 12 — Sécurité, résilience et préparation PyPI opt-ins (close)

| Ticket | Description | État |
|---|---|---|
| AUTH-AUDIT-LOGGER-RESILIENCE-001 | Résilience du logger d'audit auth (best-effort, non bloquant) | **livré** |
| SECURITY-HEADERS-DOC-LOCK-001 | Verrouillage documentation en-têtes de sécurité | **livré** |
| OPTIN-PYPI-NAMES-CHECK-001 | Audit des noms PyPI des packages opt-in | **livré** |
| OPTIN-PYPI-PUBLISH-PREPARE-001 | Préparer rbac/workflow/stats pour publication PyPI | **livré** |
| VERSION-SYNC-OPTIN-EXTRAS-001 | Synchroniser extras optionnels metadata core/opt-ins | **livré** |
| BETA-5-RELEASE-001 | Publication groupée core + rbac/workflow/stats | **livré** |

---

## Phase B9 — Corrections post-audit beta.8 → 1.0.0-beta.9

**Objectif** : solder les constats de l'[audit post-publication beta.8](../history/audits/audit-post-publication-beta8.md)
avant d'ouvrir les tests terrain sur une base saine.

**14 tickets**, classés par priorité décroissante :

| Ticket | Description | État |
|---|---|---|
| SECURITY-CRYPTOGRAPHY-MFA-001 | Mettre à jour `cryptography>=42,<46` → `>=46.0.7,<47` dans `forge-mvc-mfa` | **livré** |
| SECURITY-API-AUTH-COMPARE-DIGEST-001 | Remplacer `==` par `hmac.compare_digest` dans `core/security/api_auth.py` | **livré** |
| SECURITY-SESSION-COOKIE-HELPER-001 | Créer `set_session_cookie()` dans `core/security/cookies.py` | **livré** |
| SECURITY-SESSION-COOKIE-STARTERS-001 | Corriger les starters qui posent `session_id` au lieu de `__Host-session_id` | **livré** |
| HTTP-TRUSTED-PROXY-IP-001 | Lire `X-Real-IP` dans `core/http/request.py` | **livré** |
| AUTH-RATE-LIMIT-PROD-WARNING-001 | Avertir au démarrage si `MemorySessionStore` en production | **livré** |
| DOCS-PRODUCTION-LIMITS-001 | Documenter explicitement les limites de production (ThreadingHTTPServer, rate limit mono-process) | **livré** |
| CI-OPTIN-MEDIA-BUILD-001 | Ajouter `forge-mvc-media` à la matrice CI | **livré** |
| SESSION-CLEANUP-AUTO-001 | Nettoyage automatique des sessions expirées (`MemorySessionStore`) | **livré** |
| CORE-SESSION-DEDOMAIN-001 | Supprimer les noms de champs en français dans `core/security/session.py` (ADR-003) | **livré** |
| LANDING-BETA9-UPDATE-001 | Mettre à jour la landing : nav `CRUD` + `API`, aperçu beta.9, section API, opt-in media | **livré** |
| RELEASE-PACKAGE-LOCK-SYNC-001 | Synchroniser `package-lock.json` (version `3.0.0`) avec `package.json` (`1.0.0-beta.8`) | **livré** |
| DOCS-VERSION-SWEEP-BETA9-001 | Nettoyer les références `3.0.x` et `beta.4` dans les docs actives | **livré** |
| DOCS-LAUNCH-MODES-CLARIFY-001 | Ajouter une section « Comment lancer Forge ? » dans `docs/15-minutes.md` et `docs/getting-started.md` | **livré** |
| RELEASE-BETA9-001 | Publication `1.0.0-beta.9` (core + opt-ins) | **livré** |

> **Ordre de traitement** : les tickets WSGI du Bloc B9-D ci-dessous précèdent
> `DOCS-PRODUCTION-LIMITS-001` afin que la documentation de production reflète
> l'état final de l'intégration WSGI.

### Bloc B9-D — Intégration WSGI production

Ce bloc complète `WSGI-ENTRYPOINT-001` (entrée WSGI minimale déjà livrée)
pour rendre Forge exploitable derrière un serveur WSGI externe avant
`1.0.0-beta.9`, sans présenter `python app.py` comme une solution de
production publique.

| Ticket | Description | État |
|---|---|---|
| `WSGI-ENTRYPOINT-001` | Ajouter une entrée WSGI minimale (`core.wsgi.create_wsgi_app`) | **livré** |
| `WSGI-APP-FACTORY-CONFIG-001` | Garantir que l'application WSGI charge la même configuration que `app.py` | **livré** |
| `WSGI-PROD-WARNINGS-001` | Émettre les warnings production (memory store, multi-worker) aussi en contexte WSGI | **livré** |
| `WSGI-PRODUCTION-SMOKE-TESTS-001` | Ajouter des tests de cohérence WSGI production (factory + warnings + IP client) | **livré** |
| `WSGI-DEPLOY-DOCS-001` | Documenter un déploiement WSGI minimal derrière reverse proxy | **livré** |

### Bloc B9-C — Stabilisation CLI / aide développeur

Série menée en parallèle des corrections sécurité, intégrée à B9 pour que
l'aide `--help` / `-h` de toutes les commandes Forge soit fiable et sans
effet de bord avant `1.0.0-beta.9`.

Audit initial (62 commandes) puis dispatcher central, puis enrichissement
groupe par groupe. **Série close** : 100 % des commandes dispatchées par
`forge.py` sont classifiées (45 aide riche, 8 argparse natives, 9 manuelles,
0 manquant). Garde-fou méta `tests/meta/test_cli_help_flags_closing_audit_001.py`
verrouille toute régression. Détail dans
[`docs/history/audits/cli-help-flags-closing-audit-001.md`](../history/audits/cli-help-flags-closing-audit-001.md).

| Ticket | Description | État |
|---|---|---|
| CLI-HELP-FLAGS-AUDIT-001 | Auditer le support `--help` des 62 commandes CLI Forge | **livré** |
| CLI-HELP-FLAGS-DISPATCHER-001 | Intercepter `--help` / `-h` au dispatcher avant exécution métier | **livré** |
| CLI-HELP-FLAGS-INIT-COMMANDS-001 | Enrichir l'aide des 6 commandes `*:init` critiques | **livré** |
| CLI-HELP-FLAGS-SCHEMA-RBAC-001 | Enrichir l'aide des 4 commandes schema / RBAC | **livré** |
| CLI-HELP-FLAGS-PUBLIC-PAGES-001 | Enrichir l'aide des 5 commandes `make:public-*` | **livré** |
| CLI-HELP-FLAGS-MAIL-001 | Enrichir l'aide des 4 commandes mail restantes | **livré** |
| CLI-HELP-FLAGS-MIGRATIONS-001 | Enrichir l'aide des 3 commandes migration restantes | **livré** |
| CLI-HELP-FLAGS-PROJECT-DIAGNOSTICS-001 | Enrichir l'aide des 4 commandes de diagnostic projet | **livré** |
| CLI-HELP-FLAGS-ENTITY-MODEL-CRUD-001 | Enrichir l'aide des 5 commandes entité / modèle / CRUD | **livré** |
| CLI-HELP-FLAGS-AUTH-COMPLETION-001 | Enrichir l'aide des 5 commandes Auth restantes | **livré** |
| CLI-HELP-FLAGS-REMAINING-MINOR-001 | Enrichir l'aide des 9 dernières commandes génériques (sync, build, new, starter, js:init, docs, i18n, deploy) | **livré** |
| CLI-HELP-FLAGS-CLOSING-AUDIT-001 | Audit final + garde-fou méta de classification (125 tests) | **livré** |

**Total Bloc B9-C : 12 tickets livrés.** Série officiellement close —
plus de tickets `CLI-HELP-FLAGS-*` prévus.

---

## Phase B10 — Stabilisation post-beta.9 / pré-RC

**Objectif** : phase corrective post-publication `1.0.0-beta.9`. Remettre la
base en état strictement vert (4 tests rouges, validateur PEP 440 / SemVer,
documentation opt-ins PyPI) puis durcir les derniers points sensibles (headers
WSGI, isolation tests opt-in, défense uploads, validation MFA au boot) avant
d'envisager une release candidate.

L'audit post-publication beta.9 a identifié 16 tickets répartis en
4 catégories : bloquants immédiats, critiques pré-RC, durcissement,
et clôture.

### Bloquants immédiats (3 tickets)

| Ticket | Statut | Rôle |
|---|---|---|
| `AUTH-SESSION-HARDENING-TESTS-ALIGN-001` | **livré** | Corriger les 4 tests rouges dans `tests/test_auth_session_hardening.py` après l'évolution du contrat session `first_name` / `last_name` (cf `CORE-SESSION-DEDOMAIN-001`). |
| `RELEASE-VALIDATE-PEP440-SEMVERSION-001` | **livré** | Rendre `tools/release-validate.sh` compatible avec `1.0.0-beta.x` côté SemVer public et `1.0.0bx` côté PEP 440. |
| `DOCS-OPTINS-PYPI-BETA9-SWEEP-001` | **livré** | Corriger les docs indiquant encore que `forge-mvc-mfa` / `forge-mvc-media` ne sont pas publiés alors que les opt-ins beta.9 sont disponibles sur PyPI. |

### Critiques pré-RC (4 tickets)

| Ticket | Statut | Rôle |
|---|---|---|
| `WSGI-SECURITY-HEADERS-001` | **livré** | Garantir les headers de sécurité (`X-Frame-Options`, `X-Content-Type-Options`, HSTS, Referrer-Policy, Permissions-Policy, CSP) dans le chemin WSGI via un helper ou middleware Forge, puis documenter l’articulation avec le reverse proxy. |
| `TESTS-OPTIN-IMPORTORSKIP-001` | **livré** | Protéger les tests opt-in avec `pytest.importorskip(...)` ou un mécanisme équivalent pour préserver une installation core-only. |
| `CI-PAGES-MKDOCS-STRICT-001` | **livré** | Passer le workflow GitHub Pages en `mkdocs build --strict`. |
| `DEPENDENCY-AUDIT-RELEASE-GUARD-001` | **livré** | Décider si l'audit de dépendances (CVE) doit devenir bloquant pour les releases. |

### Durcissement (7 tickets)

| Ticket | Statut | Rôle |
|---|---|---|
| `UPLOADS-SYMLINK-DEFENSE-001` | **livré** | Vérifier par tests la défense contre les symlinks dans `uploads/` et statics, puis corriger si nécessaire (`is_symlink()` / `resolve(strict=True)`). |
| `MFA-SECRET-KEY-BOOT-VALIDATION-001` | **livré** | Valider au boot la configuration `FORGE_MFA_SECRET_KEY` quand MFA est installé ou activé. |
| `APP-PY-PROD-HOST-GUARD-001` | **livré** | Empêcher une exposition accidentelle de `python app.py` en production, notamment lorsque `APP_ENV=prod` et que `APP_HOST` cible une interface publique (`0.0.0.0`, `::`, ou équivalent). |
| `DOCS-CLI-COMMANDS-EXAMPLES-RESTRUCTURE-001` | **livré** | Réorganiser la référence CLI et ajouter des exemples d'utilisation par scénarios. |
| `DOCS-IMPORTS-VALIDITY-SWEEP-001` | **livré** | Corriger les imports obsolètes ou invalides dans les exemples de documentation (ex. `from core.auth import is_mfa_enabled` → `from forge_mvc_mfa import ...`). |
| `DOCS-SITE-ARTIFACT-POLICY-001` | à faire | Clarifier que `docs/` est la source MkDocs officielle et que `site/` est uniquement un artefact généré localement par `mkdocs build`, ignoré par Git et supprimable sans perte. |
| `TESTS-AUTOUSE-FIXTURES-AUDIT-001` | **livré** | Auditer les fixtures `autouse` hors `conftest.py` pour limiter les contaminations d'état global (cas révélé par `test_configurable_session_store_001` lors de B9). |

### Clôture (2 tickets)

| Ticket | Statut | Rôle |
|---|---|---|
| `B10-CLOSING-AUDIT-001` | à faire | Relancer l'audit complet après livraison des corrections B10. |
| `RELEASE-BETA10-001` | à faire | Préparer une release corrective `1.0.0-beta.10` si tous les contrôles sont verts. |

### Ordre officiel recommandé

1. `AUTH-SESSION-HARDENING-TESTS-ALIGN-001`
2. `RELEASE-VALIDATE-PEP440-SEMVERSION-001`
3. `DOCS-OPTINS-PYPI-BETA9-SWEEP-001`
4. `WSGI-SECURITY-HEADERS-001`
5. `TESTS-OPTIN-IMPORTORSKIP-001`
6. `CI-PAGES-MKDOCS-STRICT-001`
7. `DEPENDENCY-AUDIT-RELEASE-GUARD-001`
8. `UPLOADS-SYMLINK-DEFENSE-001`
9. `MFA-SECRET-KEY-BOOT-VALIDATION-001`
10. `APP-PY-PROD-HOST-GUARD-001`
11. `DOCS-CLI-COMMANDS-EXAMPLES-RESTRUCTURE-001`
12. `DOCS-IMPORTS-VALIDITY-SWEEP-001`
13. `DOCS-SITE-ARTIFACT-POLICY-001`
14. `TESTS-AUTOUSE-FIXTURES-AUDIT-001`
15. `B10-CLOSING-AUDIT-001`
16. `RELEASE-BETA10-001`

**Total Phase B10 : 16 tickets prévus.**

### Corrections terrain hors-audit (livrées en cours de phase)

Tickets résolvant des problèmes découverts en condition réelle pendant la
phase B10, hors du périmètre de l'audit initial. Ne sont pas comptés dans
les 15 tickets ci-dessus.

| Ticket | Statut | Rôle |
|---|---|---|
| `APP-PY-TLS-HANDSHAKE-PER-THREAD-001` | **livré** | Corriger le blocage TLS de la boucle d'accept dans `app.py` — handshake TLS exécuté dans le thread du client via `TLSThreadingHTTPServer`, borné par `TLS_HANDSHAKE_TIMEOUT = 10s`. Découvert terrain (VS Code Remote SSH + certificat auto-signé non encore accepté). |
| `APP-PY-TLS-HANDSHAKE-DOCS-001` | **livré** | Documenter le correctif TLS via ADR-015 et enrichir la docstring de `TLSThreadingHTTPServer` pour empêcher une future régression par « simplification ». |

---

## Règle de mise à jour des roadmaps

À partir de la séparation des roadmaps (DOC-ROADMAP-SPLIT-001) :

- tout ticket concernant **Forge** — framework, core, CLI, générateurs, modules, starters, documentation Forge, publication Forge — met à jour `docs/roadmap/forge-roadmap.md` ;
- tout ticket concernant **Forge Design** — modèle JSON, éditeur graphique, prévisualisation, export, interface — met à jour `docs/roadmap/forge-design-roadmap.md` ;
- un ticket ne met à jour les deux roadmaps que s'il modifie explicitement la frontière entre Forge et Forge Design ;
- chaque ticket doit indiquer dans sa section Documentation quelle roadmap est concernée.

Exemple de section attendue dans les tickets Forge :

```text
## Roadmap à mettre à jour
Mettre à jour uniquement : docs/roadmap/forge-roadmap.md
Ne pas modifier : docs/roadmap/forge-design-roadmap.md
```

Forge ne dépend pas de Forge Design. Forge Design n'est pas dans la roadmap Forge.
