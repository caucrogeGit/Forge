# Audit STARTER-LEGACY-AUDIT-001 — Starters historiques Forge

## Objectif

Auditer les starters historiques Forge 1 à 4 afin de qualifier leur état réel, leur cohérence avec Forge actuel et les profils officiels, et de préparer les décisions du ticket `STARTER-LEGACY-DECISION-001`.

Ce document ne modifie aucun starter. Il observe et recommande.

---

## Synthèse

| # | Nom | Slug | Kind | État | Profil associé | Recommandation |
|---|---|---|---|---|---|---|
| 1 | Contacts | `contact-simple` | `crud` | fonctionnel | `minimal` / `standard` | conserver officiel |
| 2 | Utilisateurs / Auth | `utilisateurs-auth` | `application` | fonctionnel, décalé | `standard` | aligner ou documenter legacy |
| 3 | Carnet de contacts | `carnet-contacts` | `application` | fonctionnel | `standard` | conserver officiel |
| 4 | Suivi pédagogique | `suivi-comportement-eleves` | `application` | fonctionnel, complexe | aucun / legacy | documenter comme démonstrateur historique |

---

## Starter 1 — Contacts (`contact-simple`)

### Identification

- **Numéro** : 1
- **Nom** : Contacts
- **Slug** : `contact-simple`
- **Aliases** : `contacts`, `1`
- **Kind** : `crud` (implicite — pas de champ `kind` dans `starter.json`)
- **requires_db** : oui
- **Fichiers principaux** : `starter.json`, `contact.json` (entity JSON uniquement, pas de dossier `files/`)
- **Page de documentation** : `docs/starter-app-01-contacts.md`
- **Tests associés** : `tests/test_starter_cli.py`
- **Rebuild docs** : `docs/starters/01-contact-simple/README.md`, `docs/starters/01-contact-simple/rebuild.md`

### État technique

- Listé par `forge starter:list` : ✅
- Générable par `forge starter:build 1` : ✅
- Supporte `--dry-run` : ✅
- Supporte `--force` : ✅
- Mécanisme : génère une entité via `make_entity`, injecte le JSON `contact.json`, lance `make_crud`, câble les routes dans `mvc/routes.py` via `routes_marker`
- Dépendance DB : oui
- Dossier `files/` : **absent** — tout est généré à la volée (make_entity + make_crud)
- Routes déclarées : oui, en JSON dans `starter.json` (7 routes CRUD standard)
- Données packagées : entité seule (`contact.json`)
- Règles de non-écrasement : respectées par le mécanisme CRUD

### Cohérence avec Forge actuel

| Composant | Présent | Commentaire |
|---|---|---|
| Tailwind | — | généré par le squelette Forge, pas le starter |
| Pages publiques | non | routes admin uniquement |
| i18n | non | aucune clé `trans()` |
| HTMX | non | — |
| Relations | non | entité unique |
| CRUD | ✅ | c'est son objectif |
| Médias | non | — |
| Auth/User | non | — |
| RBAC | non | — |
| Modules | non | — |
| Profils de projet | non concerné | généré dans un projet existant |

### Cohérence avec les profils Forge

Profil recommandé : **`minimal`** (démonstrateur pédagogique) ou **`standard`** (projet classique avec CRUD).

C'est le starter le plus simple : une entité, un CRUD, des routes. Correspond à l'objectif du profil `minimal` ou à un usage `standard` basique.

### Cohérence documentaire

- Page `starter-app-01-contacts.md` : ✅ existe, décrit fidèlement l'état réel
- Rebuild docs : ✅ présent
- Pas de mention de `docs/roadmap.md` : ✅
- Pas de confusion avec les profils Forge : ✅

### Risques

- **Dette technique** : faible. Mécanisme simple et stable.
- **Documentation** : à jour.
- **Dépendance fragile** : aucune.
- **Conflit profils** : aucun.
- **Conflit Communes & Séjours** : aucun.
- **Risque utilisateur** : nul — c'est le point d'entrée idéal.
- **Risque maintenance** : faible.

