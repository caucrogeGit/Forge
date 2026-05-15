# Audit CONSOLIDATION-001 — Architecture globale Forge

## Objectif

Réaliser un audit global de l'architecture Forge après la clôture des phases 4.5 à 9.1. Identifier les incohérences, zones fragiles, doublons et dettes techniques. Ne rien modifier.

Phases couvertes :
- Phase 4.5 — Auth/User avancée
- Phase 5 — Relations avancées et CRUD enrichi
- Phase 6 — Pages publiques génériques
- Phase 7 — Workflow, statistiques et modules
- Phase 8 — Starter Communes & Séjours
- Phase 9 — Profils de projet
- Phase 9.1 — Modernisation / clarification des starters historiques

---

## Synthèse

**Verdict global : Forge est architecturalement cohérent.**

Le cœur est bien découpé en 14 modules thématiques. La CLI compte 31+ commandes, toutes déléguées proprement depuis `forge.py`. Les 4 profils de projet sont cohérents. Les tests couvrent très largement les zones critiques (161 fichiers). Le packaging est minimal et justifié.

Deux incohérences mineures sont détectées : les `doc_url` des starters 2 et 5 pointent encore vers l'ancien format de documentation. Aucune dette technique critique n'est identifiée.

**4794 tests passés, 1 skipped. `compileall` OK. `mkdocs --strict` OK.**

---

## État global du framework

| Critère | État |
|---------|------|
| Core modulaire | ✅ 14 modules thématiques séparés |
| CLI cohérente | ✅ 31+ commandes déléguées depuis forge.py |
| Profils de projet | ✅ 4 profils, `standard` comme défaut |
| Starters documentés | ✅ 5 starters avec statuts clairs |
| Documentation alignée | ✅ roadmap, profils, starters, audits cohérents |
| Tests | ✅ 161 fichiers, couverture très complète |
| Packaging Python | ✅ 6 dépendances runtime justifiées |
| Packaging frontend | ✅ Tailwind CLI uniquement |
| docs/roadmap.md | ✅ Absent — seul docs/forge-roadmap.md existe |
| docs/forge-design-roadmap.md | ✅ Séparé, indépendant |

---

## Architecture core

**14 modules identifiés :**

| Module | Fichiers | Responsabilité |
|--------|----------|----------------|
| `core/auth` | 18 | Authentification complète : contrat utilisateur, sessions, tokens, MFA, OIDC, RBAC utilisateur, audit, rate-limiting |
| `core/database` | 5 | Connexion MariaDB, transactions, chargement SQL |
| `core/forms` | 4 | Champs de formulaire, validation, champs relationnels |
| `core/http` | 5 | Router, requête/réponse HTTP, helpers |
| `core/i18n` | 3 | Internationalisation, traducteur |
| `core/mail` | 9 | Configuration, envoi SMTP, templates mail, logs, transports |
| `core/modules` | 6 | Découverte de modules, registry, manifests, routes dynamiques |
| `core/mvc` | ~4 | Contrôleur de base, rendu Jinja |
| `core/security` | 6 | CSRF, RBAC générique, hachage legacy (PBKDF2), sessions legacy |
| `core/stats` | 5 | Tracking événements, schéma, consultation admin |
| `core/templating` | 3 | Gestionnaire Jinja2, contrats |
| `core/uploads` | 8 | Gestion médias, galeries, images, stockage, validation |
| `core/validation` | 3 | Décorateurs de validation |
| `core/workflow` | 4 | Transitions d'état, statuts, intégration Jinja |

**Couplage `core.auth` / `core.security` :**

Les deux modules coexistent avec des responsabilités distinctes et claires :

- `core.auth` : identité utilisateur moderne (argon2, sessions sécurisées, tokens, MFA, OIDC, RBAC utilisateur).
- `core.security` : transverse de sécurité (CSRF, sessions HTTP brutes, RBAC générique sans identité, hachage legacy PBKDF2).

`core.auth` importe certains primitives de `core.security` (sessions HTTP) — ce couplage est intentionnel et justifié. `core.security` n'importe pas `core.auth`.

**Modules les plus volumineux :**

| Fichier | Lignes | Évaluation |
|---------|--------|------------|
| `core/auth/oidc.py` | ~1011 | ⚠️ Grand, mais cohérent : flux OIDC, PKCE, state, nonce, callbacks |
| `core/auth/mfa.py` | ~799 | ⚠️ Grand, mais cohérent : TOTP, codes de récupération, challenge, revalidation |
| `core/forms/fields.py` | ~549 | Acceptable : nombreux champs spécialisés |
| `core/auth/__init__.py` | ~427 | Acceptable : ré-exports de contrats publics |

