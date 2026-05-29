# Roadmap Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette roadmap concerne uniquement **Forge**, le framework MVC Python : cœur, CLI, générateurs, modules, starters, documentation, tests et publication.

Forge Design est désormais traité dans une roadmap séparée.

> **Note** : Ce document contient l'historique de développement interne pré-publication.
> La version publique actuelle est **Forge 1.0.0-beta.11**.

---

## État actuel — Forge 1.0.0-beta.11

**Tag courant : `v1.0.0-beta.11` (2026-05-25)**

Précédent : v1.0.0-beta.9 (2026-05-24), v1.0.0-beta.8 (2026-05-22), v1.0.0-beta.7 (2026-05-22), v1.0.0-beta.6 (2026-05-21), v1.0.0-beta.5 (2026-05-17), v1.0.0-beta.3 (2026-05-16), v1.0.0-beta.2 (2026-05-16), v1.0.0-beta.1 (2026-05-15), v3.0.5 (2026-05-14), v3.0.4 (2026-05-14), v3.0.3 (2026-05-14), v3.0.2 (2026-05-13), v3.0.1 (2026-05-12), v3.0.0 (2026-05-12).

**Statut : v1.0.0-beta.11 publiée (core + 5 opt-ins). Phase B10 close : 20 tickets livrés couvrant stabilisation post-beta.9, WSGI headers partagés, MFA secret key boot validation, défense symlinks, app.py prod guard, audits dépendances bloquants en release, identité publique alignée (Roger Lequette / forgemvc@gmail.com), politique DB_ADMIN_* clarifiée, validation release indépendante du PATH, convention de tag SemVer publique verrouillée. Audit pré-release `B10-CLOSING-AUDIT-001` validé GO.**

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
| DOCS-LAUNCH-MODES-CLARIFY-001 | Ajouter une section « Comment lancer Forge ? » dans `docs/15-minutes.md` (renommé en `docs/bonjour-forge.md` par `DX-DOCS-BONJOUR-FORGE-CLOSE-001`) et `docs/getting-started.md` | **livré** |
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

## Phase B10 — Stabilisation post-beta.9 / pré-release beta.10

**Objectif** : phase corrective post-publication `1.0.0-beta.9`. Remettre la
base en état strictement vert (tests rouges, validateur PEP 440 / SemVer,
documentation opt-ins PyPI) puis durcir les derniers points sensibles (headers
WSGI, isolation tests opt-in, défense uploads, validation MFA au boot, garde
prod sur `app.py`, identité publique alignée) avant la release corrective
`1.0.0-beta.11`.

La phase B10 consolide les corrections issues de l'audit post-beta.9, puis
ajoute plusieurs tickets de durcissement et de cohérence release apparus
pendant la stabilisation. Les tickets sont regroupés par rôle :

* **Bloquants immédiats** — fait passer la suite de tests au vert
* **Critiques pré-RC** — durcissements indispensables avant toute release
* **Durcissement et garde-fous** — qualité, défenses en profondeur,
  cohérence documentaire et tests méta
* **Cohérence release** — robustesse de l'outillage de validation et de la
  roadmap elle-même
* **Clôture** — audit final + tag `beta.10`

### Bloquants immédiats

| Ticket | Statut | Rôle |
|---|---|---|
| `AUTH-SESSION-HARDENING-TESTS-ALIGN-001` | **livré** | Corriger les 4 tests rouges dans `tests/test_auth_session_hardening.py` après l'évolution du contrat session `first_name` / `last_name` (cf `CORE-SESSION-DEDOMAIN-001`). |
| `RELEASE-VALIDATE-PEP440-SEMVERSION-001` | **livré** | Rendre `tools/release-validate.sh` compatible avec `1.0.0-beta.x` côté SemVer public et `1.0.0bx` côté PEP 440. |
| `DOCS-OPTINS-PYPI-BETA9-SWEEP-001` | **livré** | Corriger les docs indiquant encore que `forge-mvc-mfa` / `forge-mvc-media` ne sont pas publiés alors que les opt-ins beta.9 sont disponibles sur PyPI. |

### Critiques pré-RC

| Ticket | Statut | Rôle |
|---|---|---|
| `WSGI-SECURITY-HEADERS-001` | **livré** | Garantir les headers de sécurité (`X-Frame-Options`, `X-Content-Type-Options`, HSTS, Referrer-Policy, Permissions-Policy, CSP) dans le chemin WSGI via un helper ou middleware Forge, puis documenter l’articulation avec le reverse proxy. |
| `TESTS-OPTIN-IMPORTORSKIP-001` | **livré** | Protéger les tests opt-in avec `pytest.importorskip(...)` ou un mécanisme équivalent pour préserver une installation core-only. |
| `CI-PAGES-MKDOCS-STRICT-001` | **livré** | Passer le workflow GitHub Pages en `mkdocs build --strict`. |
| `DEPENDENCY-AUDIT-RELEASE-GUARD-001` | **livré** | Décider si l'audit de dépendances (CVE) doit devenir bloquant pour les releases. |

### Durcissement et garde-fous

| Ticket | Statut | Rôle |
|---|---|---|
| `UPLOADS-SYMLINK-DEFENSE-001` | **livré** | Vérifier par tests la défense contre les symlinks dans `uploads/` et statics, puis corriger si nécessaire (`is_symlink()` / `resolve(strict=True)`). |
| `MFA-SECRET-KEY-BOOT-VALIDATION-001` | **livré** | Valider au boot la configuration `FORGE_MFA_SECRET_KEY` quand MFA est installé ou activé. |
| `APP-PY-PROD-HOST-GUARD-001` | **livré** | Empêcher une exposition accidentelle de `python app.py` en production, notamment lorsque `APP_ENV=prod` et que `APP_HOST` cible une interface publique (`0.0.0.0`, `::`, ou équivalent). |
| `DOCS-CLI-COMMANDS-EXAMPLES-RESTRUCTURE-001` | **livré** | Réorganiser la référence CLI et ajouter des exemples d'utilisation par scénarios. |
| `DOCS-IMPORTS-VALIDITY-SWEEP-001` | **livré** | Corriger les imports obsolètes ou invalides dans les exemples de documentation (ex. `from core.auth import is_mfa_enabled` → `from forge_mvc_mfa import ...`). |
| `DOCS-SITE-ARTIFACT-POLICY-001` | **livré** | Clarifier que `docs/` est la source MkDocs officielle et que `site/` est uniquement un artefact généré localement par `mkdocs build`, ignoré par Git et supprimable sans perte. |
| `TESTS-AUTOUSE-FIXTURES-AUDIT-001` | **livré** | Auditer les fixtures `autouse` hors `conftest.py` pour limiter les contaminations d'état global (cas révélé par `test_configurable_session_store_001` lors de B9). |
| `LANDING-CONTACT-NAV-FORM-001` | **livré** | Ajouter Contact à la navigation landing, créer une section formulaire vers `forgemvc@gmail.com`, et aligner l'identité publique Forge sur Roger Lequette. |
| `ENV-PROD-DB-ADMIN-SECRETS-POLICY-001` | **livré** | Clarifier que les secrets MariaDB admin/root ne doivent pas être stockés dans l'environnement runtime de production ; réserver `DB_ADMIN_*` au provisioning CLI ou à un fichier local non commité. |

### Cohérence release

| Ticket | Statut | Rôle |
|---|---|---|
| `RELEASE-VALIDATE-PATH-ROBUSTNESS-001` | **livré** | Rendre `tools/release-validate.sh` plus robuste en utilisant un interpréteur Python explicite (`PYTHON_BIN`) au lieu d'un `PATH` implicite. |
| `ROADMAP-B10-CONSISTENCY-SWEEP-001` | **livré** | Nettoyer la cohérence de la roadmap B10 avant l'audit final : compteurs, sections, statuts et tickets ajoutés en cours de phase. |
| `RELEASE-TAG-CONVENTION-TEST-ALIGN-001` | **livré** | Aligner `tests/meta/test_release_current_version_001.py` sur la convention de tag SemVer Forge (`v1.0.0-beta.x` et non `v1.0.0bx`). |

### Clôture

| Ticket | Statut | Rôle |
|---|---|---|
| `B10-CLOSING-AUDIT-001` | **livré** | Audit final B10 réalisé (`docs/history/audits/audit-pre-release-beta10.md`) ; décision **GO** pour `RELEASE-BETA10-001`. |
| `RELEASE-BETA10-001` | **livré** | Release corrective `1.0.0-beta.11` préparée (2026-05-25) — bump versions (core + 4 opt-ins), CHANGELOG, build/twine/install isolé OK ; tag `v1.0.0-beta.11` créé. Push et publication PyPI conditionnés à validation explicite. |
| `INSTALL-DOCS-STRUCTURE-001` | **livré** | Réorganisation propre des parcours d'installation sous `docs/install/` : `git mv` de `installation.md`, `installation-pipx.md`, `installation-developpement.md`, `installation-mariadb.md`, `installation-vm-debian.md`, `installation-windows.md`, `installation-github.md` vers `docs/install/{index,pipx,core-dev,mariadb,vm-debian,windows,github}.md` (historique préservé). Création de `docs/install/index.md` (aiguillage utilisateur ↔ développeur core) et `docs/install/production.md` (entrée courte vers `wsgi-deployment.md` / `production-limits.md` / `deployment.md`). Mise à jour de `mkdocs.yml` (section Installation reconstruite), des liens internes dans toute la doc active (`auth.md`, `bonjour-forge.md`, `getting-started.md`, `guide.md`, `pdf.md`, `rbac.md`, `reference/api.md`, `reference/cli-commands.md`, `release-policy.md`, starters), de la source landing (URLs `install/pipx/` + `install/core-dev/`) et de 10 tests méta. Test méta dédié : `tests/meta/test_install_docs_structure_001.py` (31 cas — existence, aiguillage, anciens chemins absents, landing, mkdocs nav, mkdocs strict). Validations : pytest meta, ruff, mkdocs --strict, git diff --check, forge sync:landing --check. |
| `LANDING-PUBLIC-CONTRACT-REALIGN-001` | **livré** | Réalignement de la landing canonique sur son contrat public réel après modifications manuelles. Correction HTML : ajout des 2 `</div>` manquants en section Installation et uniformisation du design de la card Production (`landing-panel`, `<pre>` réindenté, suppression de `flex flex-wrap` et de 3 CTA juxtaposés — un seul CTA principal vers `install/production`, les 3 guides cités en ligne). Aucune card d'installation n'utilise `md:col-span-2`. Décisions de suppression assumées et documentées dans les tests : 5e card « Bonjour Forge » de la section Installation (le starter `welcome` reste dans Starters), section FAQ et bloc « Stack technos » (Python/MariaDB/Jinja2/HTMX/Alpine.js/Tailwind + URLs externes), compteur « 12 000 tests » du Hero. Tests réalignés : `test_landing_install_cards_001.py` (5→4 cards, vérification `md:col-span-2` interdit), `test_landing_post_2_2_refresh.py::test_phases_recentes_mentionnees` (phrasing aligné sur les 4 cards Installation actuelles : `forge run`, Windows + WSL, pipx, Développement du core, Production — WSGI, Bienvenue dans Forge), `test_landing_public_contract.py::test_modules_description_wording` (chapeau « Modules officiels opt-in installables séparément » à la place de l'ancien « publication PyPI est progressive »), `test_docs_landing_page_3_0_001.py` (FAQ + Stack + 12 000 tests). `forge sync:landing` régénéré. Validations : pytest meta, ruff, mkdocs --strict, git diff --check, forge sync:landing --check. |

### Ordre de traitement

L'ordre de réalisation suit l'ordre des sections ci-dessus : bloquants
immédiats d'abord (pour repasser au vert), puis critiques pré-RC,
durcissement, cohérence release et enfin clôture. La numérotation rigide
qui figurait dans cette section a été retirée — l'ordre des sections
suffit, et la liste évoluait à chaque ajout de ticket en cours de phase
(`ROADMAP-B10-CONSISTENCY-SWEEP-001`).

### Corrections terrain hors-audit (livrées en cours de phase)

Tickets résolvant des problèmes découverts en condition réelle pendant la
phase B10, hors du périmètre de l'audit initial. Indépendants des
sections ci-dessus.

| Ticket | Statut | Rôle |
|---|---|---|
| `APP-PY-TLS-HANDSHAKE-PER-THREAD-001` | **livré** | Corriger le blocage TLS de la boucle d'accept dans `app.py` — handshake TLS exécuté dans le thread du client via `TLSThreadingHTTPServer`, borné par `TLS_HANDSHAKE_TIMEOUT = 10s`. Découvert terrain (VS Code Remote SSH + certificat auto-signé non encore accepté). |
| `APP-PY-TLS-HANDSHAKE-DOCS-001` | **livré** | Documenter le correctif TLS via ADR-015 et enrichir la docstring de `TLSThreadingHTTPServer` pour empêcher une future régression par « simplification ». |

---

## Phase post-beta.10 — Point d'entrée unifié, inspectabilité, DX et premier contact

Petite série de tickets qui remplace les deux entrées historiques
(`python app.py` et `scripts/dev-server.sh`) par une commande officielle
unique `forge run`, ajoute l'autoreload développement, amorce la
convention d'inspection des classes API publiques (`Request`,
`Response`), aligne les squelettes générés sur cette convention pour que
l'autocomplétion fonctionne par défaut, rend les erreurs de rendu de
template pédagogiques en développement, et repositionne le starter
d'entrée autour de « Bonjour Forge » pour que le premier contact passe
par `Response.text(...)` avant `BaseController.render(...)`.
L'intégration WSGI/Gunicorn et le live reload navigateur restent hors
série.

