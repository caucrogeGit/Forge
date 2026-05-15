# Audit CONSOLIDATION-ROADMAP-001 — Décision Forge 2.0, Forge Design et post-roadmap

**Date :** 2026-05-09
**Périmètre :** trajectoire Forge 2.0, périmètre core, frontières Forge Design, limites assumées
**Ticket :** CONSOLIDATION-ROADMAP-001

---

## Objectif

Clore la Phase 9.5 de consolidation en décidant clairement ce qui fait partie de Forge 2.0, ce qui est repoussé, ce qui appartient à Forge Design, et ce qui reste interdit au cœur Forge.

Ce ticket ne publie pas Forge 2.0.

---

## Synthèse

| Domaine | Décision | Commentaire |
|---|---|---|
| Core MVC | Forge 2.0 | BaseController, BaseModel, BaseForm, BaseEntity, routeur, sessions |
| CLI | Forge 2.0 | 59 commandes, convention namespace:action, `forge.py` unifié |
| Entités JSON | Forge 2.0 | Modèle canonique JSON, validations, relations déclaratives |
| SQL généré | Forge 2.0 | `forge build:model`, migrations versionnées, `forge db:apply` |
| CRUD | Forge 2.0 | Génération complète contrôleur/modèle/form/vues |
| Formulaires | Forge 2.0 | BaseForm, validation, CSRF |
| Médias | Forge 2.0 | Upload, variantes, galerie, stockage local |
| Mail | Forge 2.0 | Mailer, FakeTransport, MailTemplateRenderer |
| RBAC | Forge 2.0 | Rôles, permissions, `@require_permission` |
| Auth/User | Forge 2.0 | Sessions, hash Argon2, MFA TOTP, codes récupération, email verification, reset password, OIDC (AUTH-OIDC-001-003 terminés), admin CLI (AUTH-ADMIN-001-003 terminés) |
| Tailwind CSS | Forge 2.0 | v4.2.2 officiel, `forge js:init`, `build:css` |
| HTMX | Forge 2.0 avec limites | Optionnel, `forge js:init htmx`, CRUD progressif |
| Alpine.js | Forge 2.0 avec limites | Optionnel, `forge js:init alpine` |
| i18n | Forge 2.0 | `trans()`, JSON catalogues, `i18n:check`, préfixes protégés |
| Pages publiques | Forge 2.0 | `make:public-page/list/show/form/contact` |
| Modules | Forge 2.0 avec limites | Cycle en 4 étapes, sécurité validée, pas de `module:remove` ni rollback |
| Profils | Forge 2.0 avec limites | 4 profils déclarés, squelettes encore peu différenciés |
| Starters | Forge 2.0 | 5 starters documentés, statuts clairs, rebuild.md pour tous |
| Communes & Séjours | Démonstrateur Forge 2.0 | Démonstrateur avancé, pas de logique métier dans core |
| Forge Design | Projet séparé | Roadmap séparée, aucun couplage obligatoire |
| OIDC / OAuth | Forge 2.0 (livré) | AUTH-OIDC-001-003 terminés en Phase 4.5 — erreur corrigée dans PUBLICATION-2.0-PREP-001 |
| Admin utilisateurs | Forge 2.0 (livré) | AUTH-ADMIN-001-003 terminés en Phase 4.5 — erreur corrigée dans PUBLICATION-2.0-PREP-001 |
| API JSON légère | Post-2.0 | Tickets API-JSON-001 à 005 planifiés |
| Marketplace modules | Post-2.0 ou exclu | Hors périmètre Forge 2.0 |
| module:remove / rollback | Post-2.0 | Non critique pour 2.0 |
| Profils différenciés | Post-2.0 | Ticket PROFILE-DIFFERENTIATION-001 proposé |
| Tests E2E MariaDB réels | Post-2.0 | Tickets E2E-MARIADB-001, E2E-CLI-001 planifiés |
| Paiement | Exclu | Hors cœur Forge, hors Forge Design |
| Réservation avancée | Exclue | Hors cœur, réside dans les starters uniquement |
| SaaS multi-tenant | Exclu | Hors cœur Forge |
| SPA React/Vue/Svelte | Exclue | Hors cœur, philosophie anti-SPA documentée |
| ORM complet | Exclu | Hors cœur, SQL explicite par choix |
| WebAuthn / passkeys | Exclu post-2.0 | Ticket envisageable après 2.0 |

---

## Audits de consolidation pris en compte