`core/auth/oidc.py` à 1011 lignes est le fichier le plus grand du core. Il reste lisible (flux OIDC bien découpé en fonctions) mais pourrait bénéficier d'un découpage interne si la complexité augmente.

**Aucun TODO / FIXME / HACK identifié dans `core/` ni `forge_cli/`.**

---

## CLI Forge

**31+ commandes disponibles, toutes déléguées depuis `forge.py` :**

| Catégorie | Commandes |
|-----------|-----------|
| Projet | `new`, `doctor`, `help`, `--version` |
| Entités | `make:entity`, `make:crud`, `make:relation`, `sync:entity`, `sync:relations` |
| Pages publiques | `make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`, `make:public-contact` |
| Uploads / médias | `upload:init`, `media:init` |
| Front | `js:init` (htmx, alpine, htmx-alpine) |
| i18n | `i18n:init`, `i18n:check` |
| Auth | `auth:init`, `auth:doctor`, `auth:status`, `auth:list-sql`, `auth:user:create`, `auth:user:list`, `auth:user:show`, `auth:user:disable`, `auth:user:enable`, `auth:user:password`, `auth:user:role:add`, `auth:user:role:remove`, `auth:user:roles` |
| Mail | `mail:init`, `mail:test`, `mail:render`, `mail:doctor`, `mail:logs` |
| Deploy | `deploy:init`, `deploy:check` |
| Starters | `starter:list`, `starter:build` |
| Modules | `module:list`, `module:install`, `module:files`, `module:routes` |
| Database | `db:init`, `db:apply` |
| Migrations | `migration:status`, `migration:apply`, `migration:make`, `migration:diff` |
| Routes | `routes:list` |
| Docs | `docs:pdf` |

**Nommage :** uniforme (`make:{ressource}` ou `{ressource}:action`). Pas d'incohérence détectée.

**Délégation :** `forge.py` délègue correctement à `forge_cli.*`. Aucune logique métier dans `forge.py`.

**Points à vérifier dans CONSOLIDATION-CLI-001 :**

- Cohérence des messages d'aide (`--help`) entre commandes.
- Couverture des cas d'erreur (commande inconnue, arguments manquants).
- Nomenclature `auth:user:*` vs `auth:*` — profondeur uniforme ?
- Commandes `deploy:*` — sont-elles stables et documentées ?

---

## Générateurs

Générateurs principaux :

- `make:entity` → `forge_cli/entities/make_entity.py`
- `make:crud` → `forge_cli/entities/make_crud.py`
- `make:relation` → `forge_cli/entities/make_relation.py`
- `make:public-{page,list,show,form,contact}` → `forge_cli/public_*.py`
- `sync:entity` → `forge_cli/entities/sync_entity.py`

**Architecture des générateurs :** chaque générateur est un module indépendant. Pas de super-classe générateur commune — acceptable pour ce volume.

**Points à vérifier dans CONSOLIDATION-CLI-001 :**

- Comportement non-écrasant (preservation du code utilisateur) — couvert par CONSOLIDATION-NON-OVERWRITE-001.
- Générateurs `make:public-*` : sont-ils testés pour tous les profils ?

---

## Auth/User et RBAC

**`core.auth` :** brique complète et autonome. Contrat utilisateur minimal (`AuthUser`), sessions sécurisées, tokens, vérification email, reset password, MFA (TOTP + codes de récupération + challenge + revalidation), OIDC (state, nonce, PKCE), RBAC utilisateur (`user_roles`), journalisation, rate-limiting.

**`core.security` :** CSRF + RBAC générique + hachage legacy. Reste indispensable pour le fonctionnement transverse (CSRF sur tous les formulaires). Ne pas supprimer.

**Starter 2 — Utilisateurs/Auth :** modernisé dans STARTER-AUTH-MODERNIZE-001. Utilise `core.auth` (`verify_password`, `login_user`, `logout_user`, `@login_required`, `get_authenticated_user_id`, `hash_password`). Conserve `core.security.session` pour CSRF (intentionnel, correct).

**Starter 4 — Suivi pédagogique :** utilise `core.security.hashing` et `core.security.session` côté auth. Acceptable : c'est un starter legacy/historique, marqué comme tel dans la documentation. Pas de modernisation prévue.