| Ticket | Statut | Rôle |
|---|---|---|
| `FORGE-RUN-COMMAND-001` | **livré** | Commande `forge run` officielle : lit `APP_ENV`, lance le serveur de développement en `dev` (délégation à `scripts/dev-server.sh` si présent, sinon `python app.py`) et refuse le serveur intégré en `prod` en affichant la stratégie WSGI recommandée. |
| `DEV-SERVER-AUTORELOAD-001` | **livré** | Superviseur d'autoreload (`forge_cli.dev_reloader`) : `forge run` (dev, défaut) spawne `python app.py`, polling `stat()` sur `app.py`, `config.py`, `env/dev`, `mvc/**/*.{py,html,json,sql}` et `core/**/*.py`, redémarrage propre (`terminate` + `wait` + respawn) sur changement. Stdlib uniquement (pas de `watchfiles`/`watchdog`). Désactivable via `--no-reload` (chemin legacy `scripts/dev-server.sh`). Prod : inchangé (refus + message WSGI). |
| `API-INSPECTABLE-OBJECTS-CONVENTION-001` | **livré** | Convention pour les classes API publiques inspectables. Premier lot livré : `Request` (accesseurs `param/header/form/json/file/route_param`, propriété `.data` avec masquage Authorization/Cookie/password/csrf/token/api_key/secret) et `Response` (constructeurs `text/html/json/debug`, propriétés `.data` / `.cookies`, dump masqué en dev, refus 404 en prod). Convention documentée dans `docs/reference/http.md` ; audit des classes restantes (`UploadedFile`, `RouteEntry`, `Form`, `Session`) reporté à des tickets dédiés. |
| `DX-TYPED-SKELETONS-001` | **livré** | Squelettes générés typés pour l'autocomplétion Pylance/VS Code : imports `Request`/`Response` automatiques + annotation `def <action>(request: Request) -> Response:` sur toutes les actions publiques. Couvre le starter `welcome`, le générateur CRUD (`forge make:crud`), les générateurs `make:public-page/list/show/form/contact` et les contrôleurs livrés par les 6 starters (`welcome`, `contact-simple`, `carnet-contacts`, `suivi-comportement-eleves`, `communes-sejours`, `utilisateurs-auth`, `auth-mfa`). Helpers internes (`_list_context`, `_parse_*`) volontairement laissés non typés. |
| `DX-RENDER-ERROR-001` | **livré** | Erreur développeur claire quand `BaseController.render("bonjour", request=request)` cible une vue inexistante. Nouvelle exception interne `core.templating.errors.TemplateNotFoundError`, re-raise par `Jinja2Renderer`, formatage centralisé dans `core.http.helpers.html` : en `APP_ENV=dev`, réponse `text/plain` 500 pédagogique citant `render()` + `Response.text(...)` + `Response.debug(...)` + exemples valides ; en `APP_ENV=prod`, réponse minimale « Erreur serveur. » sans fuite du nom de template ni du chemin `mvc/views/`. Aucun stacktrace exposé dans aucun mode. |
| `STARTER-BONJOUR-FORGE-001` | **livré** | Refonte pédagogique du starter d'entrée (`forge new --starter welcome`, alias `bonjour` / `bonjour-forge` / `bienvenue` / `7`). Nouveau titre public « Bonjour Forge ». Progression : `index` retourne désormais `Response.text("Bonjour Forge")` (zéro template), nouvelles routes `/welcome/greet?name=…` (`request.param(...)`) et `/welcome/inspect` (`Response.debug(request.data)`), puis introduction de `BaseController.render(...)` via `/welcome/cycle` et les vues HTML existantes. Vue `welcome/index.html` retirée (remplacée par `Response.text`). Doc `docs/starters/welcome/index.md` repositionnée autour de cette progression, `docs/starters/index.md` mis à jour. Signatures typées `request: Request -> Response` conservées. |
| `DX-DEBUG-DUMP-HTML-001` | **livré** | Rendu HTML pédagogique pour `Response.debug(obj)` en `APP_ENV=dev`. Nouveau module `core.http.debug_dumper` (`render_debug_html(obj)` + `MAX_DEPTH=5`). En dev : `text/html; charset=utf-8`, titre « Debug Forge », normalisation `.data` → conteneur natif → `type + repr`, masquage des clés sensibles (mêmes règles que `request.data`), échappement HTML systématique, profondeur bornée (`<max depth reached>`), détection des cycles (`<cycle detected>`). Comportement prod inchangé (404 minimal, aucune fuite). Tests : `tests/test_dx_debug_dump_html_001.py` (41 cas). API publique `Response.debug(obj)` inchangée — seul le rendu interne en dev change. |
| `DX-DOCS-BONJOUR-FORGE-CLOSE-001` | **livré** | Clôture documentaire de la phase beta 11 DX. Renommage de `docs/15-minutes.md` en `docs/bonjour-forge.md` et refonte du contenu autour du parcours développeur livré : `forge run` → route → contrôleur → `Response.text("Bonjour Forge")` → `request.param(...)` → `Response.debug(request.data)` → `BaseController.render(...)`. Différence `Response.text(...)` vs `BaseController.render(...)` documentée. Navigation MkDocs alignée (« Bonjour Forge »), liens internes corrigés (`docs/getting-started.md`, `docs/app-complete-tutorial.md`, `docs/lts-policy.md`). Tests méta migrés : `tests/meta/test_doc_15min.py` renommé en `tests/meta/test_doc_bonjour_forge.py` et adapté, `tests/meta/test_getting_started_3_0_001.py` et `tests/meta/test_meta_tests_root_migration_001.py` mis à jour. Les mentions historiques de « 15 minutes » dans `docs/history/`, `CHANGELOG.md` et la roadmap restent telles quelles (mémoire brute du passé). |
| `INSTALL-WSL-DOCS-001` | **livré** | Guide officiel d'installation Windows 11 + WSL Ubuntu 24.04 ajouté à `docs/install/windows-wsl.md` (création du sous-dossier `docs/install/` pour ce ticket — réorganisation plus large reportée). Couvre WSL Ubuntu 24.04, VS Code Remote WSL, dépendances Linux, Node.js 20 LTS, `pipx install --pip-args="--pre" forge-mvc` (avertissement : ne pas installer le paquet `forge`), configuration Git, MariaDB, création du projet avec `forge new <nom> --starter welcome` dans le HOME Linux WSL (jamais sous `/mnt/c`), `forge db:init`, `forge doctor`, lancement via `forge run` (`python app.py` reste mentionné en note bas niveau uniquement), vérification des routes `/welcome` / `/welcome/greet` / `/welcome/inspect`, FAQ problèmes fréquents, validation finale en tableau. Version Forge gérée via la variable documentaire `{{forge_version}}` (pas de version figée). Navigation MkDocs mise à jour (`Premiers pas → Installer Forge → Windows + WSL (parcours complet)`). Liens internes ajoutés depuis `docs/bonjour-forge.md` et `docs/getting-started.md`. Tests méta : `tests/meta/test_install_windows_wsl_docs_001.py` (10 cas). |
| `INSTALL-WSL-DOCS-FIELD-FIX-001` | **livré** | Corrections terrain sur `docs/install/windows-wsl.md` avant mise en avant landing. Parcours MariaDB refondu : création d'un compte `forge_admin@localhost` dédié à la place de `root` (root MariaDB sous WSL est accessible via `sudo mariadb` mais ne fonctionne pas de façon fiable depuis `env/dev` et exposerait le mot de passe root). Bloc Python `secrets` qui met à jour `env/dev` avec deux mots de passe aléatoires 24 caractères (`DB_ADMIN_PWD` et `DB_APP_PWD`). Bloc SQL appliquant `CREATE USER IF NOT EXISTS` + `ALTER USER ... IDENTIFIED BY` pour rendre le tutoriel rejouable (le `CREATE USER IF NOT EXISTS` seul ne réinitialise pas le mot de passe d'un compte existant). Convention de dossier uniformisée `~/dev/` → `~/Projets/`. Section « Problèmes fréquents » renforcée : « MariaDB n'est pas actif », « `Access denied for user 'forge_admin'@'localhost'` », « `forge db:init` affiche Connexion MariaDB admin impossible », « Ne pas commiter les secrets DB ». `forge run` reste la commande de lancement principale, `--starter welcome` et les routes `/welcome*` restent en place. Tests méta enrichis (`TestForgeAdminAccount`, 12 cas supplémentaires) — total 42 cas. |
| `LANDING-INSTALL-CARDS-001` | **livré** | Section « Installer Forge selon votre usage » de la landing canonique (`mvc/views/landing/index.html`) refondue en 5 cards distinctes : (1) **Bonjour Forge** → `docs/bonjour-forge.md` ; (2) **Windows + WSL** → `docs/install/windows-wsl.md` ; (3) **Utilisateur du framework — pipx** → `docs/installation-pipx.md`, avec mise en avant explicite de `pipx install --pip-args="--pre" forge-mvc` et avertissement « Ne pas installer le paquet `forge` » ; (4) **Développement du core** → Option A retenue : card avec label « Documentation en cours de consolidation », lien neutre vers `docs/installation-developpement.md` (référence partielle), renvoie le ticket d'audit à venir `INSTALL-CORE-DEV-DOCS-AUDIT-001` ; (5) **Production — WSGI + Gunicorn + reverse proxy** (pleine largeur) → `docs/wsgi-deployment.md` + `docs/production-limits.md` + `docs/deployment.md`, avec note explicite « `python app.py` et `forge run` sont des outils de développement — pas d'exposition publique ». `docs/index.html` régénéré via `forge sync:landing` (banner GENERE PAR conservé). Aucun lien cassé introduit (toutes les cibles existent et sont testées). Tests méta : `tests/meta/test_landing_install_cards_001.py` (35 cas — sync, sections, contenu par card, cibles, build strict). |
| `INSTALL-CORE-DEV-DOCS-AUDIT-001` | **livré** | Consolidation de `docs/installation-developpement.md` (37 → ~190 lignes) après audit terrain du dépôt réel. Page restructurée en 9 sections couvrant : (1) tableau comparatif **utilisateur framework vs développeur core** avec avertissement explicite « Ne pas utiliser `pipx` pour développer le core » ; (2) prérequis (Python 3.12+, MariaDB pour E2E uniquement, Node optionnel) ; (3) `git clone` (URL HTTPS officielle + variante SSH) ; (4) `python -m venv` ; (5) `pip install -r requirements-dev.txt` — parcours principal — qui inclut `requirements.txt` + outils dev + 5 modules opt-in du monorepo en éditable (variante minimale `pip install -e .` aussi documentée pour profilage) ; (6) **les 5 validations canoniques avant commit** : `python -m pytest -x -q`, `python -m compileall -q .`, `ruff check .`, `mkdocs build --strict`, `git diff --check` (+ option E2E MariaDB) ; (7) CSS Tailwind — `static/tailwind.css` est commité donc Node n'est pas requis pour pytest/mkdocs ; (8) **`forge run` dans le dépôt core** : possible (dogfood via `app.py` + `mvc/` racine), mais positionné comme **outil de validation manuelle** secondaire, pas comme workflow quotidien (pytest/ruff/mkdocs restent le quotidien du contributeur) ; (9) opt-ins (`packages/`) — chaque module a son `pyproject.toml`, modifications éditables sans réinstallation. Liens internes ajoutés vers `contributing.md`, ADR, charte v2, release policy, tests E2E. Card landing core-dev : label « Documentation en cours de consolidation » retiré, CTA accent restauré comme les 4 autres cards. `docs/index.html` resynchronisé via `forge sync:landing`. Tests méta : `tests/meta/test_install_core_dev_docs_001.py` (30 cas — existence, distinction utilisateur/core, étapes canoniques, 5 validations, forge run, opt-ins, Tailwind, liens, roadmap, mkdocs strict). |
| `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` | **livré** | Audit de l'état réel beta 11 après tous les travaux DX, documentation, installation et landing. Reconstruit le tableau ticket/état/commits, mappe chaque fichier WIP au ticket associé, vérifie roadmap et tests. Résultat : 14 tickets confirmés livrés (code + tests + roadmap), 67 fichiers modifiés + 9 nouveaux + 2 supprimés tous attachés à tickets « livré » et restant à découper en commits. Validations : DX ciblés (348 passed), docs/landing/install (287 passed), tests/meta (6 107 passed, 4 skipped), suite complète (15 051 passed, 6 skipped), compileall + ruff + mkdocs --strict + git diff --check + forge sync:landing --check tous OK. Décision : OK pour lancer `BETA11-DX-CLOSING-AUDIT-001`. Rapport : `docs/history/audits/audit-beta11-post-docs-consolidation.md`. |
| `BETA11-DX-CLOSING-AUDIT-001` | **livré** | Clôture officielle de la phase Forge 1.0.0-beta.11. Découpe du WIP en 4 commits cohérents (DX runtime / starter Bonjour Forge / docs DX / landing realign final) + 1 commit audit. Préparation de la section `[1.0.0-beta.11]` dans `CHANGELOG.md` (sans bump version, sans tag — appartient à `RELEASE-BETA11-001`). Working tree propre après commits. Validations finales identiques à l'audit pré-clôture : 15 051 passed, 6 skipped + 5 validations canoniques + forge sync:landing --check OK. Décision : GO pour `RELEASE-BETA11-001`. Rapport : `docs/history/audits/audit-beta11-dx-closing.md`. |
| `STARTER-BONJOUR-FORGE-MINIMAL-001` | **livré** | Ramène le starter `welcome` (Bonjour Forge) à un premier contact strictement minimal : deux routes (`/welcome`, `/welcome/greet`), un contrôleur avec `Response.text(...)` et `request.param(...)`, **zéro vue HTML**, zéro base de données. Suppression des routes `/welcome/inspect`, `/welcome/cycle`, `/welcome/request`, `/welcome/response`, `/welcome/routing`, `/welcome/404-demo` et des 5 vues HTML associées (`cycle.html`, `request_example.html`, `response_example.html`, `routing_example.html`, `not_found_demo.html`). Doc `docs/starters/welcome/index.md` ramenée à ~85 lignes (suppression Tailwind/Mermaid/Symfony/Django/404/Response.debug/render). Doc d'entrée `docs/bonjour-forge.md` réduite aux sections 1–5 (sections request.data / Response.debug / BaseController.render retirées — repoussées à de futurs starters dédiés). `docs/install/windows-wsl.md` aligné (table de vérification des routes : seulement `/welcome` et `/welcome/greet`). Tests : `tests/test_starter_bonjour_forge_001.py` supprimé et remplacé par `tests/test_starter_bonjour_forge_minimal_001.py` ; `tests/meta/test_starter_welcome_001.py` et `tests/meta/test_doc_bonjour_forge.py` réécrits autour du contrat minimal (tests d'absence des méthodes/vues/notions retirées) ; `tests/test_dx_typed_controller_skeletons_001.py` et `tests/meta/test_install_windows_wsl_docs_001.py` ajustés. Aliases historiques (`welcome`, `bienvenue`, `7`) et nouveaux (`bonjour`, `bonjour-forge`) conservés. |
| `GIT-RECOVERY-WORKFLOW-GUARD-001` | **livré** | Verrouille la procédure de contrôle du dépôt de travail avant tout ticket Forge et la procédure officielle de récupération si des commits ont été créés hors du dépôt canonique. Origine : commits faits par erreur dans un projet généré WSL (`~/Projets/forge-test-b11`) après la release `1.0.0-beta.11`, portés ensuite par patchs (`f962d60`, `4d0fe43`, `c79ff4c`). Nouvelle page `docs/contributing/canonical-repo.md` (~160 lignes, 6 sections) couvrant : (1) dépôt canonique attendu (`/home/roger/Projets/Forge`, branche `main`, remote `caucrogeGit/Forge.git`) ; (2) checklist pré-ticket en 5 commandes (`pwd`, `git status --short`, `git branch --show-current`, `git remote -v`, `git log -3 --oneline`) ; (3) signaux d'un mauvais dépôt (branche `master`, commit initial « based on Forge », chemin `forge-test-*`, remote inattendu, `mvc/` isolé sans `core/`/`forge_cli/`/`packages/`) ; (4) procédure 4.1→4.9 (arrêt, `git format-patch`, copie, branche `port/recovery-YYYYMMDD`, `git apply --check`, `git am`, validations canoniques, fast-forward, push) ; (5) interdits explicites (merge direct d'un projet généré, gros diff sans audit, application auto d'un patch WIP, travail depuis `forge-test-*` sur le core) ; (6) liens vers conventions, contributing et release. Navigation MkDocs : nouvelle entrée sous « Pour contribuer ». Lien ajouté dans `docs/contributing.md` (section « Voir aussi »). Garde-fou : `tests/meta/test_git_recovery_workflow_guard_001.py`. Diff CLAUDE.md (mention « étape 0 » du dépôt canonique) préparé et appliqué manuellement par le mainteneur (hook §9 bloque l'écriture agent sur CLAUDE.md). Aucun code runtime modifié, aucun hook touché. |
| `STARTER-ROADMAP-PROGRESSION-001` | **livré** | Formalise la progression pédagogique officielle des starters Forge avant le CRUD. Origine : suite à `STARTER-BONJOUR-FORGE-MINIMAL-001`, le saut direct `welcome` → `01-contact-simple` est trop brutal (Jinja2, routes dynamiques, formulaire POST, validation, SQL/migrations apparaissent en bloc). Nouvelle section « Progression recommandée » dans `docs/starters/index.md` listant les 9 paliers (1. Bonjour Forge → 2. Paramètres d'URL → 3. Première vue HTML → 4. Route dynamique → 5. Inspecter une requête → 6. Premier formulaire POST → 7. Validation serveur → 8. Première base SQL → 9. Premier CRUD) avec admonition `!!! warning` sur le saut welcome → CRUD tant que les paliers 2–8 ne sont pas livrés. `docs/starters/welcome/index.md` : section « Après ce starter » réécrite — ne renvoie plus directement vers `Starter 1 — Contacts` mais vers la progression officielle, et présente Contacts comme « niveau avancé ». `docs/bonjour-forge.md` : ligne « Progression officielle des starters » en tête du tableau « Aller plus loin » + admonition `!!! info "Ne sautez pas directement vers le CRUD Contacts"`. `docs/getting-started.md` : bullet « Progression officielle des starters » ajouté entre Bonjour Forge et Application complète. Tickets futurs inscrits comme trajectoire (`STARTER-QUERY-PARAMS-001`, `STARTER-FIRST-HTML-VIEW-001`, `STARTER-DYNAMIC-ROUTE-001`, `STARTER-REQUEST-DEBUG-001`, `STARTER-FORM-POST-001`, `STARTER-SERVER-VALIDATION-001`, `STARTER-FIRST-SQL-001`, `STARTER-CONTACTS-CRUD-REPOSITION-001`) — non créés dans ce ticket. Garde-fou méta : `tests/meta/test_starter_progression_001.py`. Aucun starter modifié, aucun moteur de routing / Request / Response / BaseController touché, CLAUDE.md inchangé, release beta.11 intacte. |
| `STARTER-QUERY-PARAMS-001` | **livré** | Premier starter de la progression pédagogique officielle (palier 2, après Bonjour Forge). Crée `forge_cli/starters/data/query-params/` : `starter.json` (id `query-params`, number 8, aliases `query_params`/`params`/`8`, `requires_db: false`, `kind: skeleton`), `routes.py.snippet` (deux routes `/query-params` et `/query-params/hello` avec marqueurs `# forge-starter:query-params:start|end`), `files/mvc/controllers/query_params_controller.py` (deux méthodes typées `request: Request -> Response`, `index` retourne `Response.text(...)` avec message d'aide, `hello` lit `request.param("name", default="Forge")` et retourne `Bonjour {name}`). Aucune vue HTML, aucune base de données, aucun template. Documentation : `docs/starters/query-params/index.md` (~100 lignes) couvrant objectif, routes, contrôleur, exemples navigateur, à retenir, palier suivant. Mises à jour : tableau de synthèse + section « Génération automatique » de `docs/starters/index.md`, navigation MkDocs sous « Modules et starters » (entre Bienvenue et Contacts), progression officielle palier 2 marqué livré. Tests : `tests/test_starter_query_params_001.py` (contrôleur, snippet, métadonnées, dry-run, absence SQL/views) et `tests/meta/test_starter_query_params_docs_001.py` (doc + nav). Test progression `tests/meta/test_starter_progression_001.py` mis à jour pour refléter palier 2 livré (retiré `STARTER-QUERY-PARAMS-001` de la liste des futurs, retiré `query-params` de la liste des starters non créés). Hors périmètre respecté : `Request.param(...)` inchangé, routeur inchangé, hooks intacts, CLAUDE.md inchangé, release beta.11 intacte. |
| `AGENTS-NO-BACKGROUND-VALIDATION-001` | **livré** | Verrouille dans `CLAUDE.md` (section 12, nouvelle sous-section « Validations : pas d'attente passive ») l'interdiction pour les agents Claude/Codex de lancer les validations Forge (`pytest`, `mkdocs`, `ruff`, `compileall`) en arrière-plan ou de masquer une preuve finale avec `tail`/`head`. Origine : sur le ticket `STARTER-QUERY-PARAMS-001`, le bg `pytest tests/meta -q` avait laissé l'agent en attente passive avec un fichier de sortie à 0 octet, sans exit code ni résumé exploitable. Interdits explicites listés (bg, « j'attends la fin », sortie tronquée, validation sans exit code). Attendus listés (foreground, sortie utile complète, exit code, erreur complète en échec, fallback « demander à l'utilisateur de coller le résultat » si trop long). Note attenante : les futurs tickets Forge ne doivent plus écrire `pytest tests/meta -q` sans préciser que la commande tourne en foreground et sans masquer la sortie. Bloc inséré manuellement par le mainteneur (hook §9 bloque l'écriture agent sur `CLAUDE.md`). Aucun code runtime modifié, aucun hook touché, aucun test ajouté dans ce ticket (un éventuel garde-fou méta « la section "Validations : pas d'attente passive" est présente » serait pris dans un `AGENTS-NO-BACKGROUND-VALIDATION-TEST-001` séparé). |
| `AGENTS-NO-BACKGROUND-VALIDATION-TEST-001` | **livré** | Garde-fou méta de la règle livrée par `AGENTS-NO-BACKGROUND-VALIDATION-001`. Ajoute la classe `TestNoBackgroundValidationRule` dans `tests/meta/test_claude_md_001.py` avec un helper `_validation_rule_block()` qui extrait le bloc de règle entre le header `### Validations : pas d'attente passive` (smart apostrophe U+2019) et la prochaine section `##`, puis 14 assertions : header présent, bloc non vide, 10 marqueurs paramétrés présents DANS le bloc (`arrière-plan`, `foreground`, `exit code`, `pytest`, `mkdocs`, `ruff`, `compileall`, `tail`, `head`, `"j'attends la fin"`), listes `Interdit :` et `Attendu :` présentes, position du bloc à l'intérieur de la section 12 (hook PreToolUse). Stratégie d'extraction nécessaire car `pytest`/`mkdocs`/`ruff`/`compileall` apparaissent ailleurs dans CLAUDE.md (sections 6, 11), donc une recherche globale serait trompeuse. CLAUDE.md inchangé, aucun hook touché, aucun starter touché, roadmap inchangée hors cette entrée. Validations foreground : pytest -v (52 passed, exit 0), ruff check tests/meta (OK), git diff --check (OK). |
| `STARTER-FIRST-HTML-VIEW-001` | **livré** | Deuxième starter pédagogique de la progression officielle (palier 3, après Paramètres d'URL). Crée `forge_cli/starters/data/first-html-view/` : `starter.json` (id `first-html-view`, number 9, aliases `first_html_view`/`html-view`/`9`, `requires_db: false`, `kind: skeleton`), `routes.py.snippet` (une route `/first-html-view`, marqueurs `# forge-starter:first-html-view:start|end`), `files/mvc/controllers/first_html_view_controller.py` (méthode `index` typée `request: Request -> Response` qui appelle `BaseController.render("first_html_view/index.html", request=request)`), `files/mvc/views/first_html_view/index.html` (vue HTML minimale — un H1, un paragraphe, pas de Tailwind, pas de layout, pas d'include). Aucune base de données, aucun formulaire, aucune route dynamique. Documentation : `docs/starters/first-html-view/index.md` (~75 lignes) — assume l'utilisateur déjà dans un projet créé avec ce starter, seul `forge run` mentionné pour lancer le serveur (interdits stricts : `Starter 9`, `starter:build 9`, `starter:build first-html-view`, `forge new mon-projet …`, `cd mon-projet`, `source .venv/bin/activate`). Mises à jour : tableau de synthèse de `docs/starters/index.md` (ligne palier 3), progression palier 3 marqué livré, navigation MkDocs sous « Modules et starters » (entre Paramètres d'URL et Contacts). Tests proportionnés : `tests/test_starter_first_html_view_001.py` (~12 cas — contrat starter.json, snippet, contrôleur, vue, absence SQL/migration, doc + anti-régression sur les patterns interdits, palier 3 livré dans la progression). Test progression `tests/meta/test_starter_progression_001.py` mis à jour (palier 3 livré ; `STARTER-FIRST-HTML-VIEW-001` retiré de la liste des codes futurs ; `first-html-view` retiré de la liste des starters non créés). Hors périmètre respecté : `BaseController.render(...)` inchangé, routeur inchangé, hooks intacts, CLAUDE.md inchangé, release beta.11 intacte. Validations proportionnées (foreground, sortie utile, exit codes) : `pytest tests/test_starter_first_html_view_001.py` + voisins, `mkdocs --strict`, `ruff`, `compileall` ciblés. |
| `STARTER-DYNAMIC-ROUTE-001` | **livré** | Troisième starter pédagogique de la progression officielle (palier 4, après Première vue HTML). Crée `forge_cli/starters/data/dynamic-route/` : `starter.json` (id `dynamic-route`, number 10, aliases `dynamic_route`/`route-param`/`10`, `requires_db: false`, `kind: skeleton`), `routes.py.snippet` (une route `GET /dynamic-route/articles/{id}` single-line — le parser `routes_from_snippet` ne gère que single-line, marqueurs `# forge-starter:dynamic-route:start|end`), `files/mvc/controllers/dynamic_route_controller.py` (méthode `show` typée `request: Request -> Response` qui appelle `request.route_param("id", default="inconnu")` puis `Response.text(f"Article {article_id}")`). Aucune vue HTML, aucune base de données, aucun formulaire. Documentation : `docs/starters/dynamic-route/index.md` (~75 lignes) — assume l'utilisateur déjà dans un projet créé avec ce starter, seul `forge run` mentionné. Interdits stricts : `Starter 10`, `starter:build 10`, `starter:build dynamic-route`, `forge new mon-projet …`, `cd mon-projet`, `source .venv/bin/activate`. La doc distingue explicitement `request.param(...)` (query string `?id=42`) de `request.route_param(...)` (segment dynamique `/articles/42`). Mises à jour : tableau de synthèse de `docs/starters/index.md` (palier 4), progression palier 4 marqué livré, navigation MkDocs (entre Première vue HTML et Contacts). Tests proportionnés : `tests/test_starter_dynamic_route_001.py` (~12 cas — contrat starter.json + route exacte avec `{id}` + contrôleur + absence SQL/migration/vue + doc + 6 patterns interdits + palier 4 livré). Test progression `tests/meta/test_starter_progression_001.py` mis à jour (palier 4 livré ; `STARTER-DYNAMIC-ROUTE-001` retiré des codes futurs ; `dynamic-route` retiré des starters non créés ; ajout `test_palier_4_dynamic_route_marque_livre`). Hors périmètre respecté : `Request.route_param(...)` inchangé (API existante `route_param(key, default=None)`), routeur inchangé, hooks intacts, CLAUDE.md inchangé, release beta.11 intacte. Validations proportionnées (foreground, sortie utile, exit codes) : `pytest tests/test_starter_dynamic_route_001.py + voisins`, `mkdocs --strict`, `ruff`, `compileall` ciblés. |
| `STARTER-REQUEST-DEBUG-001` | **livré** | Quatrième starter pédagogique de la progression officielle (palier 5, après Route dynamique). Crée `forge_cli/starters/data/request-debug/` : `starter.json` (id `request-debug`, number 11, aliases `request_debug`/`debug`/`11`, `requires_db: false`, `kind: skeleton`), `routes.py.snippet` (une route `GET /request-debug`, marqueurs `# forge-starter:request-debug:start|end`), `files/mvc/controllers/request_debug_controller.py` (méthode `index` typée `request: Request -> Response` qui retourne exactement `Response.debug(request.data)`). Aucune vue HTML, aucune base de données, aucun formulaire. Documentation : `docs/starters/request-debug/index.md` (~70 lignes) — assume l'utilisateur déjà dans un projet créé avec ce starter, seul `forge run` mentionné. Interdits stricts : `Starter 11`, `starter:build 11`, `starter:build request-debug`, `forge new mon-projet …`, `cd mon-projet`, `source .venv/bin/activate`. Note pédagogique brève sur la contrainte `APP_ENV` : `Response.debug(...)` HTML pédagogique en dev, refuse en prod (404) — pas un cours sécurité complet. Mises à jour : tableau de synthèse de `docs/starters/index.md` (palier 5), progression palier 5 marqué livré, navigation MkDocs (entre Route dynamique et Contacts). Tests proportionnés : `tests/test_starter_request_debug_001.py` (~12 cas — contrat starter.json + route /request-debug + contrôleur appelle `Response.debug(request.data)` + absence SQL/migration/vue/HTML + doc + 6 patterns interdits + palier 5 livré). Test progression `tests/meta/test_starter_progression_001.py` mis à jour (palier 5 livré ; `STARTER-REQUEST-DEBUG-001` retiré des codes futurs ; `request-debug` retiré des starters non créés ; ajout `test_palier_5_request_debug_marque_livre`). Hors périmètre respecté : `Response.debug(...)`, `request.data`, `Request`, routeur inchangés, hooks intacts, CLAUDE.md inchangé, release beta.11 intacte. Validations proportionnées (foreground, sortie utile, exit codes) : `pytest tests/test_starter_request_debug_001.py + voisins`, `mkdocs --strict`, `ruff`, `compileall` ciblés. |
| `STARTER-FORM-POST-001` | **livré** | Cinquième starter pédagogique de la progression officielle (palier 6, après Inspecter une requête). Crée `forge_cli/starters/data/form-post/` : `starter.json` (id `form-post`, number 12, aliases `form_post`/`post-form`/`12`, `requires_db: false`, `kind: skeleton`), `routes.py.snippet` (deux routes `GET /form-post` et `POST /form-post` single-line, marqueurs `# forge-starter:form-post:start|end`), `files/mvc/controllers/form_post_controller.py` (méthode `index` qui appelle `BaseController.render("form_post/index.html", request=request, context={"csrf_token": BaseController.csrf_token(request)})` ; méthode `submit` qui appelle `request.form("name", default="Forge")` puis retourne `Response.text(f"Bonjour {name}")`), `files/mvc/views/form_post/index.html` (formulaire HTML minimal — un H1, un `<form method="post" action="/form-post">` avec `<input type="hidden" name="csrf_token" value="{{ csrf_token }}">`, un label/input pour `name`, un bouton submit ; aucun Tailwind, aucun layout, aucun include, aucun JS). Aucune base de données, aucune validation serveur avancée. Audit CSRF avant écriture : le routeur Forge a `csrf=True` par défaut sur `router.group` (`core/http/router.py:136`), le pattern existant utilise `BaseController.csrf_token(request)` dans le contrôleur + `<input type="hidden" name="csrf_token">` dans la vue (cf. `carnet-contacts`). Le starter respecte ce pattern et laisse le middleware Forge vérifier le token automatiquement — aucune modification du moteur CSRF. API utilisée telle quelle : `Request.form(key, default=None)` à `core/http/request.py:245`, `BaseController.csrf_token(request)` à `core/mvc/controller/base_controller.py:89`. Documentation : `docs/starters/form-post/index.md` (~85 lignes) — assume l'utilisateur déjà dans un projet créé avec ce starter, seul `forge run` mentionné. Interdits stricts : `Starter 12`, `starter:build 12`, `starter:build form-post`, `forge new mon-projet …`, `cd mon-projet`, `source .venv/bin/activate`. Mises à jour : tableau de synthèse de `docs/starters/index.md` (palier 6), progression palier 6 marqué livré, navigation MkDocs (entre Inspecter une requête et Contacts). Tests proportionnés : `tests/test_starter_form_post_001.py` (~15 cas — contrat starter.json + deux routes GET/POST + contrôleur (imports, render index, request.form + Response.text submit, csrf_token passé au template) + vue (form method post action /form-post, input name="name", champ csrf_token) + absence SQL/migration/entity + doc + 6 patterns interdits + palier 6 livré). Test progression `tests/meta/test_starter_progression_001.py` mis à jour (palier 6 livré ; `STARTER-FORM-POST-001` retiré des codes futurs ; `form-post` retiré des starters non créés ; ajout `test_palier_6_form_post_marque_livre`). Hors périmètre respecté : moteur CSRF inchangé, moteur de templates inchangé, `Request`, `Response`, `BaseController`, routeur, hooks intacts, CLAUDE.md inchangé, release beta.11 intacte. Validations proportionnées (foreground, sortie complète, exit codes) : `pytest tests/test_starter_form_post_001.py + voisins`, `mkdocs --strict`, `ruff`, `compileall` ciblés. |
| `STARTER-SERVER-VALIDATION-001` | **livré** | Sixième starter pédagogique de la progression officielle (palier 7, après Premier formulaire POST). Crée `forge_cli/starters/data/server-validation/` : `starter.json` (id `server-validation`, number 13, aliases `server_validation`/`validation`/`13`, `requires_db: false`, `kind: skeleton`), `routes.py.snippet` (deux routes `GET /server-validation` et `POST /server-validation` single-line, marqueurs `# forge-starter:server-validation:start|end`), `files/mvc/controllers/server_validation_controller.py` (`index` rend le template avec `csrf_token` ; `submit` lit `request.form("name", default="").strip()`, retourne `Response.text("Le prénom est obligatoire", status=422)` si vide, sinon `Response.text(f"Bonjour {name}")`), `files/mvc/views/server_validation/index.html` (formulaire minimal sans Tailwind, sans JS, sans message HTML dynamique, avec champ caché `csrf_token`). Aucune base de données, aucun framework de validation, aucune classe `Validator`, aucun réaffichage avec messages dynamiques — uniquement le contrôle minimum côté serveur. API utilisée telle quelle : `Response.text(body, status=200, headers=None)` à `core/http/response.py:67` (le paramètre `status` accepte 422 directement), `Request.form(...)`, `BaseController.csrf_token(...)`. Documentation : `docs/starters/server-validation/index.md` (~80 lignes) — assume l'utilisateur déjà dans un projet créé avec ce starter, seul `forge run` mentionné. Interdits stricts : `Starter 13`, `starter:build 13`, `starter:build server-validation`, `forge new mon-projet …`, `cd mon-projet`, `source .venv/bin/activate`. La doc explique brièvement le statut HTTP 422 et pose le principe « le serveur doit toujours vérifier ce qu'il reçoit ». Mises à jour : tableau de synthèse de `docs/starters/index.md` (palier 7), progression palier 7 marqué livré, navigation MkDocs (entre Premier formulaire POST et Contacts). Tests proportionnés : `tests/test_starter_server_validation_001.py` (~16 cas — contrat starter.json + deux routes GET/POST + contrôleur (imports, render index, csrf_token, request.form, branche vide retourne status 422, branche valide retourne `Bonjour {name}`) + vue (form method post action /server-validation, input name="name", champ csrf_token, pas de Tailwind/JS) + absence SQL/migration/entity + doc + 6 patterns interdits + palier 7 livré). Test progression `tests/meta/test_starter_progression_001.py` mis à jour (palier 7 livré ; `STARTER-SERVER-VALIDATION-001` retiré des codes futurs ; `server-validation` retiré des starters non créés ; ajout `test_palier_7_server_validation_marque_livre`). Hors périmètre respecté : `Response`, `Request`, `BaseController`, moteur CSRF, routeur, middleware inchangés ; aucune classe `Validator`, aucun système complet de validation ; hooks intacts, CLAUDE.md inchangé, release beta.11 intacte. Validations proportionnées (foreground, sortie complète, exit codes) : `pytest tests/test_starter_server_validation_001.py + voisins`, `mkdocs --strict`, `ruff`, `compileall` ciblés. |
| `STARTER-FIRST-SQL-001` | **livré** | Septième starter pédagogique de la progression officielle (palier 8, dernier palier avant le CRUD Contacts). Audit DB préalable : API officielle `core.database.db.{fetch_one, fetch_all, execute, insert}` confirmée, pattern existant des models de starters CRUD (raw SQL en chaîne Python lisible, ex. `carnet-contacts/contact_model.py`) ; mécanisme migration `forge migration:apply` confirmé avec `MIGRATIONS_DIR = mvc/migrations` (`forge_cli/entities/migrations.py:19`) et format de fichier `YYYYMMDDHHMMSS_nom.sql`. Crée `forge_cli/starters/data/first-sql/` : `starter.json` (id `first-sql`, number 14, aliases `first_sql`/`sql`/`14`, **`requires_db: true`**, `kind: skeleton`), `routes.py.snippet` (une route `GET /first-sql`, marqueurs `# forge-starter:first-sql:start|end`), `files/mvc/controllers/first_sql_controller.py` (constante `SELECT_FIRST_MESSAGE = "SELECT content FROM first_sql_messages ORDER BY id LIMIT 1"` au niveau module pour garder le SQL lisible ; `index` appelle `fetch_one(...)` puis retourne `Response.text(f"Message depuis la base : {message}")` avec fallback `(aucun message)` si table vide), `files/mvc/migrations/20260527120000_create_first_sql_messages.sql` (format timestamp YYYYMMDDHHMMSS requis par le collecteur ; `CREATE TABLE IF NOT EXISTS first_sql_messages` + `INSERT … WHERE NOT EXISTS` idempotent). Aucun CRUD, aucune entité JSON, aucun model, aucun formulaire, aucune relation. Documentation : `docs/starters/first-sql/index.md` (~90 lignes) — assume l'utilisateur déjà dans un projet créé avec ce starter, instructions `forge migration:apply` puis `forge run` (autorisées car réellement nécessaires pour activer la table). Interdits stricts : `Starter 14`, `forge starter:build 14`, `forge starter:build first-sql`, `forge new mon-projet …`, `cd mon-projet`, `source .venv/bin/activate`. La doc présente Contacts comme palier suivant niveau avancé (futur ticket `STARTER-CONTACTS-CRUD-REPOSITION-001`). Mises à jour : tableau de synthèse de `docs/starters/index.md` (palier 8, profil `minimal`/`standard` requis pour db:init), progression palier 8 marqué livré, navigation MkDocs (entre Validation serveur et Contacts). Tests proportionnés : `tests/test_starter_first_sql_001.py` (~16 cas — contrat starter.json + `requires_db: true` explicite + route /first-sql + contrôleur (imports incluant `core.database.db.fetch_one`, SELECT visible, Response.text avec format `f"Message depuis la base : {message}"`) + migration timestamp YYYYMMDDHHMMSS + CREATE TABLE first_sql_messages + INSERT 'Bonjour SQL' + absence entity.json/CRUD/forms + doc + 6 patterns interdits + palier 8 livré). Test progression `tests/meta/test_starter_progression_001.py` mis à jour (palier 8 livré ; `STARTER-FIRST-SQL-001` retiré des codes futurs ; `first-sql` retiré des starters non créés ; `TestFutureStartersNotYetCreated` n'a plus que `CONTACTS-CRUD-REPOSITION-001` à attendre ; ajout `test_palier_8_first_sql_marque_livre`). Hors périmètre respecté : `core.database.db` inchangé (utilisé tel quel), moteur migration inchangé, `Request`/`Response`/`BaseController` inchangés, aucun CRUD/entité/model/relation/pagination, hooks intacts, CLAUDE.md inchangé, release beta.11 intacte. Validations proportionnées (foreground, sortie complète, exit codes) : `pytest tests/test_starter_first_sql_001.py + voisins`, `mkdocs --strict`, `ruff`, `compileall` ciblés. |
| `STARTER-CONTACTS-CRUD-REPOSITION-001` | **livré** | Repositionnement pédagogique du starter `01-contact-simple` (Contacts CRUD) comme palier 9 — synthèse avancée — de la progression officielle des starters. Aucun code runtime modifié, aucune migration, aucune entité, aucun contrôleur touché ; uniquement la présentation documentaire. `docs/starters/01-contact-simple/index.md` : badge en-tête « Starter Forge · Niveau 1 » → « Starter Forge · Palier 9 (avancé) » ; sous-titre « Premier parcours Forge » → « Synthèse avancée et point d'arrivée de la progression officielle des starters » avec lien vers `#progression-recommandee` ; admonition `!!! warning "Palier 9 — synthèse avancée"` qui liste explicitement les 9 prérequis pédagogiques (routes, contrôleurs, `Response.text`, paramètres d'URL `request.param`, rendu HTML `BaseController.render`, routes dynamiques `request.route_param`, inspection requête, formulaires POST avec CSRF, validation serveur, migrations SQL `fetch_one`) ; carte « Niveau : Débutant Forge » → « Niveau : Avancé » avec mention des paliers ; admonition « Profil recommandé » reformulée pour rediriger vers `Bonjour Forge` pour le premier contact. `docs/starters/index.md` : ligne du tableau de synthèse pour Contacts CRUD réécrite (« Découvrir Forge avec un exemple CRUD simple » → « **Palier 9** de la progression — synthèse avancée du CRUD officiel ; suppose les 8 paliers précédents acquis ») ; section « Starter 1 — Contacts » réécrite (« idéal pour découvrir Forge », « premier parcours Forge » retirés ; remplacés par « palier 9 », « synthèse avancée », liste des prérequis, redirection vers Bonjour Forge pour le premier contact) ; progression palier 9 reformulé (`livré ; synthèse avancée, repositionnement pédagogique formalisé par STARTER-CONTACTS-CRUD-REPOSITION-001`). Test méta dédié `tests/meta/test_contacts_crud_reposition_001.py` (8 cas — palier 9 dans la progression, mention « synthèse avancée » dans la page Contacts, prérequis pédagogiques présents, badge en-tête repositionné, absences `Niveau 1` / `Premier parcours Forge` / `Débutant Forge` / `idéal pour découvrir Forge` comme étiquettes Contacts, redirection Bonjour Forge présente). Hors périmètre respecté : code starter Contacts, migrations, entités JSON, contrôleurs générés, `Request`/`Response`/`BaseController`, hooks, CLAUDE.md, release beta.11 tous intacts. La progression pédagogique officielle des starters est désormais complète (paliers 1 → 9 livrés et clairement positionnés). |
| `FORGE-UPDATE-COMMAND-001` | **livré** | Nouvelle commande `forge update` pour mettre à jour le package `forge-mvc` dans l'environnement Python courant. Cible précise : un utilisateur qui a créé son projet avec une ancienne beta et veut s'aligner sur la dernière version. Audit préalable : dispatcher forge.py (pattern `if command == "…": _main(args[1:]); return`), `forge_cli/help.py` (texte court CLI), `forge_cli/help_dispatch.py` (`HELP_TEXTS` court + `HELP_TEXTS_RICH` détaillé par commande). Crée `forge_cli/update.py` (`main(args) -> int`) avec 4 modes : défaut `pip install --upgrade forge-mvc` via `sys.executable` (reste dans le venv courant) ; `--pre` ajoute `--pre` (recommandé tant que Forge est en beta) ; `--check` lecture seule, affiche version installée + commande qui serait lancée ; `--dry-run` affiche la commande pip sans l'exécuter. Détection pipx : si `sys.executable` pointe sous `pipx/venvs/`, n'exécute PAS pip (qui ne mettrait pas à jour l'install pipx globale) et affiche le bon `pipx upgrade forge-mvc` à lancer. Branchement : import + dispatcher dans `forge.py`, ligne courte dans `forge_cli/help.py` (« forge update — Met à jour Forge dans l'environnement courant »), entrée `HELP_TEXTS` + bloc `HELP_TEXTS_RICH` détaillé dans `forge_cli/help_dispatch.py` (Usage, Description, Modes, Options, Cas pipx, Hors périmètre, Après mise à jour). Documentation : `docs/reference/cli-commands.md` (entrée `forge-update` complète avec cas pipx + ligne ajoutée dans le tableau « Commandes essentielles »), `docs/install/windows-wsl.md` (admonition `!!! tip "Mettre à jour Forge plus tard"` après l'étape pipx). Tests ciblés : `tests/test_forge_update_command_001.py` (~14 cas — dispatcher reconnaît `update`, --help via format_command_help, --dry-run n'appelle pas subprocess.run, --pre ajoute `--pre`, `sys.executable` utilisé, détection pipx via mock de `sys.executable`, branche pipx affiche `pipx upgrade` sans pip, branche venv lance subprocess.run, échec pip → exit code non-nul, --check lecture seule, ligne dans help.py, format_command_help renvoie texte enrichi). Hors périmètre respecté : aucune migration projet, aucun fichier `env/*` touché, aucun fichier généré sous `mvc/` modifié, aucune mise à jour du `pyproject.toml` du projet, aucune intégration IoT, aucune release, aucun tag, aucune publication PyPI. Validations proportionnées (foreground, sortie complète, exit codes) : `pytest tests/test_forge_update_command_001.py + tests/meta/test_cli_help*`, `ruff check forge_cli/update.py tests/test_forge_update_command_001.py`, `compileall -q forge_cli/update.py …`, `mkdocs --strict`, `git diff --check`. |

