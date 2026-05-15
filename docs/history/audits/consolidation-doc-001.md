# Audit CONSOLIDATION-DOC-001 — Cohérence documentaire Forge

## Objectif

Auditer la cohérence globale de la documentation Forge après les phases 4.5 à 9.1, la modernisation des starters, l'arrivée des profils, le starter Communes & Séjours et la séparation Forge / Forge Design. Identifier les lacunes et incohérences sans les corriger massivement.

---

## Synthèse

**Verdict : la documentation Forge est cohérente et publiable.**

La version 1.5.0 est affirmée de façon cohérente dans README, guide, installation et référence. La navigation MkDocs couvre 40 pages organisées logiquement. Les starters ont chacun leur documentation. Les commandes CLI récentes (`auth:user:role:*`, `module:*`, `forge new --profile`) sont documentées dans les bonnes pages.

Deux lacunes notables : `docs/modules.md` est absent (les modules sont documentés dans `docs/reference.md` mais sans page dédiée), et `docs/starters/communes-sejours/rebuild.md` n'existe pas (les starters 1–4 ont chacun un `rebuild.md`). Aucune incohérence bloquante.

---

## Fichiers audités

| Fichier | Existe |
|---------|--------|
| `README.md` | ✅ (849 lignes) |
| `mkdocs.yml` | ✅ (126 lignes) |
| `docs/index.md` | ❌ — `docs/index.html` généré par `forge sync:landing` |
| `docs/guide.md` | ✅ |
| `docs/reference.md` | ✅ |
| `docs/installation.md` | ✅ |
| `docs/deployment.md` | ✅ |
| `docs/auth.md` | ✅ |
| `docs/rbac.md` | ✅ |
| `docs/modules.md` | ❌ — absent |
| `docs/profiles.md` | ✅ |
| `docs/front.md` | ✅ |
| `docs/forge-roadmap.md` | ✅ |
| `docs/forge-design-roadmap.md` | ✅ |
| `docs/starters/index.md` | ✅ |
| `docs/starters/01-contact-simple/` | ✅ (index.md + rebuild.md) |
| `docs/starters/02-utilisateurs-auth/` | ✅ (index.md + rebuild.md) |
| `docs/starters/03-carnet-contacts/` | ✅ (index.md + rebuild.md) |
| `docs/starters/04-suivi-comportement-eleves/` | ✅ (index.md + rebuild.md) |
| `docs/starters/communes-sejours/` | ✅ index.md — ❌ rebuild.md absent |
| `docs/audits/` | ✅ 13 fichiers (non référencés dans la nav MkDocs — intentionnel) |

---

## Tableau de synthèse

| Zone documentaire | État | Commentaire |
|---|---|---|
| README | ✅ OK | Cohérent, version 1.5.0, limites honnêtes, liens valides |
| MkDocs nav | ✅ OK | 40 pages, starters rangés, audits hors nav (intentionnel) |
| Roadmap Forge | ✅ OK | forge-roadmap.md seul, roadmap.md absent, prochaines priorités à jour |
| Forge Design | ✅ OK | Séparé dans forge-design-roadmap.md, présenté comme projet compagnon futur |
| Versions | ✅ OK | 1.5.0 cohérent partout, 2.0 uniquement dans la roadmap comme objectif |
| CLI / documentation | ✅ OK | auth:user:role:*, module:*, forge new --profile documentés |
| Starters | ✅ OK | 5 starters avec statuts clairs — communes-sejours sans rebuild.md |
| Profils | ✅ OK | 4 profils, standard par défaut, lien depuis README |
| Modules | ⚠️ LACUNE | docs/modules.md absent — modules couverts dans reference.md uniquement |
| Auth/RBAC | ✅ OK | Séparation RBAC générique / Auth/User optionnel claire |
| Front/i18n | ✅ OK | Tailwind officiel, HTMX et Alpine optionnels, pas de SPA intégrée |
| Déploiement | ✅ OK | Nginx recommandé, forge deploy:init/check documentés |

---

## Cohérence README

**README.md — 849 lignes. Cohérent.**