**Points à vérifier dans CONSOLIDATION-TESTS-001 :**

- Couverture des scénarios MFA + OIDC en conditions d'intégration.
- Tests `auth:user:*` CLI : commandes discrètes ou intégrées ?

---

## CRUD, relations et pages publiques

**CRUD :** générateur `make:crud` complet. Supporte pagination, recherche, tri, états vides, relations `many_to_one`, `many_to_many`, pivot enrichi, HTMX optionnel. Couverture de tests très large (27 fichiers).

**Relations :** `relations.json` déclaratif. Relations `many_to_one`, `many_to_many` (table pivot SQL), `ordered`. JOIN SQL généré. Tests couverts.

**Pages publiques :** 5 générateurs (`make:public-*`). Compatibles i18n et médias. Testés (8 fichiers).

**Points à vérifier dans CONSOLIDATION-STARTER-001 :**

- Starter 3 (Carnet) démontre `many_to_one` + JOIN SQL — vérifier que la doc est à jour.
- Starter 5 (Communes & Séjours) démontre pages publiques + formulaire + mail + médias + i18n.

---

## Front, i18n et templates

**Tailwind CSS** : dépendance frontend unique déclarée dans `package.json`. HTMX et Alpine.js sont injectables optionnellement via `js:init`.

**i18n** : module `core/i18n` léger (3 fichiers). Compatible avec les pages publiques. Testé (3 fichiers).

**Templates** : Jinja2 via `core/templating`. Layouts public/admin dans le profil `standard`. Composants Jinja documentés.

**Points à vérifier dans CONSOLIDATION-FRONT-001 :**

- Comportement de `js:init` sur un profil `minimal` (pas de Tailwind avancé).
- Layouts générés pour chaque profil — `minimal` n'a pas de layout avancé.

---

## Mail, médias, workflow et statistiques

**Mail** : module `core/mail` complet (9 fichiers). SMTP, templates, logs, transports. Testé (7 fichiers).

**Médias / uploads** : module `core/uploads` (8 fichiers). Galeries, images, stockage, validation. Testé (10 fichiers). Refus symlinks et `file://`.

**Workflow** : module `core/workflow` (4 fichiers). Transitions d'état, statuts, helpers Jinja. Testé (3 fichiers). Générique — pas de logique métier.

**Statistiques** : module `core/stats` (5 fichiers). Tracking explicite (`track_event()`), schéma SQL, consultation admin. Testé (4 fichiers).

**Règle vérifiée :** aucun de ces modules n'est automatique ou intrusif. Tout est opt-in.

---

## Modules

**Système de modules** : `core/modules` (6 fichiers). Découverte via `forge_modules.json`, registry, manifests, routes dynamiques.

**Sécurité** : symlinks refusés, `file://` dans les URL refusé. Testé (7 fichiers).

**Limitations connues (hors périmètre CONSOLIDATION-001) :**

- Pas de rollback d'installation.
- Pas de `module:update` ni `module:remove`.
- Pas de `module doctor`.
- Installations partielles non détectées.

Ces limitations sont connues et documentées. Elles relèvent de CONSOLIDATION-MODULES-001.

---

## Starters et profils

**5 starters avec statuts clairs :**

| Starter | Statut | Profil recommandé |
|---------|--------|-------------------|
| 1 — Contacts | Officiel simple | `minimal` / `standard` |
| 2 — Utilisateurs/Auth | Auth minimale moderne (`core.auth`) | `standard` |
| 3 — Carnet de contacts | Officiel relationnel | `standard` |
| 4 — Suivi pédagogique | Historique / legacy | — |
| 5 — Communes & Séjours | Démonstrateur avancé principal | `standard` |

**Incohérence `doc_url` détectée :**

Les starters 2 et 5 pointent encore vers l'ancien format de documentation :

- Starter 2 : `https://caucrogegit.github.io/Forge/starter-app-02-utilisateurs-auth/` ❌
- Starter 5 : `https://caucrogegit.github.io/Forge/starter-app-05-communes-sejours/` ❌

Les starters 1, 3 et 4 ont été mis à jour dans la Phase 9.1. Cette correction reste à faire pour les starters 2 et 5.

**4 profils cohérents :**

| Profil | Contenu | Défaut |
|--------|---------|--------|
| `minimal` | Jinja + Tailwind seuls | — |
| `standard` | Jinja + Tailwind + composants | ✅ |
| `dynamic` | standard + HTMX | — |
| `multilingual` | standard + i18n | — |