| `IOT-SUBSCRIBER-CLI-001` | **livré** | Commande `forge iot:listen` — écoute le broker MQTT configuré et **insère** chaque mesure reçue dans `iot_events`. Transforme les briques existantes en flux local réellement utilisable : `Mosquitto → forge iot:listen → MqttSubscriber → IotEventRepository.insert() → iot_events`. Commande de **développement / pédagogie**, **pas** un service de production. Module `packages/forge-mvc-iot/forge_mvc_iot/cli/listen.py` qui expose `run_listener(*, config, repository, subscriber_factory=None) -> int` (testable, toutes dépendances injectables) et `main(argv=None) -> int`. `main` charge `load_iot_config()` (exit 1 + `[ERREUR] Configuration IoT invalide : …` si `ValueError`), instancie `IotEventRepository()` puis délègue à `run_listener`. `run_listener` construit le `MqttSubscriber` via `subscriber_factory(config=…, on_measurement=…)` (défaut `_default_subscriber_factory` qui importe `MqttSubscriber` **paresseusement** → `paho` jamais importé tant que la commande n'est pas lancée), branche `on_measurement` sur une classe interne `_StorageListener` : chaque mesure valide → `repository.insert(measurement)` + ligne `[OK] {site}/{device_id} {kind}={value} {unit}`. Bannière `[INFO]` (broker host:port, topic, stockage, « Ctrl+C pour arrêter »). `subscriber.connect()` en `try` → `[ERREUR] Connexion MQTT impossible : …` + exit 1 si le broker est injoignable (les erreurs MQTT ne portent pas le mot de passe). `loop_forever()` jusqu'à `KeyboardInterrupt` (capté → `[INFO] Arrêt demandé (Ctrl+C).`, exit 0), `disconnect()` dans un `finally`. **Arrêt au premier échec base** (plus simple/pédagogique) : si `repository.insert` lève, `_StorageListener` distingue table absente (`errno == 1146` ou `"doesn't exist"`) → message `[ERREUR] Stockage IoT indisponible.` + `Conseil : lance forge iot:init puis forge migration:apply`, sinon `[ERREUR] Insertion en base impossible — <Type>` (sobre, sans stacktrace) ; dans les deux cas mémorise l'erreur, appelle `subscriber.disconnect()` pour sortir de la boucle, et `run_listener` retourne 1. Branchement `forge.py` : `command == "iot:listen"` → `forge_mvc_iot.cli.listen.main`, import paresseux + `cli_fail` propre si le module opt-in est absent. Help text : `forge_cli/help.py` (section IoT) + `forge_cli/help_dispatch.py` (`HELP_DESCRIPTIONS` + bloc `HELP_TEXTS_RICH` : usage, comportement, prérequis `doctor --mqtt`/`doctor --db`, limites, codes de sortie) — `forge iot:listen --help` rendu par le dispatcher central. Garde-fou `tests/meta/test_cli_help_flags_closing_audit_001.py` : `iot:listen` ajouté à `ALL_DISPATCHED_COMMANDS`. Page [`docs/iot/listen-command.md`](../iot/listen-command.md) (objectif/flux, usage, sortie exemple, **parcours complet** doctor → init → apply → doctor --db → doctor --mqtt → listen → simulate → curl, gestion d'erreurs config/broker/table, limites dev vs prod) ; nav MkDocs étendue ; [`docs/iot/simulator.md`](../iot/simulator.md) « Parcours recommandé » pointe `forge iot:listen` côté consommation ; [`docs/starters/welcome-iot/index.md`](../starters/welcome-iot/index.md) « Après ce starter » montre le parcours complet `listen` + `simulate` + `curl`. Tests `tests/test_iot_listen_command_001.py` (≈20 cas — `run_listener` avec faux subscriber : `connect` appelé, `on_measurement` branché et callable, une mesure reçue → `repository.insert` appelé + ligne `[OK]`, `KeyboardInterrupt` → exit 0 + `disconnect` appelé + message d'arrêt, échec connexion → exit 1 + `[ERREUR] Connexion MQTT impossible`, erreur DB table absente → exit 1 + conseil `forge iot:init` & `forge migration:apply` + `disconnect` demandé, erreur DB générique → exit 1 message sobre sans `Traceback` ; `main` : config invalide → exit 1, succès via monkeypatch `load_iot_config`/`IotEventRepository`/`_default_subscriber_factory` → exit 0 + insert appelé ; `forge iot:listen --help` rendu (subprocess) et `forge help` liste `iot:listen` ; garde-fous : pas de lancement du simulateur, pas de route HTTP, `paho` jamais importé sans lancer la commande, `core/` n'importe pas `forge_mvc_iot`). Hors périmètre respecté : pas de daemon systemd, pas de mode service, pas de queue, pas de retry/backoff, pas de batch insert, pas de stockage multi-thread, pas de dashboard, pas de Forge Design, pas de TLS/auth avancé, pas de modification du contrat MQTT ni de l'API HTTP, ne lance pas le simulateur. Avec ce ticket, le flux IoT local est complet : `forge iot:listen` (terminal 1) + `forge iot:simulate --count 3 --interval 1` (terminal 2) + `curl /api/iot/events`. Prochain ticket : `IOT-MOSQUITTO-LOCAL-DOCS-001` (doc Mosquitto local montrant le flux complet `doctor --mqtt → listen → simulate → API HTTP`). |
| `IOT-SIMULATOR-001` | **livré** | Simulateur MQTT `forge iot:simulate` — publie des mesures **factices** mais **conformes au contrat** `forge/{site}/{device_id}/telemetry` vers le broker configuré, sans capteur physique. Ferme le flux pédagogique de bout en bout : `forge iot:doctor --mqtt` → `forge iot:simulate` → subscriber MQTT → `iot_events` → `/api/iot/events`. Responsabilité unique : **publier**. Ne lance pas le subscriber, n'écrit pas en base, n'appelle pas l'API HTTP. Module `packages/forge-mvc-iot/forge_mvc_iot/cli/simulate.py` qui expose : `SimulateOptions` (dataclass site/device/kind/value/unit/count/interval), `build_topic(site, device_id)`, `build_payload(*, kind, value, unit, timestamp, source="forge-iot-simulator")` (payload JSON contractuel avec `metadata.source`), `utc_timestamp(now=None)` (ISO 8601 UTC suffixe `Z`, précision seconde, `now` injectable + conversion fuseau→UTC), `parse_args(args) -> SimulateOptions` (parser manuel, `ArgumentError` à message clair), `publish_measurements(config, options, *, client_factory=None, now=None, sleep=None)` et `main(args)`. Defaults : site `atelier`, device `esp32-001`, kind `temperature`, value `22.4`, unit `°C`, count `1`, interval `1`. Options `--site/--device/--kind/--value/--unit/--count/--interval`. **Bornes** : `--count` 1..1000, `--interval` 0..60 s (dépassement → `ArgumentError`, exit 2). Utilise `load_iot_config()` (import paresseux dans `main`). `paho-mqtt` importé **paresseusement** via `_default_client_factory(config)` (`CallbackAPIVersion.VERSION2`, aligné sur `mqtt/subscriber.py` et le doctor). Connexion brève : `connect` → `loop_start` → `publish` (QoS 0, ×count, espacés de `interval`, `wait_for_publish` best-effort via `getattr` pour rester compatible mock) → `loop_stop` → `disconnect` dans un `finally`. **Pas** de `loop_forever`, pas de retain, pas de QoS avancé, pas de downlink. `client_factory`/`now`/`sleep` injectables pour tester sans broker ni délai réel. **Conformité contractuelle vérifiée AVANT toute connexion** : `main` construit un message témoin et le passe à `parse_message` (réutilise `forge_mvc_iot.mqtt.contract`) — un `--site Atelier` (majuscule, hors slug) est rejeté proprement (`[ERREUR] message non conforme au contrat MQTT`, exit 2) sans ouvrir de socket. Mot de passe **jamais** affiché (transmis à paho via `username_pw_set`, absent de toute sortie ; erreurs sobres sans stacktrace). Codes de sortie : `0` publication OK, `2` option/contrat invalide, `1` config invalide ou échec connexion/publication. Branchement `forge.py` : `command == "iot:simulate"` → `forge_mvc_iot.cli.simulate.main`, import paresseux avec `cli_fail` propre si le module opt-in est absent. Help text : `forge_cli/help.py` (section IoT) + `forge_cli/help_dispatch.py` (`HELP_DESCRIPTIONS` + bloc `HELP_TEXTS_RICH` : usage, défauts, options bornées, effets, limites, codes de sortie) — `forge iot:simulate --help` rendu par le dispatcher central. Garde-fou `tests/meta/test_cli_help_flags_closing_audit_001.py` : `iot:simulate` ajouté à `ALL_DISPATCHED_COMMANDS`. Page [`docs/iot/simulator.md`](../iot/simulator.md) (objectif/flux, usage, payload par défaut, tableau d'options, conformité contrat, sortie exemple, codes de sortie, parcours recommandé, limites) ; nav MkDocs étendue ; [`docs/starters/welcome-iot/index.md`](../starters/welcome-iot/index.md) « Après ce starter » pointe le simulateur + flux de test rapide. Tests `tests/test_iot_simulator_001.py` (≈30 cas — `build_topic`/`build_payload` (forme contractuelle, `metadata.source`), `utc_timestamp` (suffixe `Z`, conversion fuseau, `now` injectable), payload généré validé par `parse_message` (défauts + custom kind/value/unit), `parse_args` (défauts, chaque option, `--value` float, options inconnues / valeurs manquantes → `ArgumentError`), bornes `--count`/`--interval` (0, 1001, 61, négatif rejetés ; 1, 1000, 0, 60 acceptés), `publish_measurements` avec faux client (connect+publish+disconnect reçus, topic conforme, count messages, `interval`>0 → `sleep` appelé count-1 fois, `username_pw_set` si username), mot de passe sentinel absent de la sortie, `main` (succès exit 0 avec client mocké via monkeypatch du factory, `--count 0` exit 2, `--site Atelier` non conforme exit 2 sans connexion, config invalide exit 1, échec connexion exit 1 message sobre), `forge iot:simulate --help` rendu (subprocess) et `forge help` liste `iot:simulate`, garde-fous : `paho` jamais importé sans lancer la commande, `core/` n'importe pas `forge_mvc_iot`). Hors périmètre respecté : pas de subscriber lancé, pas d'écriture DB, pas de lecture API HTTP, pas de dashboard, pas de Forge Design, pas de code Arduino, pas de downlink, pas de retain par défaut, pas de QoS avancé. Avec ce ticket, un atelier peut faire `forge iot:doctor --mqtt && forge iot:simulate --count 3 --interval 1` et alimenter un broker local sans matériel. Prochain ticket : `IOT-MOSQUITTO-LOCAL-DOCS-001` (documenter un Mosquitto local pour exécuter le flux complet). |
| `IOT-DOCTOR-MQTT-001` | **livré** | Option `--mqtt` pour `forge iot:doctor` — connexion brève au broker MQTT configuré, **avant** de lancer un subscriber ou un simulateur. Complète la trilogie `doctor` : `forge iot:doctor` (statique) → `--db` (table `iot_events`) → `--mqtt` (broker MQTT). Symétrique à `--db` : option explicite, import paresseux, sans effet de bord. Nouvelle fonction `check_mqtt_broker(config, *, client_factory=None, connect_timeout=3.0)` dans `packages/forge-mvc-iot/forge_mvc_iot/cli/doctor.py`. Utilise **`paho-mqtt`** (pas un simple socket TCP) : un socket dirait seulement « un port répond », pas « un broker MQTT accepte la connexion » — il faut un vrai `connect()` MQTT + CONNACK. Connexion **brève** : ouverture TCP, `loop_start()`, attente du CONNACK via un `threading.Event` (timeout court 3 s), puis `loop_stop()` + `disconnect()` dans un `finally`. **Pas** de `loop_forever`, pas d'abonnement durable, pas de `publish`, pas de subscriber, pas de DB. `client_factory` injectable pour tester sans Mosquitto (faux client pilotant `on_connect`). Helper module-level `_default_mqtt_client_factory(config)` qui importe `paho.mqtt.client` **paresseusement** (aligné sur `mqtt/subscriber.py`, `CallbackAPIVersion.VERSION2`) — rien n'est importé tant que `--mqtt` n'est pas passé. Trois résultats : `ok` si CONNACK reason code 0 (`[OK] broker MQTT — connexion réussie à host:port`) ; `fail` `authentification refusée` si reason code d'auth (détection `_is_mqtt_auth_failure` : codes `{4, 5, 134, 135}` couvrant MQTT 3.1.1 et MQTT 5, fallback textuel `autoris`/`authoriz`/`password` si `int()` échoue sur un `ReasonCode`) ; `fail` `connexion impossible à host:port` si `connect()` lève (TCP refusé, hôte injoignable) ou si le CONNACK n'arrive pas (`(timeout)`) ; `fail` `connexion refusée par le broker à host:port` pour tout autre reason code non nul. Message **sobre** : pas de stacktrace, **jamais** le mot de passe (transmis à paho via `username_pw_set` mais absent de toute sortie). `run_all(*, test_db=False, test_mqtt=False)` enrichi : helper `_mqtt_check(env)` charge la config et appelle `check_mqtt_broker` ; si `load_iot_config()` lève `ValueError`, le check MQTT reste un `skip` (`configuration invalide — voir le check configuration ci-dessus`) **sans masquer** le `fail` du check configuration. `main(args)` détecte `--mqtt` (cumulable avec `--db`) — lecture simple, pas d'argparse. `info_mqtt_not_tested()` met à jour son message : `non testé par défaut — passe --mqtt pour vérifier le broker`. Help text enrichi dans `forge_cli/help_dispatch.py` (description une ligne + bloc rich text : usage cumulable `--db --mqtt`, section `--mqtt` avec les 3 résultats, rappel import paresseux et mot de passe jamais affiché). Page [`docs/iot/doctor.md`](../iot/doctor.md) : bandeau de statut réécrit (trilogie, plus de « reporté »), usage à 4 lignes, tableau des vérifications (ligne broker MQTT `skip`/`ok`/`fail` activée par `--mqtt`), **section « Sortie exemple — avec `--mqtt` »** (OK / connexion impossible / auth refusée + astuce ateliers Mosquitto), parcours recommandé à 6 étapes, limites et tickets suivants actualisés. Tests `tests/test_iot_doctor_mqtt_001.py` (≈30 cas — `check_mqtt_broker` succès (reason 0 → ok, host:port dans le détail, `connect()` appelé avec host/port, connexion brève sans subscribe/publish/loop_forever, cleanup loop_stop+disconnect), auth (reason 5, reason 134, `ReasonCode` texte-seul `Not authorized`), erreurs (connect refused → fail sans loop_start, OSError réseau, timeout `fire_connack=False` + `connect_timeout=0.05` → fail timeout avec cleanup, reason 3 → fail générique broker), credentials (`username_pw_set` appelé si username, pas sinon), password sentinel jamais leaké (détail ok et détail auth), `run_all(test_mqtt=False)` n'appelle PAS `check_mqtt_broker` (skip), `run_all(test_mqtt=True)` appelle bien le check, config invalide → mqtt skip sans masquer le fail config ni appeler le check, `main(["--mqtt"])` invoque le check / exit 1 sur fail, sans `--mqtt` mock `AssertionError` jamais appelé, `--db`+`--mqtt` coexistent, paho absent du niveau module ET absent de `sys.modules` après `run_all()` sans `--mqtt` (test subprocess interpréteur frais), `info_mqtt_not_tested` mentionne `--mqtt`, `core/` n'importe pas IoT, help dispatch mentionne `--mqtt`, `has_failures` cohérent). Tests existants mis à jour : `tests/test_iot_doctor_001.py` (`test_main_ignores_unknown_args` n'utilise plus `--mqtt` désormais reconnu ; `test_doctor_does_not_import_paho_at_module_level` vérifie l'absence d'import paho **au niveau module** plutôt qu'absence totale) ; `tests/meta/test_cli_help_flags_closing_audit_001.py` (`ALL_DISPATCHED_COMMANDS` enrichi de `iot:doctor` et `iot:init`, qui étaient dispatchés dans `forge.py` et présents dans `HELP_TEXTS_RICH` mais jamais enregistrés dans le garde-fou — corrige une régression latente du garde-fou de classification depuis `IOT-DOCTOR-001`/`IOT-INIT-COMMAND-001`). Hors périmètre respecté : aucun simulateur MQTT, aucune publication de mesure, aucun subscriber automatique, aucun stockage SQL, aucune route HTTP, aucun Forge Design, pas de TLS/ACL avancé, pas de test de topic subscribe/publish, pas de capteur réel. Avec ce ticket, la trilogie `doctor` est complète et un utilisateur peut diagnostiquer config + package + migration + table + broker avant toute ingestion. Prochain ticket : `IOT-SIMULATOR-001` (script de publication MQTT factice pour ateliers) ou intégration Forge Design IoT au-dessus de l'API HTTP JSON. |
| `IOT-DOCTOR-DB-001` | **livré** | Option `--db` pour `forge iot:doctor` — vérification de l'accès à la table `iot_events` en base, **après** `forge iot:init && forge migration:apply`. Boucle le cycle doctor → init → apply → doctor --db. Nouvelle fonction `check_database_table(fetch_one_func=None)` dans `packages/forge-mvc-iot/forge_mvc_iot/cli/doctor.py` : `fetch_one_func` injectable pour les tests, sinon **import paresseux** de `core.database.db.fetch_one` (zéro import DB tant que `--db` n'est pas passé). Exécute `SELECT COUNT(*) AS n FROM iot_events`. Trois statuts distingués via détection robuste : `ok` si la requête réussit (`[OK] table accessible (N événement(s))`) ; `warn` si la table est absente (détection `errno == 1146` MariaDB `ER_NO_SUCH_TABLE` OU texte `"doesn't exist"` en fallback si l'exception est wrappée) avec conseil `Conseil : lance forge iot:init puis forge migration:apply` ; `fail` pour toute autre exception (connexion refusée, accès refusé, base inexistante…) avec message sobre `connexion MariaDB impossible — <Type>: <message>` (pas de stacktrace, pas de SQL applicatif, jamais de mot de passe — les drivers MariaDB n'incluent que `using password: YES/NO`). `run_all(*, test_db=False)` enrichi pour brancher `check_database_table()` ou `info_db_not_tested()` selon le flag. `main(args)` détecte `--db` dans la liste d'arguments — pas d'argparse, lecture simple. `info_db_not_tested()` met à jour son message : `non testée par défaut — passe --db pour vérifier l'accès à la table`. Convention de cohérence : `warn` ne fait **pas** exit 1 (alignement avec Forge Core `doctor`) — un warn signale « apply manquante », pas un blocage. Help text enrichi dans `forge_cli/help_dispatch.py` (bloc rich text iot:doctor décrit maintenant l'option `--db` et ses 3 statuts possibles). Page [`docs/iot/doctor.md`](../iot/doctor.md) : usage avec et sans `--db`, tableau des vérifications avec colonne « Activée par », sortie exemple avec `--db` pour les 3 cas (OK 42 événements, WARN table absente avec conseil, FAIL connexion impossible), **section « Parcours recommandé »** end-to-end (doctor → init → apply → doctor --db → run). Tests `tests/test_iot_doctor_db_001.py` (≈25 cas — `check_database_table` succès (count int, zéro count, row None), absence table (errno 1146, fallback texte `doesn't exist`, conseil forge iot:init + forge migration:apply présent), erreurs connexion (access denied 1045, can't connect 2003, unknown database 1049, exception générique, message sobre sans Traceback ni SQL), password sentinel non leaké, `run_all(test_db=False)` n'appelle PAS `check_database_table` (info_db_not_tested utilisé), `run_all(test_db=True)` appelle bien `check_database_table`, `main(["--db"])` invoque le check et fait exit 1 sur fail, exit 0 sur warn (warn != failure), sans `--db` un mock qui lèverait `AssertionError` n'est jamais appelé (preuve qu'aucun import DB), `--mqtt` reste réservé, `info_db_not_tested` mentionne `--db`, `core/` n'importe toujours pas IoT, garde-fou : `from core.database` n'apparaît PAS au niveau module dans doctor.py (uniquement dans le corps de `check_database_table`), help dispatch mentionne `--db`). Test existant `tests/test_iot_doctor_001.py::test_main_ignores_unknown_args` mis à jour : `--db` est désormais reconnu, on garde `--mqtt` et `--unknown-flag` comme args ignorés. Hors périmètre respecté : aucun broker MQTT, aucun `--mqtt`, aucune création de table, aucun `migration:apply` automatique, aucun repository modifié, aucune API HTTP modifiée, aucun starter modifié fonctionnellement, aucun simulateur, aucune intégration Forge Design. Avec ce ticket, le cycle complet welcome-iot devient lisible : `forge iot:doctor` (4 OK + 2 SKIP) → `forge iot:init` (copie) → `forge migration:apply` (DDL) → `forge iot:doctor --db` (5 OK + 1 SKIP : table accessible 0 événement) → ingestion via subscriber ou publication MQTT. Prochain ticket : `IOT-SIMULATOR-001` (script de publication MQTT factice) ou `IOT-DOCTOR-MQTT-001` (option `--mqtt` symétrique pour tester le broker). |
| `IOT-INIT-COMMAND-001` | **livré** | Nouvelle commande `forge iot:init` qui copie la migration Forge IoT du package vers `mvc/migrations/` du projet. Boucle le parcours du starter `welcome-iot` : `forge iot:doctor` → `forge iot:init` → `forge migration:apply` → `forge run`. Module `packages/forge-mvc-iot/forge_mvc_iot/cli/init.py` qui expose : `iter_iot_migration_resources()` (itère les `.sql` packagés via `importlib.resources.files("forge_mvc_iot") / "migrations"`), `init_iot_migrations(project_root: Path) -> int` (logique pure et testable), `main(args)` (point d'entrée qui appelle `init_iot_migrations(Path.cwd())`). Comportement strictement scoped : aucune connexion DB, aucun SQL exécuté, aucun subscriber, aucun rollback, pas de choix interactif. **Idempotent** — la commande compare bit-à-bit le contenu et : copie si absent, signale `[OK] déjà présente (identique)` si même contenu (exit 0), **refuse l'écrasement** avec `[WARN] existe et diffère — aucune modification` si l'utilisateur a modifié sa copie locale. Crée `mvc/migrations/` si absent. Si `mvc/` absent → `[ERREUR] Ce dossier ne ressemble pas à un projet Forge` exit 1. Branchement dans `forge.py` : `iot:init` dispatché vers `forge_mvc_iot.cli.init.main`, import paresseux avec `cli_fail` propre si `forge-mvc-iot` n'est pas installé (Forge Core continue à tourner sans l'opt-in). Help text ajouté dans `forge_cli/help.py` (section IoT, ligne sous `iot:doctor`) et `forge_cli/help_dispatch.py` (entrée `HELP_DESCRIPTIONS` + bloc `HELP_TEXTS_RICH` complet : usage, comportement, prérequis, limites, suite recommandée). Page [`docs/iot/init-command.md`](../iot/init-command.md) : objectif, usage, flux recommandé end-to-end, comportement par cas (copie/idempotent/conflit/dossier inexistant/hors projet), lecture importlib.resources, hors périmètre, module opt-in absent. Pages existantes mises à jour : `docs/iot/doctor.md` (section migration manquante pointe maintenant `forge iot:init`) et `docs/starters/welcome-iot/index.md` (l'instruction manuelle `cp packages/.../migrations/*.sql ...` est remplacée par `forge iot:init && forge migration:apply`). Section IoT MkDocs étendue. Tests `tests/test_iot_init_command_001.py` (≈25 cas — itération ressources (au moins un `.sql`, fichier attendu présent, contenu bit-à-bit aligné sur `importlib.resources`), copie (fichier créé sous `mvc/migrations/`, contenu identique à la ressource, `mvc/migrations/` créé si absent avec message `[INFO]`, output contient `[OK] Migration IoT copiée` et hint `forge migration:apply`), idempotence (deuxième run retourne 0, message `déjà présente (identique)`, `mtime` inchangé prouvant l'absence de réécriture), pas d'écrasement silencieux (fichier custom préservé, `[WARN]` affiché, pas de hint apply puisque rien n'a été ni copié ni reconnu identique), hors projet Forge (exit 1, message `[ERREUR]` clair, aucun `mvc/` créé), `main()` (utilise `Path.cwd()` via `monkeypatch.chdir`, retourne 1 hors projet, ignore args inconnus), garde-fous (pas d'import `core.database`/`mariadb`/subscriber/`paho`, pas de migration_apply auto, pas d'import IoT dans `core/`), branchement CLI (`command == "iot:init"` dans `forge.py`, import paresseux dans la branche pas en tête de fichier, help text présent dans `help.py` et `help_dispatch.py` avec rich text mentionnant `forge migration:apply`). Hors périmètre respecté : aucun `forge migration:apply` automatique, aucune connexion DB, aucune vérification de table existante, aucun broker MQTT, aucun subscriber, aucun starter modifié fonctionnellement, aucun dashboard, aucune intégration Forge Design, aucun migration rollback, aucun choix interactif. Avec ce ticket, le flux end-to-end welcome-iot → ingestion devient : `forge new mon-projet --starter welcome-iot && forge iot:doctor && forge iot:init && forge migration:apply && forge run` — 5 commandes, zéro édition manuelle, zéro chemin filesystem à connaître. Prochain ticket : `IOT-DOCTOR-DB-001` (test connexion + `SELECT COUNT(*) FROM iot_events` via `forge iot:doctor --db`) ou `IOT-SIMULATOR-001` (script de publication MQTT factice pour ateliers BTS CIEL). |
| `STARTER-WELCOME-IOT-001` | **livré** | Premier starter pédagogique Forge IoT — `welcome-iot` (nom public **Bonjour IoT**). Fonctionne sans broker MQTT et sans table créée — équivalent IoT du starter `welcome`. `forge_cli/starters/data/welcome-iot/` : `starter.json` (`id welcome-iot`, `number 15`, alias `welcome-iot`/`welcome_iot`/`bonjour-iot`/`bonjour_iot`/`iot`/`15`, `kind skeleton`, `requires_db: false`, `home_route /welcome-iot`, `routes_marker welcome-iot`), `routes.py.snippet` (quatre routes pédagogiques + `register_iot_routes(router)` qui ajoute l'API officielle `/api/iot/*` en parallèle, marqueurs `# forge-starter:welcome-iot:start|end`), `files/mvc/controllers/welcome_iot_controller.py` (extends `BaseController`, imports `Request`/`Response` + explicitement `forge_mvc_iot.config.load_iot_config` et `forge_mvc_iot.storage.IotEventRepository`, quatre méthodes typées `Request -> Response`). Routes : `GET /welcome-iot` → `Response.text("Bonjour Forge IoT")` ; `GET /welcome-iot/inspect` → JSON de la configuration IoT avec mot de passe **toujours masqué** par `"***"` (ou `null` si absent) — politique alignée sur `IotConfig.__repr__` ; `GET /welcome-iot/events` → `IotEventRepository().list_recent(limit=20)` enveloppé `{"events": [...]}` ou réponse pédagogique `{"error": "iot_storage_not_ready", "message": "...applique la migration..."}` en HTTP 503 si le repo échoue (table absente, base coupée, etc.) ; `GET /welcome-iot/device/{site}/{device_id}` → `find_by_device(site, device_id, limit=20)` enveloppé `{"site", "device_id", "events"}` ou même fallback 503. Aucun subscriber MQTT lancé par le starter (lecture HTTP uniquement). Aucune écriture base. Page [`docs/starters/welcome-iot/index.md`](../starters/welcome-iot/index.md) : ce que le starter installe, classes Forge utilisées (table avec liens), rappel `forge iot:doctor` avant test, tableau des URL avec résultats attendus, exemples JSON pour chaque endpoint (avec masquage), section « Comprendre ce code », « À retenir », « Après ce starter ». Tableau de synthèse `docs/starters/index.md` enrichi (ligne `Bonjour IoT`) et nouvelle section « Démonstrateur IoT (sans broker requis) ». Nav MkDocs étendue (`mkdocs.yml`). Tests `tests/test_starter_welcome_iot_001.py` (≈40 cas — présence fichiers, `starter.json` (id, nom `Bonjour IoT`, `kind skeleton`, `requires_db: false`, `home_route`, `routes_marker`, 6 alias résolvables, `status available`, `check_paths`), routes snippet (marqueurs start/end, 4 URL présentes, import controller, import `register_iot_routes`, groupe `public=True`), contrôleur statique AST (imports `Request`/`Response`/`BaseController`/`load_iot_config`/`IotEventRepository`, classe extends `BaseController`, 4 méthodes typées `Request -> Response`), comportement runtime via `FakeRequest` + import dynamique du contrôleur (`index` retourne `"Bonjour Forge IoT"`, `inspect` retourne défauts puis mot de passe masqué après `monkeypatch.setenv` username/password, `events` 503 pédagogique sur erreur repo (vérifie qu'aucune fuite stacktrace), envelope `{"events": [...]}` sur succès, `find_by_device` même comportement + vérifie que `site`/`device_id` sont bien passés au repo via `route_params`), garde-fous (aucun import `MqttSubscriber` ni `loop_forever`/`loop_start` dans contrôleur ou snippet, aucun `.insert(` dans contrôleur, `core/` n'importe pas `forge_mvc_iot`), documentation (page existe, h1 `# Bonjour IoT`, listé dans synthèse, nav, roadmap mentionne ticket). Hors périmètre respecté : pas de capteur obligatoire, pas de broker MQTT obligatoire, pas de publication MQTT automatique, pas de subscriber lancé, pas de migration appliquée automatiquement, pas de `forge iot:init`, pas d'auth API, pas de dashboard HTML, pas d'intégration Forge Design, pas de code Arduino, pas de downlink. Avec ce starter, un utilisateur peut faire `forge new mon-projet --starter welcome-iot && forge iot:doctor && forge run` et voir Bonjour Forge IoT, inspect, et un message clair sur les événements — entièrement sans broker ni base. Prochain ticket : à arbitrer (Mosquitto local + capteur simulé pour ingestion réelle, `forge iot:init` pour la migration, ou doctor `--mqtt`/`--db`). |
| `IOT-PACKAGE-DATA-MIGRATIONS-001` | **livré** | Empaquetage des migrations SQL Forge IoT avant le starter pédagogique. Le fichier `20260528120000_create_iot_events.sql` est **déplacé** de `packages/forge-mvc-iot/migrations/` (chemin externe, non embarqué par `setuptools.packages.find`) vers `packages/forge-mvc-iot/forge_mvc_iot/migrations/` (sous-package Python avec `__init__.py`). Le `pyproject.toml` déclare `[tool.setuptools.package-data] forge_mvc_iot = ["migrations/*.sql"]` pour que les `.sql` voyagent dans la wheel et le sdist (vérifié `python -m build`). Le doctor (`IOT-DOCTOR-001`) abandonne le path-traversal `Path(forge_mvc_iot.__file__).parent.parent` au profit d'`importlib.resources.files("forge_mvc_iot") / "migrations"` — fonctionne identiquement en install éditable et en install PyPI. Test existant `tests/test_iot_storage_migration_001.py` mis à jour : `MIGRATIONS_DIR = IOT_PKG_DIR / "forge_mvc_iot" / "migrations"`. Sous-package `forge_mvc_iot.migrations/__init__.py` documente l'accès via `importlib.resources` (utile pour la future `forge iot:init`). Pages `docs/iot/storage-events.md` et `docs/iot/doctor.md` réécrites pour pointer la nouvelle localisation et l'API `importlib.resources`. Tests `tests/test_iot_package_data_migrations_001.py` (≈15 cas — fichier présent au nouveau chemin, `__init__.py` du sous-package, une seule migration `*_create_iot_events.sql`, ancien dossier `packages/forge-mvc-iot/migrations/` **supprimé** (test d'absence — convention CLAUDE.md §6), `pyproject.toml` déclare la section `package-data` avec `migrations/*.sql`, `importlib.resources` permet de lire la migration et le contenu contient le DDL, doctor retourne `ok` (status passe de `warn` à `ok` en install éditable) et n'utilise plus `_find_iot_package_root`, doc ne référence plus le chemin externe, mention du nouveau chemin/`importlib.resources`/`package-data` dans la doc, `COLUMNS`/`TABLE_NAME` toujours alignés en sanity). Vérification `python -m build` réelle : le sdist `forge_mvc_iot-1.0.0b11.tar.gz` et la wheel `forge_mvc_iot-1.0.0b11-py3-none-any.whl` contiennent le `.sql` sous `forge_mvc_iot/migrations/`. Hors périmètre respecté : aucune commande `forge iot:init`, aucune copie automatique vers `mvc/migrations/`, aucune application de migration, aucune connexion DB, aucun subscriber, aucun starter, aucun changement du DDL. Prochain ticket : `IOT-STARTER-MQTT-HELLO-001` débloqué — le starter peut s'appuyer sur des migrations qui voyagent réellement avec le module. |
| `IOT-DOCTOR-001` | **livré** | Diagnostic statique `forge iot:doctor` — **avant** le starter pédagogique. Volontairement scoped : pas de connexion broker, pas de connexion base ; les options `--mqtt` et `--db` viendront dans des tickets dédiés pour ne pas mélanger CLI, réseau MQTT et MariaDB. Module `packages/forge-mvc-iot/forge_mvc_iot/cli/doctor.py` (et `cli/__init__.py`) qui expose : `CheckResult(status: "ok"|"warn"|"fail"|"skip", label, detail, lines)` aligné sur `forge_cli.doctor` (Forge Core), six fonctions de check (`check_package_importable`, `check_config_loadable(env)`, `check_migration_present`, `check_http_api_registrable`, `info_mqtt_not_tested`, `info_db_not_tested`), orchestration `run_all`/`has_failures`/`print_report`/`main(args)`. Le check de configuration affiche les valeurs sur sous-rapport multi-lignes avec mot de passe **masqué** par `***` (jamais en clair). Le check migration cherche `packages/forge-mvc-iot/migrations/*_create_iot_events.sql` via `Path(forge_mvc_iot.__file__).parent.parent` (install éditable → `ok`, install PyPI sans ressources shippées → `warn` avec guidance, pas `fail` pour ne pas casser hors-dev). Branchement dans `forge.py` : `iot:doctor` dispatché vers `forge_mvc_iot.cli.doctor.main`, import paresseux dans la branche avec `cli_fail` propre si `forge-mvc-iot` n'est pas installé (Forge Core continue à tourner sans l'opt-in). Help text ajouté dans `forge_cli/help.py` (section IoT) et `forge_cli/help_dispatch.py` (entrée `HELP_DESCRIPTIONS` + bloc `HELP_TEXTS_RICH` complet : usage, vérifications, options, limites, code de sortie). Page [`docs/iot/doctor.md`](../iot/doctor.md) : objectif, usage, tableau des vérifications, codes de sortie, sortie exemple (default et avec auth), cas d'erreur typiques, limites, futurs tickets `--mqtt`/`--db`. Section IoT MkDocs étendue. Tests `tests/test_iot_doctor_001.py` (≈25 cas — chaque check unitairement (package OK + version, config OK + lignes, masquage password vs username en clair, config invalide → fail, migration OK + nom du fichier, API HTTP OK, MQTT/DB info `skip` avec mention `--mqtt`/`--db`), orchestration (`run_all` retourne 6 résultats avec les labels attendus, `has_failures` ne compte que `fail` (pas `warn`/`skip`), `print_report` produit l'en-tête + tags + résumé + sous-lignes), entrée `main` (retourne 0 en env monorepo, accepte `None`, ignore args inconnus), branchement CLI (`forge.py` contient `command == "iot:doctor"`, import paresseux, help text présent dans `help.py` et `help_dispatch.py`), garde-fous périmètre (`doctor.py` n'importe pas paho, ni `core.database`, ni `mqtt.subscriber`). Hors périmètre respecté : aucune connexion broker MQTT, aucune connexion base MariaDB, aucun appel réel au subscriber, aucun starter livré, aucun packaging fix (l'ABSENCE de ressources sur PyPI install est notée comme `warn` mais pas corrigée — ticket dédié à venir). Note de packaging : `packages/forge-mvc-iot/pyproject.toml` n'inclut pas (encore) le dossier `migrations/` dans la distribution PyPI — `find packages = ["forge_mvc_iot*"]` ne récupère que le Python package. C'est volontairement laissé pour un futur ticket d'empaquetage qui ajoutera `[tool.setuptools.package-data]` ou déplacera les ressources dans le Python package. Le doctor signale ce cas par un `warn` avec guidance. Prochain ticket : `IOT-STARTER-MQTT-HELLO-001` — starter pédagogique « capteur simulé + lecture Forge » qui peut désormais être livré sereinement puisque le diagnostic est en place. |
| `IOT-HTTP-API-001` | **livré** | Première API HTTP JSON Forge IoT — **lecture uniquement**, opt-in, branchement explicite par l'application. Module `packages/forge-mvc-iot/forge_mvc_iot/http.py` qui expose : la fonction publique `register_iot_routes(router, *, repository=None)` (enregistre trois routes nommées sur un `core.http.router.Router` ; instancie `IotEventRepository()` par défaut si aucun repo fourni), la classe `IotHttpController(repository)` exposée pour usage avancé (compose tes propres routes), et trois constantes de patterns `ROUTE_LIST_EVENTS` / `ROUTE_EVENTS_BY_DEVICE` / `ROUTE_DEVICE_COUNT`. Trois routes branchées : `GET /api/iot/events` → `repo.list_recent(limit=...)` (réponse `{"events": [...]}`) ; `GET /api/iot/events/{site}/{device_id}` → `repo.find_by_device(site, device_id, limit=...)` (même enveloppe) ; `GET /api/iot/devices/{site}/{device_id}/count` → `repo.count_by_device(site, device_id)` (réponse `{"site", "device_id", "count"}`). Toutes les routes sont `public=True csrf=False api=True`. Le `?limit=` est validé côté contrôleur **avant** l'appel repository : absent → `DEFAULT_LIMIT=100`, non convertible / nul / négatif / `>MAX_LIMIT=1000` → réponse `400 {"error": "invalid_limit", "message": "..."}` et `repo.list_recent` jamais appelé. Erreurs DB capturées (large `except Exception` après le repo, `logger.exception` côté serveur) → réponse sobre `500 {"error": "internal_server_error"}` sans aucune fuite SQL/stacktrace. Sérialisation `received_at` : `datetime` UTC-aware reformaté avec suffixe `Z` (pas `+00:00`), `datetime` non-UTC converti en UTC d'abord, `datetime` naïf assumé UTC — sortie toujours `YYYY-MM-DDTHH:MM:SSZ`. La clé `metadata_json` (interne stockage) n'apparaît **jamais** dans les réponses HTTP (vérifié même si un consommateur facétieux fait fuiter la clé dans son dict). API publique exposée au niveau racine : `from forge_mvc_iot import register_iot_routes`. Page [`docs/iot/http-api.md`](../iot/http-api.md) : tableau des routes, branchement explicite, paramètres, exemples curl/JSON, sérialisation `received_at`, format d'erreurs, usage direct du contrôleur. Section IoT MkDocs étendue. Tests `tests/test_iot_http_api_001.py` (≈35 cas — registration (3 routes, résolution des 3 patterns, noms stables, public/api=True, constantes alignées, défaut sans repository), `list_events` (default limit, custom limit, enveloppe, ISO Z, conversion fuseau, `metadata_json` non propagé, `metadata=None` → JSON `null`, liste vide), validation limit (param invalide → 400, repository non appelé, vide → défaut, MAX_LIMIT accepté), `find_by_device` (extraction `site`/`device_id` du chemin, appel repo correct, limit forwardé, enveloppe, 400 sur limit invalide), `count_by_device` (appel repo, enveloppe `{site, device_id, count}`, count=0), erreurs DB → 500 sobre sur les 3 routes (vérification absence `SELECT`/nom de table dans le body), garde-fous (pas d'import IoT dans `core/`, pas de SQL dans `http.py`, pas d'import `core.database`/`mariadb`, API publique exposée au racine, contrôleur utilisable standalone). Hors périmètre respecté : aucune authentification Bearer, aucun POST/ingestion HTTP, aucune pagination par offset, aucun filtre temporel, aucune agrégation, aucun dashboard HTML, aucune intégration Forge Design, aucun downlink. Prochain ticket : `IOT-DOCTOR-001` recommandé avant `IOT-STARTER-MQTT-HELLO-001` — diagnostiquer config + package + migration avant de livrer un starter pédagogique. |
| `IOT-STORAGE-REPOSITORY-READ-001` | **livré** | Premières méthodes de lecture sur `IotEventRepository` — exposées **avant** l'API HTTP pour que `IOT-HTTP-API-001` n'ait plus qu'à brancher des routes sur des méthodes déjà testées. Trois méthodes ajoutées : `list_recent(*, limit=DEFAULT_LIMIT=100) -> list[dict]` (ordre `received_at DESC`), `find_by_device(site, device_id, *, limit=DEFAULT_LIMIT) -> list[dict]` (filtre `WHERE site=? AND device_id=?`, ordre DESC), `count_by_device(site, device_id) -> int` (utilise `COUNT(*) AS n`, retourne `0` si `fetch_one` renvoie `None`). SQL exposé publiquement (charte v2 §5) : trois constantes `SELECT_IOT_EVENTS_RECENT_SQL` / `SELECT_IOT_EVENTS_BY_DEVICE_SQL` / `COUNT_IOT_EVENTS_BY_DEVICE_SQL`, toutes en placeholders qmark `?`. Validation `limit` stricte : `int` (les `bool` sont refusés explicitement bien que sous-classe d'`int`), dans `1..MAX_LIMIT=1000`, sinon `TypeError`/`ValueError`. Transformation systématique des lignes brutes via `_row_to_event_dict` : `metadata_json` (chaîne JSON ou `None`) est parsée en `metadata` (dict ou `None`), le détail de sérialisation reste interne au stockage. `Protocol DbAdapter` étendu avec `fetch_one` et `fetch_all` (toujours conforme à `core.database.db` de Forge). API publique du sous-package `forge_mvc_iot.storage` enrichie (les nouvelles constantes et la classe restent les seuls points d'entrée officiels). Page [`docs/iot/storage-events.md`](../iot/storage-events.md) : nouvelle sous-section « Méthodes de lecture » (signatures, forme du dict retourné, comportement metadata, ordre `received_at DESC`, validation `limit`), sous-section « SQL exposé » qui liste les trois constantes. Tableau de découpage mis à jour. Tests `tests/test_iot_storage_repository_read_001.py` (≈30 cas — SQL exposé contient `FROM iot_events`/`ORDER BY received_at DESC`/`LIMIT ?` selon la requête, pas de placeholder nommé, `list_recent`/`find_by_device`/`count_by_device` appellent `fetch_all`/`fetch_one` avec le bon SQL et les bons params (defaults et override), retour `list_recent`/`find_by_device` = liste de dicts avec `metadata` parsé en dict ou `None`, clé `metadata_json` ne fuite pas au consommateur, `count_by_device` retourne `int` même quand `fetch_one` retourne `None`, erreurs DB propagées sur les 3 méthodes, validation `limit` (zéro/négatif refusé, `>MAX_LIMIT` refusé, `MAX_LIMIT` accepté en bordure, types non-int refusés, `bool` refusé), garde-fous (pas d'import paho/subscriber, pas de routes HTTP `@route`/`Router(`/`Response(`/`@app.route` dans le repository), API publique storage exporte les nouvelles constantes, sanity `insert` toujours fonctionnel après ajout des lectures). Hors périmètre respecté : aucune route HTTP, aucun subscriber tiré, aucune pagination par offset, aucun filtre temporel `since/until`, aucune agrégation/downsampling, aucune intégration Forge Design. Prochain ticket : `IOT-HTTP-API-001` branche `/api/iot/events` (et éventuellement `/api/iot/events/{site}/{device_id}`) sur ces méthodes — plus de SQL à écrire côté contrôleur. |
| `IOT-STORAGE-REPOSITORY-001` | **livré** | Premier branchement réel entre le contrat de stockage IoT et la base Forge. Module `packages/forge-mvc-iot/forge_mvc_iot/storage/repository.py` qui expose la classe `IotEventRepository(db_adapter=None)` et le `Protocol` `DbAdapter` (interface minimale : `execute(sql, params)`). La méthode `insert(measurement, *, received_at=None) -> Any` appelle `build_insert_iot_event_sql(measurement, received_at=received_at)` puis délègue à `self._db.execute(sql, params)` et retourne le résultat brut de l'adapter. Par défaut, l'adapter est `core.database.db` (module Forge Core, importé paresseusement par `_default_db_adapter()` pour ne déclencher aucun import dans les tests qui injectent leur propre mock). **Premier import de `core.database` côté `forge-mvc-iot`** — sens de dépendance préservé : `forge-mvc-iot` dépend de `forge-mvc`, jamais l'inverse. Aucune création automatique de table (la migration `IOT-STORAGE-MIGRATION-001` doit avoir été appliquée), aucun `commit`/`rollback` manuel (délégué à Forge), aucune interception silencieuse d'erreur (les exceptions DB sont propagées telles quelles). API publique exposée par `forge_mvc_iot.storage` (mise à jour de `storage/__init__.py` qui réexporte `IotEventRepository`, `DbAdapter`, et les fonctions/constantes de `events`). Page [`docs/iot/storage-events.md`](../iot/storage-events.md) enrichie : nouvelle section « Repository d'insertion » (API, adapter injectable avec exemples mock et `lastrowid`, flux subscriber→repository→base sous forme de schéma ASCII, encart précisant que le branchement `on_measurement=repo.insert` reste un exemple documentaire — le subscriber n'importe **pas** le repository à ce ticket), tableau de découpage marque `IOT-STORAGE-REPOSITORY-001` livré. Tests `tests/test_iot_storage_repository_001.py` (≈22 cas — construction avec adapter injecté ou par défaut (`repo._db is core.database.db`), `_default_db_adapter()` retourne bien le module, Protocol `DbAdapter` expose `execute`, délégation à l'adapter (appelé une fois, SQL = `INSERT_IOT_EVENT_SQL`, retour brut transmis), paramètres alignés sur `COLUMNS` (`site`/`device_id`/`kind`/`value`/`unit`/`timestamp`/`metadata_json`/`received_at`), `received_at` forwardé, défaut `now(UTC)` tz-aware, `metadata=None` → Python `None`, dict → JSON déterministe `sort_keys=True`, propagation `RuntimeError` et exception custom (pas de catch silencieux), aucun `commit`/`rollback` sur l'adapter, repository n'importe pas `paho`, subscriber n'importe pas le repository, `core/` n'importe pas IoT, API publique du sous-package storage). Hors périmètre respecté : aucune création automatique de table, aucune copie automatique de migration, aucun `forge iot:init`, subscriber non branché automatiquement au repository, aucune API HTTP, aucune route, aucun dashboard, aucune intégration Forge Design, aucune déduplication, aucune rétention, aucune agrégation/downsampling, aucun TLS/ACL Mosquitto. Prochain ticket : `IOT-HTTP-API-001` — précédé idéalement d'une extension `list_recent()` dans le repository avant exposition HTTP. |
| `IOT-STORAGE-MIGRATION-001` | **livré** | Migration SQL versionnée pour la table `iot_events`. Fichier `packages/forge-mvc-iot/migrations/20260528120000_create_iot_events.sql` au format Forge (timestamp `YYYYMMDDHHMMSS` + nom + `.sql`) — placé dans le **package opt-in**, pas dans `mvc/migrations/` du framework (le module IoT possède sa migration ; l'application réelle dans la base utilisateur sera automatisée plus tard). Le DDL reprend exactement le contrat figé par `IOT-STORAGE-EVENTS-001` : `iot_events(id BIGINT UNSIGNED AUTO_INCREMENT PK, site/device_id/kind VARCHAR(64) NOT NULL, value DOUBLE NOT NULL, unit VARCHAR(32) NOT NULL, timestamp VARCHAR(40) NOT NULL, metadata_json TEXT NULL, received_at DATETIME(6) NOT NULL)`, deux index `idx_iot_events_site_device (site, device_id)` et `idx_iot_events_received_at (received_at)`, `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`, `CREATE TABLE IF NOT EXISTS` (idempotente). En-tête commentaire référence le ticket et le module. Tests `tests/test_iot_storage_migration_001.py` (≈25 cas — présence et nommage `YYYYMMDDHHMMSS_create_iot_events.sql`, unicité du fichier `*_create_iot_events.sql`, présence de `iot_events`, `CREATE TABLE IF NOT EXISTS`, `ENGINE=InnoDB`/`utf8mb4`/`utf8mb4_unicode_ci`, chaque colonne `COLUMNS` typée, `id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT`, `PRIMARY KEY (id)`, types stricts pour chaque colonne (`VARCHAR(64)`/`DOUBLE`/`VARCHAR(32)`/`VARCHAR(40)`/`TEXT NULL`/`DATETIME(6)`), les deux index présents, absence d'`UNIQUE` (hors périmètre déduplication), `storage/events.py` ne pulled toujours pas `core.database` ni `mariadb`, cohérence ordre des colonnes DDL ↔ `COLUMNS` Python). Page [`docs/iot/storage-events.md`](../iot/storage-events.md) mise à jour : section « Schéma SQL cible » pointe désormais explicitement le fichier de migration livré et indique que `COLUMNS` reste la source de vérité ; mention « pas de migration SQL » retirée des Hors périmètre ; tableau de découpage rappelle livré/à venir. Hors périmètre respecté : aucun repository Python, aucun `db.execute`, aucun appel automatique depuis le subscriber, aucune API HTTP, aucune CLI, aucune contrainte d'unicité/déduplication, aucune intégration Forge Design, aucune agrégation/rétention. Prochain ticket : `IOT-STORAGE-REPOSITORY-001` branche `core.database.db.execute(sql, params)` sur le couple produit par `build_insert_iot_event_sql`. |
| `IOT-STORAGE-EVENTS-001` | **livré** | Contrat SQL du stockage des événements IoT, **sans branchement base** (suit le découpage IOT-STORAGE-EVENTS-001 contrat → IOT-STORAGE-MIGRATION-001 migration → IOT-STORAGE-REPOSITORY-001 insertion → IOT-HTTP-API-001 lecture). Module pur `packages/forge-mvc-iot/forge_mvc_iot/storage/events.py` qui expose : `TABLE_NAME = "iot_events"`, `COLUMNS = (site, device_id, kind, value, unit, timestamp, metadata_json, received_at)` — `id` exclu car généré par la base, `INSERT_IOT_EVENT_SQL` (constante chaîne avec placeholders qmark `?` cohérents avec le starter Contacts et `core.database.db.execute`), `serialize_measurement_for_storage(measurement, *, received_at=None) -> dict[str, object]` qui produit un dict prêt pour insertion (timestamp string ISO 8601 préservé, metadata sérialisée en JSON via `json.dumps(sort_keys=True, ensure_ascii=False)` ou `None` si absente, `received_at` côté serveur en `datetime.now(UTC)` si non fourni), et `build_insert_iot_event_sql(measurement, *, received_at=None) -> tuple[str, tuple]` qui retourne `(sql, params)` directement consommable par le futur repository. Schéma SQL cible documenté dans la page mais **non appliqué** : `iot_events(id BIGINT UNSIGNED AUTO_INCREMENT PK, site/device_id/kind VARCHAR(64), value DOUBLE, unit VARCHAR(32), timestamp VARCHAR(40), metadata_json TEXT NULL, received_at DATETIME(6))` avec deux index `(site, device_id)` et `received_at`. Page [`docs/iot/storage-events.md`](../iot/storage-events.md) : API, schéma SQL informatif, décisions verrouillées (module pur, SQL visible charte v2 §5, placeholders qmark, UTC partout, JSON déterministe, `id` exclu), exemples, rappel du découpage. Section IoT MkDocs étendue. Tests `tests/test_iot_storage_events_001.py` (≈30 cas — constantes table/colonnes/exclusion `id`, sérialisation (clés, types préservés `int`/`float`, datetime tz-aware UTC, fenêtre temporelle `now(UTC)`, metadata None vs dict vs vide, JSON déterministe sort_keys, UTF-8 préservé `ensure_ascii=False`), construction SQL (tuple `(str, tuple)`, table cible, placeholders `?` au bon compte, pas de `%s` ni nommés, ordre des colonnes canonique, instruction unique, constante exposée), ordre des params positionnels aligné sur COLUMNS, metadata None → Python None (pour `NULL` SQL), garde-fous module pur (pas d'import `core.database`, pas d'`import mariadb`), `core/` n'importe pas IoT, intégration bout en bout deux mesures = même SQL params différents). Hors périmètre respecté : aucune migration appliquée, aucun branchement `core.database.db`, aucune API HTTP, aucune CLI, aucun dashboard, aucune intégration Forge Design, aucune rétention/agrégation/alerte. Prochain ticket : `IOT-STORAGE-MIGRATION-001` produit la migration versionnée `mvc/migrations/YYYYMMDDHHMMSS_create_iot_events.sql` puis `IOT-STORAGE-REPOSITORY-001` branche `core.database.db.execute`. |
| `IOT-MQTT-SUBSCRIBER-001` | **livré** | Premier subscriber MQTT Forge IoT, en deux modules séparés pour la testabilité. `packages/forge-mvc-iot/forge_mvc_iot/mqtt/contract.py` : parsing pur et validation du contrat ([IOT-MQTT-CONTRACT-001](../iot/mqtt-contract.md)), expose `Measurement` (dataclass frozen), `ContractError` (avec attribut `code` aligné sur la taxonomie publiée), et trois fonctions pures `parse_topic`, `parse_payload`, `parse_message`. Aucun import `paho-mqtt`. `packages/forge-mvc-iot/forge_mvc_iot/mqtt/subscriber.py` : classe `MqttSubscriber` qui prend un `IotConfig` injecté (pas de lecture directe de l'environnement), instancie un `paho.mqtt.client.Client` (CallbackAPIVersion.VERSION2), branche `on_connect`/`on_message`, applique `username_pw_set` quand un username est défini, expose une méthode publique testable `handle_message(topic, payload)` qui parse + dispatch vers `on_measurement` ou `on_contract_error`, et délègue le cycle de vie (`connect`/`disconnect`/`loop_forever`/`loop_start`/`loop_stop`) au client. Le `client_factory` est injectable — les tests passent un `MagicMock` au lieu d'un vrai broker. Décisions verrouillées : `site` et `device_id` viennent du **topic** (les champs homonymes dans le payload sont ignorés), codes d'erreur stables `TOPIC_PATTERN` / `PAYLOAD_PARSE` / `PAYLOAD_FIELD_MISSING` / `PAYLOAD_FIELD_TYPE` / `PAYLOAD_VALUE_FORMAT`, validation timestamp ISO 8601 UTC stricte (regex + `datetime.fromisoformat`, refus du séparateur espace, refus de `+00:00`, refus des dates invalides type `2026-02-99`), refus de `bool` comme `value`, refus des valeurs non-string dans `metadata`. `pyproject.toml` ouvre la dépendance `paho-mqtt>=2.1,<3`. Page [`docs/iot/mqtt-subscriber.md`](../iot/mqtt-subscriber.md) avec API publique, exemple complet de script de réception, recette pour tester sans broker, comportement face aux erreurs. Section IoT MkDocs étendue. Tests `tests/test_iot_mqtt_subscriber_001.py` (≈55 cas — parsing topic valide/invalide, parsing payload valide/invalide, parse_message complet avec tous types d'erreurs (5 codes), `site`/`device_id` du payload ignorés, immutabilité `Measurement`, construction subscriber avec/sans auth, `client_factory` injecté, callbacks paho assignés, `handle_message` dispatch correct, callback erreur appelé ou log seul, abonnement uniquement si `reason_code==0`, délégation `connect`/`disconnect`/`loop_*`, dépendance `paho-mqtt` déclarée, `forge-mvc` toujours requis, aucun import IoT dans `core/`). Tests précédents nettoyés : suppression de l'assertion d'absence `paho-mqtt` dans `tests/meta/test_iot_package_scaffold_001.py` et `tests/test_iot_config_001.py` (assertions correctes au moment de leur ticket d'origine, désormais obsolètes — la dépendance est légitime à partir de ce ticket). Hors périmètre respecté : aucun stockage SQL, aucune migration, aucune route HTTP, aucune commande CLI, aucun dashboard, aucune intégration Forge Design, aucun TLS/ACL, aucun downlink vers capteur, aucun changement dans `core/`. Prochain ticket : `IOT-STORAGE-EVENTS-001`. |
| `IOT-CONFIG-001` | **livré** | Contrat de configuration MQTT du module `forge-mvc-iot`, **avant** écriture du subscriber. Module `packages/forge-mvc-iot/forge_mvc_iot/config.py` qui expose une dataclass immuable `IotConfig(frozen=True)` (champs `mqtt_host`, `mqtt_port`, `mqtt_topic`, `mqtt_client_id`, `mqtt_username`, `mqtt_password`) et une fonction pure `load_iot_config(env=None) -> IotConfig` qui lit `os.environ` par défaut ou un mapping injecté pour les tests. Six variables : `FORGE_IOT_MQTT_HOST` (défaut `localhost`, vide refusé), `FORGE_IOT_MQTT_PORT` (défaut `1883`, validé `int` dans `1..65535`), `FORGE_IOT_MQTT_TOPIC` (défaut `forge/+/+/telemetry` — wildcards d'abonnement, inverses du contrat de publication, vide refusé), `FORGE_IOT_MQTT_CLIENT_ID` (défaut `forge-iot`), `FORGE_IOT_MQTT_USERNAME` / `FORGE_IOT_MQTT_PASSWORD` (défaut `None`, empty string → `None`). Le mot de passe est **masqué** dans `repr()` (`mqtt_password='***'`) tout en restant accessible en clair via `cfg.mqtt_password` (le subscriber a besoin de la valeur pour s'authentifier). Page [`docs/iot/configuration.md`](../iot/configuration.md) avec tableau des variables, API Python, masquage, trois exemples (Mosquitto local sans auth, broker LAN avec auth, broker cloud). Section IoT MkDocs étendue. Tests `tests/test_iot_config_001.py` (≈30 cas — defaults, surcharge complète et partielle, conversion port `int`, port invalide / hors plage refusé, port valide accepté en bordure 1/65535, host vide refusé, topic vide refusé, masquage repr (avec mot de passe, avec f-string, sans mot de passe = `None`), mot de passe accessible en clair, username non masqué, immutabilité, `os.environ` lu si `env=None`, mapping injecté ne lit pas `os.environ`, pas de dépendance `paho-mqtt`, aucun import IoT dans `core/`). Hors périmètre respecté : aucune dépendance `paho-mqtt`, aucune connexion broker, aucune boucle subscriber, aucune commande CLI, aucune table SQL, aucune route HTTP, aucune intégration Forge Design, aucun TLS, aucune gestion avancée des secrets. Prochain ticket : `IOT-MQTT-SUBSCRIBER-001` reçoit un `IotConfig` en argument et n'a plus à connaître l'environnement. |
| `IOT-MQTT-CONTRACT-001` | **livré** | Contrat MQTT officiel de Forge IoT figé **avant** toute écriture de subscriber. Page [`docs/iot/mqtt-contract.md`](../iot/mqtt-contract.md) qui définit : topic canonique `forge/{site}/{device_id}/telemetry` (slug `[a-z0-9-]+`, wildcards `+`/`#` interdits en publication) ; payload JSON avec quatre champs obligatoires (`kind` string slug `[a-z0-9_-]+`, `value` number, `unit` string, `timestamp` ISO 8601 UTC suffixé `Z`) et un champ optionnel (`metadata` object). Décision verrouillée : `site` et `device_id` viennent du **topic**, jamais du payload — un message qui contient quand même ces clés voit leur valeur ignorée (la vérité est dans le topic). Trois exemples valides (minimal, avec métadonnées, humidité entière), six exemples de topics mal formés, cinq exemples de payloads invalides chacun avec sa raison. Taxonomie d'erreurs stable : `TOPIC_PATTERN`, `PAYLOAD_PARSE`, `PAYLOAD_FIELD_MISSING`, `PAYLOAD_FIELD_TYPE`, `PAYLOAD_VALUE_FORMAT` — codes destinés aux logs et aux tests du futur subscriber, pas exposés en API Python. Limites itération 1 explicites : pas de batch, pas de payload composite, pas de downlink, pas de topics commandes/config/event, pas de QoS/retain imposés, pas de `schema_version`. Section IoT MkDocs étendue (`mkdocs.yml`). Garde-fou méta `tests/meta/test_iot_mqtt_contract_001.py` (présence page, référence MkDocs, topic canonique documenté, champs obligatoires et optionnels listés, décision « topic > payload » formulée explicitement, au moins un exemple JSON valide bien typé, section exemples invalides, 5 codes d'erreur présents, statut documentaire affirmé, mention dans la roadmap). Hors périmètre respecté : aucun subscriber, aucune dépendance `paho-mqtt`, aucune validation Python runtime, aucune commande CLI, aucune table SQL, aucune route HTTP, aucune intégration Forge Design, aucune politique TLS/ACL Mosquitto, aucun downlink. Prochain ticket : `IOT-MQTT-SUBSCRIBER-001`. |
| `IOT-PACKAGE-SCAFFOLD-001` | **livré** | Squelette installable du module opt-in `forge-mvc-iot` selon ADR-005 (monorepo + distribution PyPI séparée). Crée `packages/forge-mvc-iot/` : `pyproject.toml` (name `forge-mvc-iot`, version `1.0.0b11`, `requires-python = ">=3.12"`, `dependencies = ["forge-mvc>=1.0.0b5,<2"]`, classifier `Development Status :: 1 - Planning`, `tool.setuptools.packages.find` aligné sur les autres opt-ins), `README.md` (statut scaffold, MQTT prévu non implémenté, Mosquitto recommandé local, broker cloud accepté non prioritaire, Forge Core indépendant, Forge Design IoT consommera l'API HTTP), et le package Python `forge_mvc_iot/` avec sous-dossiers vides `mqtt/`, `storage/`, `diagnostics/` (chacun avec son `__init__.py` documenté qui pointe vers le ticket d'implémentation à venir). `__version__ = "1.0.0b11"` exposé au niveau racine. Aucune dépendance `paho-mqtt`, aucun subscriber MQTT, aucune commande CLI, aucune table SQL, aucune migration, aucune route HTTP, aucune modification de `core/`, aucune modification de Forge Design. Forge Core continue à ne pas dépendre de `forge-mvc-iot` (ni en `dependencies`, ni en `optional-dependencies`). Garde-fou méta `tests/meta/test_iot_package_scaffold_001.py` (structure de fichiers, pyproject contract, indépendance Forge Core, mentions README, présence dans la roadmap, importabilité du module et de ses sous-packages). Prochaine étape : `IOT-MQTT-CONTRACT-001` (contrat de message). |
| `IOT-ARCHITECTURE-001` | **livré** | Page fondatrice [`docs/iot/architecture.md`](../iot/architecture.md) qui fige le périmètre Forge IoT avant tout développement : module opt-in `forge-mvc-iot` (futur), Forge Core autonome, broker MQTT (Mosquitto recommandé en local, cloud accepté mais non prioritaire) comme transport mais pas comme source métier, Forge Design IoT consomme uniquement les API HTTP JSON exposées par Forge (jamais le broker directement). Décisions verrouillées : Forge Core ne dépend pas de `forge-mvc-iot` ; `forge-mvc-iot` dépend de Forge Core ; aucune logique IoT dans `core/` ; SQL visible (charte v2 §5) ; API publique = contrat de complétude (charte v2 §10). Section IoT ajoutée à la navigation MkDocs (`mkdocs.yml`). Tickets jalons documentés en fin de page : `IOT-PACKAGE-SCAFFOLD-001`, `IOT-MQTT-CONTRACT-001`, `IOT-MQTT-SUBSCRIBER-001`, `IOT-CONFIG-001`, `IOT-STORAGE-EVENTS-001`, `IOT-HTTP-API-001`, `IOT-DOCTOR-001`, `IOT-STARTER-MQTT-HELLO-001`, `FORGE-DESIGN-IOT-READ-API-001`. Hors périmètre respecté : aucune création de `packages/forge-mvc-iot/`, aucune dépendance `paho-mqtt`, aucune commande CLI, aucun subscriber MQTT, aucune table SQL IoT, aucune route HTTP IoT, aucune modification de Forge Design, aucun starter IoT, aucune modification de `core/`. Garde-fou méta `tests/meta/test_iot_architecture_docs_001.py` ajouté. |

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