- Version 1.5.0 affirmée dès le titre (ligne 1) et dans les commandes d'installation.
- Description : "Framework web MVC pur Python, HTTPS natif, Jinja2 intégré." — précis et honnête.
- Profils mentionnés : `--profile minimal|standard|dynamic|multilingual`, défaut `standard`, lien vers `docs/profiles.md`. ✅
- Limites explicitement listées (sessions mémoire, pas d'ORM, pas de rechargement automatique). ✅
- Aucune promesse de fonctionnalité non livrée détectée. ✅
- Forge Design non mentionné dans le README public — correct (projet séparé). ✅

---

## Cohérence MkDocs

**mkdocs.yml — 126 lignes. Navigation propre.**

- 40 pages dans la navigation, organisées en 9 sections.
- `docs/roadmap.md` absent de la navigation et du disque. ✅
- `docs/starters/index.md` présent dans la navigation. ✅
- `docs/forge-design-roadmap.md` présent dans la section "Projet". ✅
- La navigation référence `index.html` (pas `index.md`) — correct : l'accueil est généré par `forge sync:landing`.

**Pages dans `docs/audits/` (13 fichiers) non référencées dans la navigation :** choix intentionnel. Les audits sont des documents de diagnostic technique interne, pas du contenu utilisateur. Acceptable.

**`docs/modules.md` absent de la navigation et du disque.** Les modules sont documentés dans `docs/reference.md` mais sans entrée dédiée dans la navigation. Lacune à corriger dans un ticket suivant.

---

## Cohérence roadmap Forge

- `docs/forge-roadmap.md` est le seul fichier roadmap Forge. `docs/roadmap.md` n'existe pas. ✅
- Les phases 3 à 9.1 sont marquées terminées.
- Phase 9.5 (Consolidation) : en cours — tickets CONSOLIDATION-* en séquence.
- Phase 10 (Publication Forge 2.0) : présentée comme objectif, pas comme état livré. ✅
- Prochaine priorité déclarée : `CONSOLIDATION-DOC-001` (puis `CONSOLIDATION-TESTS-001`).

---

## Cohérence Forge / Forge Design

- `docs/forge-design-roadmap.md` existe séparément. ✅
- Forge Design est présenté comme "projet compagnon de Forge — il ne fait pas partie du cœur Forge 2.0". ✅
- Aucune confusion entre Forge et Forge Design dans la documentation publique. ✅
- Forge Design non mentionné dans README, guide, reference — correct. ✅

---

## Cohérence versions

Version 1.5.0 cohérente dans tous les fichiers audités :

| Fichier | Mention |
|---------|---------|
| README.md | Titre "Framework MVC Python 1.5.0" (ligne 1) |
| docs/installation.md | "référence stable `v1.5.0`" |
| docs/guide.md | `git clone --branch v1.5.0` |
| docs/reference.md | "API publique actuelle de Forge `1.5.0`" |
| docs/forge-roadmap.md | "Tag recommandé : `v1.5.0`" |

**Forge 2.0 n'apparaît que dans les sections de roadmap** (objectif futur). Aucune affirmation de livraison. ✅

---

## Cohérence CLI / documentation

**Commandes récentes vérifiées dans la documentation :**

| Commande | Documentée dans | État |
|----------|----------------|------|
| `forge new --profile` | README, docs/profiles.md | ✅ |
| `forge auth:user:role:add` | docs/auth.md, docs/rbac.md, docs/reference.md | ✅ |
| `forge auth:user:role:remove` | docs/auth.md, docs/rbac.md, docs/reference.md | ✅ |
| `forge auth:user:roles` | docs/auth.md | ✅ |
| `forge module:list` | docs/reference.md | ✅ |
| `forge module:install` | docs/reference.md | ✅ |
| `forge module:files` | docs/reference.md | ✅ |
| `forge module:routes` | docs/reference.md | ✅ |
| `forge starter:list` | docs/reference.md | ✅ |
| `forge starter:build` | docs/reference.md, docs/starters/ | ✅ |
| `forge deploy:init` | docs/deployment.md | ✅ |
| `forge deploy:check` | docs/deployment.md | ✅ |

**Commandes notées dans l'audit CLI mais absentes de la documentation utilisateur :**

- `build:model`, `check:model` — présentes dans la CLI, mentionnées dans README, mais sans section dédiée dans `docs/reference.md`. À vérifier dans CONSOLIDATION-DOC-001 (correction hors périmètre de ce ticket).
- `forge docs:pdf` — présente dans la CLI, documentée dans `docs/pdf.md`, mais `docs/pdf.md` n'est pas dans la navigation principale.

---

## Cohérence starters

**5 starters correctement documentés avec statuts clairs :**

| Starter | Statut déclaré | rebuild.md |
|---------|---------------|------------|
| 1 — Contacts | Officiel simple (`minimal`/`standard`) | ✅ |
| 2 — Utilisateurs/Auth | Auth minimale moderne (`standard`) | ✅ |
| 3 — Carnet de contacts | Officiel relationnel (`standard`) | ✅ |
| 4 — Suivi pédagogique | Historique / legacy | ✅ |
| 5 — Communes & Séjours | Démonstrateur avancé principal (`standard`) | ❌ absent |

**Lacune :** `docs/starters/communes-sejours/rebuild.md` n'existe pas. Les starters 1–4 ont tous leur fichier de reconstruction. La cohérence serait meilleure avec un rebuild.md pour le starter 5 (même minimal).

**Référence tableau des fichiers dans docs/starters/index.md (ligne 147-153) :** indique `—` pour communes-sejours rebuild — incohérence avec les autres starters qui ont rebuild.md documenté.

---

## Cohérence profils

**docs/profiles.md — 4 profils cohérents. Bien documenté.**

- `minimal`, `standard`, `dynamic`, `multilingual` — tous définis.
- `standard` comme défaut — confirmé.
- `forge new MonProjet --profile standard` — documenté.
- `forge_profile.txt` — mentionné dans profiles.md. ✅
- Relation profils ↔ starters — expliquée dans docs/starters/index.md (`## Différence entre profil et starter`). ✅

---

## Cohérence modules

**docs/modules.md : absent.**

Les modules sont documentés dans `docs/reference.md` (section dédiée) mais sans page propre. La navigation MkDocs n'a pas de section "Modules".

**Ce qui est documenté dans docs/reference.md :**
- `forge module:list`, `module:install`, `module:files`, `module:routes` — présents.
- Rôle du dossier `modules/` comme runtime officiel des routes.

**Ce qui n'est pas documenté dans la doc publique :**
- Limites du système de modules : pas de rollback, pas de `module:remove`, pas de `module:update`, installations partielles non détectées.
- Ces limites sont présentes dans `docs/audits/consolidation-001-architecture.md` (interne).

**Recommandation :** Créer `docs/modules.md` dans un ticket dédié post-consolidation.

---

## Cohérence Auth / RBAC

**docs/auth.md et docs/rbac.md — bien séparés et cohérents.**

- Séparation RBAC générique (core.security) / Auth/User optionnel (core.auth) : expliquée clairement. ✅
- "Auth répond à : qui est l'utilisateur ? RBAC répond à : qu'a-t-il le droit de faire ?" ✅
- `user_roles` côté Auth/User — documenté dans docs/auth.md. ✅
- Commandes `auth:user:role:add`, `auth:user:role:remove`, `auth:user:roles` — documentées dans docs/auth.md, docs/rbac.md et docs/reference.md. ✅
- Limites repoussées (WebAuthn, SAML, multi-tenant, invitations) — mentionnées dans docs/auth.md. ✅

**Typo mineure :** `docs/auth.md` ligne 1 : "Auth/User avancee" — accent manquant sur le dernier `e`. Coquille cosmétique.

---

## Cohérence front / i18n

**docs/front.md — cohérent.**

- Tailwind CSS comme framework CSS officiel. ✅
- HTMX optionnel, injectable via `forge js:init htmx`. ✅
- Alpine.js optionnel, injectable via `forge js:init alpine`. ✅
- "HTML serveur reste la base. HTMX et Alpine améliorent l'expérience." ✅
- Pas de SPA React/Vue/Svelte intégrée. ✅
- i18n : documentée dans docs/reference.md et dans les pages starters. Pas de page dédiée `docs/i18n.md` — acceptable car i18n est couvert dans front.md et reference.md.

---

## Cohérence déploiement

**docs/deployment.md — bien documenté, réaliste.**

- Architecture recommandée : Nginx (reverse proxy) → Forge Python. ✅
- HTTPS dev (serveur Python autonome) distingué de la production. ✅
- "Ne jamais exposer le serveur Forge directement à Internet en production." ✅
- `forge deploy:init` et `forge deploy:check` documentés avec exemples. ✅
- Pas de promesse "prêt SaaS" ou "multi-tenant". ✅

---

## Documents d'audit existants

13 documents dans `docs/audits/` — cohérents entre eux :

| Document | Verdict | Cohérence avec roadmap |
|----------|---------|----------------------|
| consolidation-001-architecture.md | Forge cohérent après phases 4.5–9.1 | ✅ |
| consolidation-cli-001.md | CLI cohérente, 4 incohérences mineures | ✅ |
| auth-security-audit-001.md | Auth/User livré et sécurisé | ✅ |
| starter-legacy-audit-001.md | Starters historiques audités | ✅ |
| starter-legacy-decision-001.md | Décisions de statut prises | ✅ |
| starter-modernization-plan-001.md | Plan 9.1 exécuté | ✅ |
| crud-*.md (6 fichiers) | Phase 5 terminée | ✅ |
| media-v2-audit.md | Phase 1 terminée | ✅ |

Aucune contradiction entre les verdicts des audits et l'état de la roadmap. ✅

---

## Points cohérents

1. **Version 1.5.0 cohérente** dans tous les fichiers audités. Forge 2.0 uniquement en roadmap.
2. **Forge Design séparé** — roadmap indépendante, projet compagnon futur, non mélangé dans la doc Forge.
3. **Commandes CLI récentes documentées** — auth:user:role:*, module:*, forge new --profile tous présents dans les bonnes pages.
4. **Starters documentés avec statuts clairs** — 5 starters, 4 rebuild.md, index consolidé.
5. **Profils cohérents** — 4 profils, standard par défaut, lien depuis README.
6. **Déploiement réaliste** — Nginx recommandé, limites du serveur dev clairement énoncées.
7. **Auth/RBAC séparés** — distinction claire, commandes documentées, limites WebAuthn/SAML reconnues.
8. **README sans promesses excessives** — limites honnêtement exposées.
9. **docs/roadmap.md absent** — seul docs/forge-roadmap.md existe. ✅
10. **docs/audits/ cohérent** — 13 documents internes non contradictoires.

---

## Incohérences détectées

| N° | Zone | Description | Sévérité |
|----|------|-------------|----------|
| 1 | Modules | `docs/modules.md` absent — limites des modules non documentées publiquement | ⚠️ NOTABLE |
| 2 | Starters | `docs/starters/communes-sejours/rebuild.md` absent — incohérence avec starters 1–4 | ⚠️ FAIBLE |
| 3 | Auth | Typo "avancee" → "avancée" dans docs/auth.md ligne 1 | ℹ️ COSMÉTIQUE |
| 4 | CLI/Doc | `build:model` / `check:model` — peu visibles dans la documentation (mention README, absent de reference.md) | ⚠️ FAIBLE |
| 5 | Navigation | `docs/pdf.md` présent mais non référencé dans mkdocs.yml navigation principale | ℹ️ MINEUR |
| 6 | Audits | Audits internes (docs/audits/) non navigables — choix intentionnel, mais non documenté | ℹ️ ACCEPTABLE |

---

## Incohérences bloquantes

**Aucune incohérence bloquante détectée.**

La documentation est suffisamment cohérente pour poursuivre la consolidation.

---

## Recommandations

Ces corrections ne doivent pas être faites dans CONSOLIDATION-DOC-001. Elles sont proposées comme tickets futurs.

### Ticket proposé : CONSOLIDATION-DOC-MODULES-001

Créer `docs/modules.md` couvrant :
- Présentation du système de modules.
- Commandes `module:list`, `module:install`, `module:files`, `module:routes`.
- Rôle du dossier `modules/` comme runtime officiel des routes.
- Limites explicites : pas de rollback, pas de `module:remove`, pas de `module:update`.
- Lien vers les audits de sécurité modules.

### Ticket proposé : CONSOLIDATION-STARTER-001 (existant)

Dans CONSOLIDATION-STARTER-001, ajouter :
- Créer `docs/starters/communes-sejours/rebuild.md` (même minimal).
- Corriger `doc_url` starters 2 et 5 dans les starter.json.

### Ticket proposé : DOC-FIX-MINOR-001

Corrections cosmétiques groupées :
- `docs/auth.md` ligne 1 : "avancee" → "avancée".
- Vérifier `build:model` / `check:model` dans `docs/reference.md`.
- Ajouter `docs/pdf.md` dans la navigation ou l'exclure explicitement.

---

## Tickets futurs proposés

| Ticket | Objectif |
|--------|---------|
| CONSOLIDATION-TESTS-001 | Audit couverture tests et zones fragiles |
| CONSOLIDATION-NON-OVERWRITE-001 | Vérifier la préservation du code utilisateur |
| CONSOLIDATION-MODULES-001 | Vérifier cycle complet des modules |
| CONSOLIDATION-PROFILES-001 | Vérifier cohérence des profils générés |
| CONSOLIDATION-FRONT-001 | Vérifier Tailwind / HTMX / Alpine / templates |
| CONSOLIDATION-STARTER-001 | Vérifier Communes & Séjours + doc_url starters 2 et 5 |
| CONSOLIDATION-ROADMAP-001 | Décider Forge 2.0 / Forge Design / post-roadmap |
| CONSOLIDATION-DOC-MODULES-001 | Créer docs/modules.md avec limites documentées |
| DOC-FIX-MINOR-001 | Corrections cosmétiques groupées |

---

## Verdict final

**La documentation Forge est cohérente et publiable.**

Version 1.5.0 affirmée honnêtement. Navigation MkDocs propre. Commandes CLI récentes documentées. Starters avec statuts clairs. Auth/RBAC séparés. Déploiement réaliste. Forge Design séparé.

Deux lacunes notables (`docs/modules.md` absent, `commons-sejours/rebuild.md` absent) doivent être adressées dans les tickets de consolidation suivants. Aucune lacune ne bloque la publication.

---

*Audit réalisé le 2026-05-08. Forge post-1.5.0. 4810 tests passés, 1 skipped.*