| Ticket | Résultat | Document |
|---|---|---|
| CONSOLIDATION-001 | Architecture cohérente, aucune dette critique | `consolidation-001-architecture.md` |
| CONSOLIDATION-CLI-001 | CLI cohérente, 59 commandes, 4 incohérences mineures | `consolidation-cli-001.md` |
| CONSOLIDATION-DOC-001 | Documentation publiable, navigation propre | `consolidation-doc-001.md` |
| CONSOLIDATION-TESTS-001 | Suite robuste, 5044 tests | `consolidation-tests-001.md` |
| CONSOLIDATION-NON-OVERWRITE-001 | Préservation code utilisateur validée | `consolidation-non-overwrite-001.md` |
| CONSOLIDATION-MODULES-001 | Modules fiables, sécurité validée | `consolidation-modules-001.md` |
| CONSOLIDATION-PROFILES-001 | Profils stables, séparation Forge Design garantie | `consolidation-profiles-001.md` |
| CONSOLIDATION-FRONT-001 | Socle front cohérent, philosophie anti-SPA | `consolidation-front-001.md` |
| CONSOLIDATION-STARTER-001 | Starters cohérents, doc_url corrigés, rebuild.md complets | `consolidation-starter-001.md` |

---

## État final de la Phase 9.5

La Phase 9.5 a vérifié 9 domaines distincts :

1. **Architecture** : core MVC en 3 couches propres, aucune logique métier dans le cœur.
2. **CLI** : 59 commandes, convention `namespace:action` uniforme, dispatch propre dans `forge.py`.
3. **Documentation** : MkDocs strict, navigation cohérente, starters documentés avec rebuild.md.
4. **Tests** : 5044 tests passés, 1 skipped. Couverture Auth/CRUD/modules/starters/profils.
5. **Non-écrasement** : 3 mécanismes distincts, scénario d'intégration validé.
6. **Modules** : cycle en 4 étapes, sécurité renforcée, conflits atomiques détectés.
7. **Profils** : 4 profils officiels, `forge_profile.txt`, séparation Forge Design.
8. **Front** : Tailwind v4, HTMX/Alpine optionnels, CRUD progressif, i18n natif.
9. **Starters** : 5 starters, doc_url cohérents, Communes & Séjours démonstrateur sans pollution core.

**Aucune incohérence bloquante n'a été identifiée.** Les incohérences mineures détectées ont toutes été corrigées ou documentées avec un ticket futur proposé.

---

## Décision sur Forge 2.0

**Forge est prêt à entrer en Phase 10 — Publication Forge 2.0.**

**Décision : OUI avec limites assumées.**

Les conditions de sortie de la Phase 9.5 sont remplies :

- CLI cohérente ✅
- Documentation alignée avec le code ✅
- Roadmap nettoyée ✅
- Profils de projet stables ✅
- Système de modules stabilisé ✅
- Starter démonstrateur fonctionnel ✅
- Aucune confusion entre framework et application métier ✅
- Tests complets verts ✅
- Stratégie claire pour Forge 2.0 ✅

---

## Contenu retenu pour Forge 2.0

### Core MVC

- `core/mvc/` : `BaseController`, routeur, sessions CSRF, `BaseModel`, `BaseForm`
- `core/entities/` : `BaseEntity`, JSON canonique, validations
- `core/migrations/` : `MigrationManager`, SQL versionné, `db:apply`
- `core/rbac/` : rôles, permissions, décorateurs
- `core/auth/` : sessions, `argon2`, `@login_required`, MFA TOTP, email verification, reset password, codes récupération
- `core/mail/` : `Mailer`, `FakeTransport`, `MailTemplateRenderer`
- `core/media/` : upload, variantes, galerie, `MediaField`
- `core/i18n/` : `trans()`, catalogues JSON, `i18n:check`
- `core/modules/` : découverte, installation, fichiers, routes — cycle en 4 étapes
- `integrations/` : Jinja2, MariaDB, SQLite

### CLI (`forge_cli/`)

- `forge new` avec `--profile`
- `make:entity`, `sync:entity`, `build:model`, `check:model`
- `make:crud`, `make:form`, `make:public-*`
- `db:init`, `db:apply`, `db:migrate`, `db:rollback`, `db:status`
- `routes:list`, `doctor`
- `starter:list`, `starter:build`
- `module:list`, `module:install`, `module:files`, `module:routes`
- `js:init htmx/alpine/htmx-alpine`
- `i18n:check`
- `upload:init` / `media:init`
- `rbac:*`, `mail:*`, `migration:*`, `build:css`

### Front

- Tailwind CSS v4.2.2 (officiel, `npm run build:css`)
- HTMX et Alpine.js (optionnels via `forge js:init`)
- Layouts Jinja2 : `base.html`, `admin.html`, `public.html`
- `{% block scripts %}` pour chargement explicite
- 6 composants + 4 partials