`forge_profile.txt` est écrit dans le projet généré. Cohérence avec `docs/profiles.md` confirmée.

---

## Documentation

**Structure :**

- `docs/forge-roadmap.md` : roadmap Forge complète, phases 3 à 10 + post-2.0.
- `docs/forge-design-roadmap.md` : roadmap Forge Design, séparée.
- `docs/profiles.md` : 4 profils documentés.
- `docs/starters/index.md` : index des starters avec statuts, profils, usages recommandés.
- `docs/starters/0N-*/index.md` : documentation de chaque starter.
- `docs/audits/` : 11 documents d'audit spécialisés.

**`docs/roadmap.md` absent** — correct. Seul `docs/forge-roadmap.md` est utilisé.

**Alignement code ↔ doc :**

- Profils dans `forge_cli/project_profiles.py` ↔ `docs/profiles.md` : ✅ alignés.
- Starters dans `forge_cli/starters/data/*/starter.json` ↔ `docs/starters/` : ✅ alignés (sauf `doc_url` starters 2 et 5).
- Commandes CLI ↔ `docs/reference.md` : à vérifier dans CONSOLIDATION-DOC-001.

**Points à vérifier dans CONSOLIDATION-DOC-001 :**

- Vérifier que `docs/reference.md` reflète toutes les commandes Auth.
- Vérifier que `docs/guide.md` couvre les profils et les starters.
- Vérifier que les liens internes MkDocs ne génèrent pas de warnings.

---

## Tests

**161 fichiers de test. 4794 passed, 1 skipped.**

**Distribution par zone :**

| Zone | Fichiers | État |
|------|----------|------|
| Auth | ~28 | ✅ Très bien couverte |
| CRUD | ~27 | ✅ Très bien couverte |
| Entités | ~8 | ✅ Bien couverte |
| Forms | ~10 | ✅ Bien couverte |
| Modules | ~7 | ✅ Bien couverte |
| Mail | ~7 | ✅ Bien couverte |
| Médias / uploads | ~10 | ✅ Bien couverte |
| Pages publiques | ~8 | ✅ Bien couverte |
| Database / migrations | ~6 | ✅ Bien couverte |
| i18n | ~3 | ⚠️ Couverture légère |
| Workflow | ~3 | ⚠️ Couverture légère |
| Stats | ~4 | ✅ Acceptable |
| Frontend / CSS / JS | ~3 | ⚠️ Couverture légère (contrats, pas E2E) |
| Starters | ~8 | ✅ Bien couverte |
| Profils | ~4 | ✅ Bien couverte |

**Points à approfondir dans CONSOLIDATION-TESTS-001 :**

- i18n : 3 fichiers de tests, complexité des traductions peu testée.
- Workflow : transitions d'état en contexte d'intégration.
- Frontend : tests de contrats CSS/JS (présence des fichiers), pas de tests E2E.
- Scénarios MFA + OIDC en conditions réelles (base de données, callbacks).

---

## Packaging et dépendances

**6 dépendances Python runtime :**

| Dépendance | Usage |
|-----------|-------|
| `mariadb==1.1.14` | Base de données |
| `python-dotenv==1.2.2` | Configuration `.env` |
| `jinja2==3.1.6` | Templating HTML |
| `Pillow>=10.0,<13` | Traitement images |
| `argon2-cffi>=25.1,<26` | Hachage mots de passe (argon2id) |
| `pyotp>=2.9,<3` | TOTP pour MFA |

**Cohérence `pyproject.toml` / `requirements.txt` :** identique. ✅

**Dépendances frontend :**

- `tailwindcss` + `@tailwindcss/cli` (développement uniquement, pas runtime).

**Règle vérifiée :** Forge ne dépend pas de frameworks Python tiers (Flask, Django, FastAPI, SQLAlchemy). Le core est autonome.

---

## Risques détectés

| Risque | Sévérité | Zone |
|--------|----------|------|
| `core/auth/oidc.py` — 1011 lignes | ⚠️ MOYEN | Lisibilité future si logique OIDC s'étend |
| `doc_url` starters 2 et 5 — ancien format | ⚠️ FAIBLE | Incohérence doc uniquement |
| Couverture i18n légère | ⚠️ FAIBLE | Tests à approfondir |
| Modules : pas de rollback ni de `module:remove` | ℹ️ CONNU | Limitations documentées, non critiques |
| Starter 4 utilise `core.security.hashing` legacy | ✅ ACCEPTABLE | Starter marqué legacy, pas prévu pour modernisation |