---

## Starter 2 — Utilisateurs / Auth (`utilisateurs-auth`)

### Identification

- **Numéro** : 2
- **Nom** : Utilisateurs / authentification
- **Slug** : `utilisateurs-auth`
- **Aliases** : `utilisateurs-auth`, `utilisateurs`, `auth`, `2`
- **Kind** : `application`
- **requires_db** : oui
- **Fichiers principaux** : `starter.json`, `entities/utilisateur.json`, `files/mvc/controllers/auth_controller.py`, `files/mvc/controllers/dashboard_controller.py`, `files/mvc/models/auth_model.py`, vues, scripts
- **Page de documentation** : `docs/starter-app-02-utilisateurs-auth.md`
- **Tests associés** : `tests/test_starter_cli.py`
- **Rebuild docs** : `docs/starters/02-utilisateurs-auth/README.md`, `docs/starters/02-utilisateurs-auth/rebuild.md`

### État technique

- Listé par `forge starter:list` : ✅
- Générable par `forge starter:build 2` : ✅
- Supporte `--dry-run` : ✅
- Supporte `--force` : ✅
- Mécanisme : copie les fichiers du dossier `files/`, injecte l'entité `utilisateur`, câble les routes via `routes.py.snippet`
- Dépendance DB : oui
- Dossier `files/` : présent (controllers, models, vues, scripts)
- Routes : snippet (pas de routes JSON)
- Données packagées : entité `utilisateur.json`
- Script fourni : `create_auth_user.py`
- CSRF manuel dans les controllers

### Cohérence avec Forge actuel

| Composant | Présent | Commentaire |
|---|---|---|
| Tailwind | — | squelette Forge |
| Pages publiques | non | `/login` est public mais déclaré manuellement |
| i18n | non | aucune clé `trans()` |
| HTMX | non | — |
| Relations | non | entité unique |
| CRUD | non | formulaire auth custom |
| Médias | non | — |
| Auth/User (Phase 4.5) | ⚠️ **décalé** | utilise `core.security.hashing` / `core.security.session` au lieu de `core.auth` |
| RBAC | non | — |
| Modules | non | — |
| Profils de projet | non concerné | — |

**Point critique** : le starter 2 implémente son propre `auth_model.py` avec une table `utilisateur` (champ `Login`, `PasswordHash`, `Actif`) et utilise `core.security.hashing`, `core.security.session`. La Phase 4.5 a livré `core.auth` avec une table `users` standardisée et les helpers `current_user()`, `is_authenticated()`, `@login_required`. Ces deux approches coexistent mais sont incompatibles.

### Cohérence avec les profils Forge

Profil recommandé : **`standard`** (application avec auth).

Mais son implémentation auth est en décalage avec les briques Auth/User officielles (Phase 4.5). Le starter démontre un mécanisme valide historiquement, mais l'utilisateur qui le suit ne bénéficiera pas des helpers Auth/User récents.

### Cohérence documentaire

- Page `starter-app-02-utilisateurs-auth.md` : ✅ existe
- Le mot "profil" apparaît dans la doc — c'est un profil **utilisateur** (page profil de l'application), pas un profil Forge. Pas de confusion réelle, mais vocabulaire ambigu.
- Rebuild docs : ✅ présent
- Pas de mention de `docs/roadmap.md` : ✅

### Risques

- **Dette technique** : élevée. L'auth custom du starter est dépassée par Phase 4.5.
- **Documentation** : techniquement exacte mais ne guide pas vers `core.auth`.
- **Dépendance fragile** : `core.security.hashing` — toujours présent mais doubloné par `core.auth`.
- **Conflit avec Auth/User Phase 4.5** : le starter 2 et la Phase 4.5 enseignent deux façons différentes de faire de l'auth. Risque de confusion majeur pour un nouvel utilisateur.
- **Conflit Communes & Séjours** : aucun direct.
- **Risque utilisateur** : moyen — l'utilisateur peut ne pas savoir qu'il existe une auth standardisée plus récente.
- **Risque maintenance** : élevé si `core.security` évolue sans que le starter soit mis à jour.