### Starters

- 1 — Contacts (officiel simple)
- 2 — Utilisateurs/Auth (Auth moderne `core.auth`)
- 3 — Carnet de contacts (officiel relationnel)
- 4 — Suivi pédagogique (legacy conservé)
- 5 — Communes & Séjours (démonstrateur avancé)

### Documentation

- MkDocs avec Material, `mkdocs build --strict` vert
- Guide, référence, installation, déploiement, profils, front, starters

### Tests

- 5044 tests passés, 1 skipped
- Couverture : core, CLI, entités, CRUD, Auth/RBAC, modules, profils, starters, front, i18n, médias

---

## Limites assumées de Forge 2.0

Ces limites ne bloquent pas la publication. Elles sont documentées et cohérentes avec la philosophie Forge.

| Limite | Raison | Ticket futur |
|---|---|---|
| Profils peu différenciés (même squelette) | Décision volontaire, ticket proposé | `PROFILE-DIFFERENTIATION-001` |
| `module:remove` absent | Hors périmètre 2.0, complexité rollback | Post-2.0 |
| `module:routes` sans rollback atomique | Risque faible, documenté | Post-2.0 |
| `js:init` absent de `reference.md` | Documenté dans `front.md` | `CONSOLIDATION-DOC-FRONT-001` |
| `docs/modules.md` absent | Documenté dans l'audit modules | `CONSOLIDATION-DOC-MODULES-001` |
| Tests E2E réels MariaDB à renforcer | Hors perimètre pytest pur | `E2E-MARIADB-001` |
| Styles d'aide CLI hétérogènes | Incohérence mineure, non bloquante | `DX-HELP-001` |
| Suivi pédagogique auth pré-`core.auth` | Clairement legacy, documenté | — |

**Note :** OIDC (AUTH-OIDC-001-003) et administration utilisateurs (AUTH-ADMIN-001-003) sont livrés en Phase 4.5 — leur mention initiale comme « non livrés » était une erreur, corrigée dans PUBLICATION-2.0-PREP-001.

---

## Éléments repoussés post-2.0

### Expérience développeur

| Ticket | Objectif |
|---|---|
| DX-DOCTOR-001 | Étendre `forge doctor` aux modules, templates, i18n |
| DX-PROJECT-CHECK-001 | Ajouter `forge project:check` |
| DX-ERRORS-001 | Standardiser les messages d'erreur CLI |
| DX-HELP-001 | Harmoniser les aides |

### Sécurité

| Ticket | Objectif |
|---|---|
| SECURITY-AUDIT-001 | Audit sécurité complet |
| SECURITY-HEADERS-001 | Headers HTTP de sécurité |
| SECURITY-UPLOADS-AUDIT-001 | Réaudit uploads/médias |
| SECURITY-RBAC-AUDIT-001 | Cohérence RBAC/routes/templates |

### Tests d'intégration

| Ticket | Objectif |
|---|---|
| E2E-CLI-001 | Cycle complet `forge new` → entité → migration → CRUD |
| E2E-MARIADB-001 | Migrations sur MariaDB réelle |
| E2E-STARTER-001 | Génération et exécution starters |
| E2E-MODULE-001 | Installation module dans projet généré |

### Release et compatibilité

| Ticket | Objectif |
|---|---|
| RELEASE-POLICY-001 | Politique de versionnement |
| RELEASE-COMPAT-001 | Compatibilité Python/MariaDB/Node |
| RELEASE-MIGRATION-GUIDE-001 | Guide de migration |

### Documentation avancée

| Ticket | Objectif |
|---|---|
| DOC-15MIN-001 | Tutoriel "15 minutes avec Forge" |
| DOC-APP-COMPLETE-001 | Tutoriel application complète |
| DOC-MODULE-AUTHOR-001 | Guide créer un module |
| CONSOLIDATION-DOC-FRONT-001 | Ajouter `js:init` dans `docs/reference.md` |
| CONSOLIDATION-DOC-MODULES-001 | Créer `docs/modules.md` |

### Fonctionnalités futures

| Ticket | Objectif |
|---|---|
| PROFILE-DIFFERENTIATION-001 | Squelettes réellement différenciés par profil |
| API-JSON-001 | Réponses JSON simples |
| AUTH-OIDC-ADVANCED-001 | Améliorations OIDC multi-provider avancé (OIDC de base livré) |
| AUTH-ADMIN-ADVANCED-001 | Interface admin web utilisateurs (CLI admin livré) |

---

## Éléments relevant de Forge Design