**Risques critiques identifiés : aucun.**

---

## Points cohérents

1. **Séparation des responsabilités** : core, CLI, générateurs, starters et documentation ont des rôles distincts et respectés.
2. **core.auth / core.security** : coexistence claire et justifiée. Migration moderne réalisée (starter 2).
3. **Profils** : 4 profils cohérents, `standard` comme défaut, écrit dans `forge_profile.txt`.
4. **Starters** : 5 starters avec statuts clairs, documentation alignée, index consolidé.
5. **Tests** : 161 fichiers, 4794 tests passés — couverture fonctionnelle très complète.
6. **Packaging** : 6 dépendances Python justifiées, aucun framework tiers, frontend minimal.
7. **Documentation séparée** : Forge ↔ Forge Design, deux roadmaps indépendantes.
8. **Aucune logique métier dans le core** : Communes & Séjours reste un starter, pas du code core.

---

## Points à corriger

Ces corrections sont identifiées mais **ne relèvent pas de CONSOLIDATION-001**. Elles doivent être adressées dans les tickets suivants.

| Point | Ticket recommandé |
|-------|------------------|
| `doc_url` starters 2 et 5 — corriger le format | CONSOLIDATION-STARTER-001 |
| Vérifier `docs/reference.md` vs commandes Auth actuelles | CONSOLIDATION-DOC-001 |
| Audit couverture i18n et workflow | CONSOLIDATION-TESTS-001 |
| Vérifier messages `--help` cohérents sur 31+ commandes | CONSOLIDATION-CLI-001 |
| Modules : documenter limites rollback / remove / update | CONSOLIDATION-MODULES-001 |

---

## Recommandations pour les tickets suivants

**Séquence recommandée (aucune priorité urgente non standard détectée) :**

### 1. CONSOLIDATION-CLI-001 — Audit cohérence CLI

Vérifier :
- Messages `--help` sur toutes les commandes.
- Cohérence `auth:user:*` (sous-commandes imbriquées).
- Commandes `deploy:*` — stabilité et documentation.
- Comportement en cas d'argument manquant ou invalide.

### 2. CONSOLIDATION-DOC-001 — Audit documentation / roadmap / README

Vérifier :
- `docs/reference.md` couvre les commandes Auth ajoutées post-1.5.0.
- `docs/guide.md` couvre profils et starters.
- `README.md` est à jour pour une première impression correcte.
- Liens internes MkDocs sans warnings.
- `doc_url` starters 2 et 5 : corriger dans ce ticket ou dans CONSOLIDATION-STARTER-001.

### 3. CONSOLIDATION-TESTS-001 — Audit couverture et zones fragiles

Vérifier :
- i18n : ajouter tests sur pluralisation, fallback, chargement.
- Workflow : ajouter tests de transitions invalides.
- Scénarios MFA / OIDC en intégration.
- Modules : tester installations partielles (si faisable sans risque).

### 4. CONSOLIDATION-NON-OVERWRITE-001 — Vérifier la préservation du code utilisateur

Vérifier que les générateurs (`make:entity`, `make:crud`, `make:public-*`) ne surprennent pas les fichiers existants.

### 5. CONSOLIDATION-MODULES-001 — Vérifier le cycle complet des modules

Vérifier et documenter les limites : rollback, `module:remove`, `module:update`, installations partielles.

### 6. CONSOLIDATION-PROFILES-001 — Vérifier la cohérence des profils

Vérifier les fichiers générés pour chaque profil. `multilingual` n'impose pas `dynamic`.

### 7. CONSOLIDATION-FRONT-001 — Vérifier Tailwind / HTMX / Alpine / templates

Vérifier les layouts générés par profil. Comportement `js:init` sur `minimal`.

### 8. CONSOLIDATION-STARTER-001 — Vérifier que Communes & Séjours démontre Forge sans polluer le core

Vérifier :
- `doc_url` starters 2 et 5.
- Starter 5 démontre bien pages publiques + mail + médias + i18n.
- Starter 4 marqué legacy dans `starter.json` (vérifier le champ `status`).

### 9. CONSOLIDATION-ROADMAP-001 — Décider ce qui relève de Forge 2.0, Forge Design ou post-roadmap

Nettoyer la roadmap, identifier les tickets post-2.0 qui pourraient remonter.

---

*Audit réalisé le 2026-05-08. Forge post-1.5.0. 4794 tests passés, 1 skipped.*