---

## Starter 3 — Carnet de contacts (`carnet-contacts`)

### Identification

- **Numéro** : 3
- **Nom** : Carnet de contacts
- **Slug** : `carnet-contacts`
- **Aliases** : `3`, `carnet`, `carnet-contacts`
- **Kind** : `application`
- **requires_db** : oui
- **Fichiers principaux** : `starter.json`, `entities/ville.json`, `entities/contact.json`, `relations.json`, `files/mvc/` (controllers, models, forms, views), `files/scripts/seed_villes.py`
- **Page de documentation** : `docs/starter-app-03-carnet-contacts.md`
- **Tests associés** : `tests/test_starter_cli.py`
- **Rebuild docs** : `docs/starters/03-carnet-contacts/README.md`, `docs/starters/03-carnet-contacts/rebuild.md`

### État technique

- Listé par `forge starter:list` : ✅
- Générable par `forge starter:build 3` : ✅
- Supporte `--dry-run` : ✅
- Supporte `--force` : ✅
- Mécanisme : copie `files/`, injecte les entités Ville + Contact, injecte `relations.json`, câble les routes via `routes.py.snippet`
- Dépendance DB : oui
- Dossier `files/` : présent (controllers, models, forms, vues, scripts)
- Routes : snippet
- Données packagées : 2 entités + `relations.json`
- Script fourni : `seed_villes.py`
- Formulaire contact : formulaire avec sélection de ville (relation many_to_one)

### Cohérence avec Forge actuel

| Composant | Présent | Commentaire |
|---|---|---|
| Tailwind | — | squelette Forge |
| Pages publiques | non | routes admin |
| i18n | non | aucune clé `trans()` |
| HTMX | non | — |
| Relations | ✅ | `many_to_one` Ville → Contact via `relations.json` |
| CRUD | ✅ | deux entités avec CRUD |
| Médias | non | — |
| Auth/User | non | — |
| RBAC | non | — |
| Modules | non | — |
| Profils de projet | non concerné | — |

### Cohérence avec les profils Forge

Profil recommandé : **`standard`** (application multi-entités avec relations SQL simples).

C'est le bon niveau de complexité pour un `standard` : deux entités, une relation, pas d'auth, pas de front dynamique.

### Cohérence documentaire

- Page `starter-app-03-carnet-contacts.md` : ✅ existe, décrit fidèlement
- Rebuild docs : ✅ présent
- Pas de mention de `docs/roadmap.md` : ✅
- Pas de confusion avec les profils Forge : ✅

### Risques

- **Dette technique** : faible.
- **Documentation** : à jour.
- **Dépendance fragile** : vérifier que `relations.json` respecte la syntaxe actuelle de Forge (format `many_to_one` stable en Forge 1.5).
- **Conflit profils** : aucun.
- **Conflit Communes & Séjours** : aucun direct.
- **Risque utilisateur** : nul.
- **Risque maintenance** : faible.

---

## Starter 4 — Suivi pédagogique (`suivi-comportement-eleves`)

### Identification

- **Numéro** : 4
- **Nom** : Suivi pédagogique
- **Slug** : `suivi-comportement-eleves`
- **Aliases** : `4`, `suivi`, `suivi-comportement-eleves`
- **Kind** : `application`
- **requires_db** : oui
- **Fichiers principaux** : `starter.json`, 4 entités JSON, `relations.json`, `files/mvc/` (5 controllers, 4 models, vues), `files/scripts/` (create_auth_user.py, seed_suivi.py)
- **Page de documentation** : `docs/starter-app-04-suivi-comportement-eleves.md`
- **Tests associés** : `tests/test_starter_cli.py`
- **Rebuild docs** : `docs/starters/04-suivi-comportement-eleves/README.md`, `docs/starters/04-suivi-comportement-eleves/rebuild.md`