Forge Design est un projet compagnon séparé. Sa roadmap propre est dans `docs/forge-design-roadmap.md`.

| Élément | Statut |
|---|---|
| Éditeur graphique de templates | Forge Design exclusivement |
| Modèle JSON d'interface visuelle | Forge Design exclusivement |
| Preview visuelle en temps réel | Forge Design exclusivement |
| Export de templates Forge | Forge Design exclusivement |
| Interface de composition front | Forge Design exclusivement |
| Thèmes et bibliothèques de composants | Forge Design exclusivement |

**Règles inviolables :**

- Forge Design ne doit jamais devenir une dépendance obligatoire de Forge.
- Le cœur Forge doit fonctionner sans Forge Design.
- Forge Design doit produire du code Forge lisible, pas un binaire opaque.
- Forge Design ne doit pas transformer Forge en éditeur React/Vue.

---

## Éléments explicitement exclus du cœur Forge

Ces éléments ne feront jamais partie du cœur Forge, quelle que soit la version.

| Élément | Raison |
|---|---|
| ORM complet | Philosophie SQL explicite |
| SaaS multi-tenant | Logique applicative, hors framework |
| Paiement intégré | Logique métier, risque sécurité, hors framework |
| Réservation avancée | Logique métier, hors framework |
| Marketplace plugins | Complexité gouvernance, hors périmètre |
| SPA React/Vue/Svelte | Philosophie HTML serveur d'abord |
| WebAuthn / passkeys | Envisageable post-2.0 uniquement |
| SAML / SSO entreprise | Hors cible, complexité élevée |
| Moteur SaaS | Hors cœur, hors philosophie |
| Traduction automatique | Hors cœur |
| Déploiement spécifique intégré | Hors framework |

---

## Statut de Communes & Séjours

**Communes & Séjours est et reste le démonstrateur avancé de Forge 2.0.**

Il démontre :
- entités et relations ;
- pages publiques ;
- formulaire avec validation serveur ;
- notifications mail ;
- i18n via `trans()` ;
- seed JSON ;
- Tailwind sans JavaScript obligatoire.

Il ne fournit pas et ne fournira pas :
- réservation confirmée ;
- paiement ;
- calendrier de disponibilités ;
- espace propriétaire complet ;
- back-office métier ;
- synchronisation Airbnb/Booking ;
- moteur SaaS.

**Aucune logique Communes & Séjours n'est présente dans `core/`.** La vérification a été effectuée dans CONSOLIDATION-STARTER-001.

---

## Risques restants

| Risque | Niveau | Traitement |
|---|---|---|
| `module:routes` sans rollback | Faible | Documenté, ticket post-2.0 |
| Profils peu différenciés | Faible | Documenté `PROFILE-DIFFERENTIATION-001` |
| Suivi pédagogique auth antérieure | Faible | Clairement legacy dans la doc |
| Tests E2E réels absents | Modéré | Fonctionnel en unit tests, E2E post-2.0 |
| `js:init` absent de `reference.md` | Mineur | `CONSOLIDATION-DOC-FRONT-001` |
| `docs/modules.md` absent | Mineur | `CONSOLIDATION-DOC-MODULES-001` |

**Aucun risque bloquant pour la Phase 10.**

---

## Recommandations

1. **Lancer PUBLICATION-2.0-PREP-001** : préparer la publication sans modifier le code.
2. **Choisir le tag** : `v2.0.0` ou `v2.0.0-rc.1` selon la décision finale.
3. **Corriger les deux lacunes documentaires mineures** avant publication :
   - `CONSOLIDATION-DOC-FRONT-001` : ajouter `js:init` dans `reference.md`.
   - `CONSOLIDATION-DOC-MODULES-001` : créer `docs/modules.md`.
4. **Ne pas ajouter de fonctionnalité** entre Phase 9.5 et Phase 10.

---

## Prochaine phase

**Phase 10 — Publication Forge 2.0**

Prochaine priorité : `PUBLICATION-2.0-PREP-001`

Objectif : préparer la publication sans modifier le cœur — README final, version cohérente, tag, instructions d'installation propres.

---

## Verdict final

**La Phase 9.5 est terminée. Forge est prêt à entrer en Phase 10.**

9 audits de consolidation réalisés, 0 incohérence bloquante détectée. Le cœur Forge est cohérent, la CLI est exploitable, la documentation est publiable, les tests sont verts, les starters sont documentés, et Communes & Séjours démontre Forge sans polluer le core.

**Forge 2.0 est publiable avec les limites assumées ci-dessus.**

**Résultat :** CONSOLIDATION-ROADMAP-001 — **VALIDÉ. Phase 9.5 close.**