### État technique

- Listé par `forge starter:list` : ✅
- Générable par `forge starter:build 4` : ✅
- Supporte `--dry-run` : ✅
- Supporte `--force` : ✅
- Mécanisme : copie `files/`, injecte 4 entités, `relations.json`, câble les routes via `routes.py.snippet`
- Dépendance DB : oui
- Dossier `files/` : présent (nombreux fichiers — plus complexe que les autres starters)
- Routes : snippet
- Données packagées : 4 entités + `relations.json`
- Scripts : `create_auth_user.py` + `seed_suivi.py`
- Auth : même pattern que starter 2 — `core.security.hashing` / `core.security.session`

### Cohérence avec Forge actuel

| Composant | Présent | Commentaire |
|---|---|---|
| Tailwind | — | squelette Forge |
| Pages publiques | non | routes admin + auth |
| i18n | non | aucune clé `trans()` |
| HTMX | non | — |
| Relations | ✅ | plusieurs relations déclarées en `relations.json` |
| CRUD | ✅ | élèves, cours, observations |
| Médias | non | — |
| Auth/User (Phase 4.5) | ⚠️ **décalé** | même problème que starter 2 |
| RBAC | non | — |
| Modules | non | — |
| Profils de projet | non concerné | — |

**Point critique identique au starter 2** : auth custom via `core.security`, décalée de Phase 4.5 (`core.auth`).

### Cohérence avec les profils Forge

Profil recommandé : **aucun profil simple — démonstrateur historique**.

C'est une mini-application métier spécialisée (suivi d'élèves). Sa richesse (auth, plusieurs entités, relations, dashboard, seed) en fait un bon démonstrateur "Forge complet" mais elle est trop métier pour servir de base générique. Ne correspond pas à `minimal`, `standard`, `dynamic` ni `multilingual`.

### Cohérence documentaire

- Page `starter-app-04-suivi-comportement-eleves.md` : ✅ existe, décrit fidèlement
- Se présente comme "vitrine Forge complète" — formulation juste.
- Rebuild docs : ✅ présent
- Pas de mention de `docs/roadmap.md` : ✅

### Risques

- **Dette technique** : élevée. Auth décalée de Phase 4.5, comme starter 2.
- **Documentation** : exacte mais ne signale pas que l'auth utilisée est différente de l'auth standardisée.
- **Dépendance fragile** : `core.security.hashing` — stable pour l'instant.
- **Conflit avec Auth/User Phase 4.5** : le plus risqué des deux starters auth, car la complexité masque mieux le décalage.
- **Conflit Communes & Séjours** : les deux sont des "démonstrateurs complets". Positionnement à clarifier.
- **Risque utilisateur** : élevé — un débutant peut confondre le pattern auth de ce starter avec la bonne pratique actuelle.
- **Risque maintenance** : élevé.

---

## Comparaison avec Communes & Séjours (starter 5)

| Critère | Starter 4 — Suivi | Starter 5 — Communes & Séjours |
|---|---|---|
| Kind | `application` | `skeleton` |
| Auth | custom (`core.security`) | non (pages publiques) |
| i18n | non | ✅ |
| Médias | non | ✅ |
| Pages publiques | non | ✅ |
| Formulaire public | non | ✅ |
| Mails | non | ✅ |
| Seed | SQL script | JSON |
| Documentation | complète | complète |
| Positionnement | mini-app métier historique | démonstrateur avancé officiel |

Le starter 5 est le démonstrateur officiel de référence depuis la Phase 8. Le starter 4 est un démonstrateur historique plus ancien, moins complet sur les nouvelles briques mais plus accessible pour un projet admin multi-entités.

---

## Cohérence avec les profils Forge

| Starter | Profil le plus proche | Justification |
|---|---|---|
| 1 — Contacts | `minimal` ou `standard` | Entité unique, CRUD simple, pas d'auth ni de relations |
| 2 — Auth | `standard` | Application avec authentification, mais auth décalée de Phase 4.5 |
| 3 — Carnet | `standard` | Multi-entités, relations SQL, sans auth ni front dynamique |
| 4 — Suivi | aucun / démonstrateur | Trop métier et trop complexe pour un profil générique |
| 5 — Communes | démonstrateur avancé | Hors profil simple — vitrine complète des briques Forge |

Aucun starter n'utilise actuellement `dynamic` (HTMX) ni `multilingual` (i18n). Ce sont des directions à explorer dans les starters futurs.

---

## Risques détectés

### Risque 1 — Double approche auth (critique)

Les starters 2 et 4 utilisent `core.security.hashing` / `core.security.session` et implémentent un `auth_model.py` custom. Forge Phase 4.5 a livré `core.auth` avec une table `users` standardisée et les helpers `current_user()`, `@login_required`. Ces deux approches coexistent dans le framework.

**Impact** : un utilisateur qui suit le starter 2 apprend une approche auth différente de celle recommandée par la Phase 4.5. Le risque de confusion est réel.

### Risque 2 — Starter 4 positionné comme "vitrine complète" alors que le starter 5 existe

Depuis la Phase 8, le starter Communes & Séjours est le démonstrateur officiel. Le starter 4 se présente aussi comme "vitrine Forge complète". Les deux mots similaires peuvent créer une ambiguïté.

### Risque 3 — Absence d'i18n dans tous les starters historiques

Aucun des starters 1 à 4 n'utilise `trans()` ou le système i18n. Forge 1.5 a livré l'i18n comme brique standard. Un starter `multilingual` dédié n'existe pas encore.

### Risque 4 — Aucun starter n'utilise les pages publiques (sauf Communes & Séjours)

Les starters 1 à 3 ne proposent pas de pages publiques (`make:public-*`). Seul Communes & Séjours le démontre.

### Risque 5 — `contact-simple` sans `files/` (comportement différent des autres)

Le starter 1 n'a pas de dossier `files/` : il repose entièrement sur `make_entity` + `make_crud`. C'est le seul starter de type `crud`. Si `make_crud` change, le starter change automatiquement — avantage. Mais le comportement est différent des starters 2, 3, 4 qui copient des fichiers figés.

---

## Recommandations pour STARTER-LEGACY-DECISION-001

| Starter | Recommandation | Priorité |
|---|---|---|
| 1 — Contacts | **Conserver officiel** — le plus simple, stable, pédagogique | basse |
| 2 — Auth | **Aligner avec Phase 4.5** ou **documenter comme legacy** | haute |
| 3 — Carnet | **Conserver officiel** — bon exemple de relation SQL | basse |
| 4 — Suivi | **Documenter comme démonstrateur historique** — pas un starter de départ | moyenne |

### Détail des recommandations

**Starter 1** : rien à faire. Conserver tel quel. Peut éventuellement être aligné sur le profil `minimal` dans STARTER-PROFILES-001.

**Starter 2** : deux options à décider dans STARTER-LEGACY-DECISION-001 :
- Option A — Aligner : réécrire l'auth en utilisant `core.auth` (Phase 4.5). Coût moyen.
- Option B — Legacy : marquer explicitement ce starter comme "approche historique avant Phase 4.5" dans la doc.

**Starter 3** : conserver officiel. Vérifier que le format `relations.json` est toujours à jour. Peut être aligné sur le profil `standard` dans STARTER-PROFILES-001.

**Starter 4** : documenter clairement son statut de démonstrateur historique (pas un starter de départ recommandé). Signaler que l'auth utilisée est pré-Phase 4.5. Clarifier son positionnement vis-à-vis du starter 5.

---

*Document produit par STARTER-LEGACY-AUDIT-001. Les décisions sont à prendre dans STARTER-LEGACY-DECISION-001.*
