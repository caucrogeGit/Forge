# Audit BETA11-DX-CLOSING-AUDIT-001

**Date** : 2026-05-27
**Branche** : `main`
**Périmètre** : clôturer officiellement la phase Forge 1.0.0-beta.11
(Expérience développeur / Bonjour Forge), transformer le WIP validé
par `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` en état publiable, et
décider GO / NO-GO pour `RELEASE-BETA11-001`.

---

## 1. Résumé exécutif

Phase beta 11 close au sens code + tests + commits + roadmap.

- **14 tickets** livrés (7 DX, 1 clôture documentaire, 2 installation
  WSL, 4 landing / install / structure).
- **5 commits** créés (4 commits par périmètre + 1 commit audit) pour
  passer du working tree WIP à un historique lisible.
- **15 051 tests passés, 6 skipped** — aucune régression.
- **5 validations canoniques OK** (`pytest`, `compileall`, `ruff`,
  `mkdocs --strict`, `git diff --check`) + `forge sync:landing --check`.
- Pas de bump version, pas de tag, pas de publication PyPI — c'est le
  périmètre du ticket suivant `RELEASE-BETA11-001`.

**Décision : GO pour `RELEASE-BETA11-001`.**

---

## 2. Tickets beta 11 livrés

Les 14 tickets ci-dessous sont confirmés livrés : code + tests
+ entrée roadmap + commit.

| Ticket | Domaine | Commit |
|---|---|---|
| `FORGE-RUN-COMMAND-001` | CLI runtime | `185be93` |
| `DEV-SERVER-AUTORELOAD-001` | CLI runtime | `185be93` |
| `API-INSPECTABLE-OBJECTS-CONVENTION-001` | HTTP | `185be93` |
| `DX-TYPED-SKELETONS-001` | Génération | `185be93` |
| `DX-RENDER-ERROR-001` | Templating | `185be93` |
| `DX-DEBUG-DUMP-HTML-001` | HTTP / Dev | `185be93` |
| `STARTER-BONJOUR-FORGE-001` | Starter | `b03d7af` |
| `DX-DOCS-BONJOUR-FORGE-CLOSE-001` | Docs | `6b46281` |
| `INSTALL-WSL-DOCS-001` | Docs install | `07667f7`, `e7b1f6a`, `7a9c671` (pré-existants) |
| `INSTALL-WSL-DOCS-FIELD-FIX-001` | Docs install | `07667f7`, `e7b1f6a` (pré-existants) |
| `LANDING-INSTALL-CARDS-001` | Landing | `07667f7`, `e7b1f6a`, `f19dc91` |
| `INSTALL-CORE-DEV-DOCS-AUDIT-001` | Docs install | `07667f7` (pré-existant) |
| `INSTALL-DOCS-STRUCTURE-001` | Docs install | `07667f7` (pré-existant) |
| `LANDING-PUBLIC-CONTRACT-REALIGN-001` | Landing | `07667f7`, `e7b1f6a`, `f19dc91` |

Tickets d'audit beta 11 :

| Ticket | Statut | Commit |
|---|---|---|
| `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` | livré (audit pré-clôture) | (ce commit) |
| `BETA11-DX-CLOSING-AUDIT-001` | livré (ce ticket) | (ce commit) |

---

## 3. État Git avant clôture

État au début du ticket (post-audit `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001`) :

```text
Branche : main
Dernier commit : 7a9c671 fix(docs): réparer mkdocs --strict après
                          suppression installation-github.md

git status --short :
  67 fichiers modifiés (M)
   9 fichiers neufs (??)
   2 fichiers supprimés (D)

git diff --stat :
  66 files changed, 1093 insertions(+), 967 deletions(-)
```

Tous les fichiers WIP étaient attachés aux tickets beta 11 déjà
déclarés « livré » dans la roadmap. Aucun fichier parasite.

---

## 4. Commits créés pendant ce ticket

5 commits cohérents — un par périmètre, plus l'audit.

### Commit 1 — `185be93`

```
feat(dx): forge run + autoreload + Request/Response inspectables + skeletons typés
```

Périmètre : 6 tickets DX (`FORGE-RUN-COMMAND-001`,
`DEV-SERVER-AUTORELOAD-001`,
`API-INSPECTABLE-OBJECTS-CONVENTION-001`, `DX-TYPED-SKELETONS-001`,
`DX-RENDER-ERROR-001`, `DX-DEBUG-DUMP-HTML-001`).

Contenu :
- `core/http/{request,response,helpers}.py` : convention d'inspection
  + helpers `text/html/json/debug` + `TemplateNotFoundError`.
- `core/http/debug_dumper.py` (nouveau) : rendu HTML dev pour
  `Response.debug(obj)`.
- `core/templating/errors.py` (nouveau) : `TemplateNotFoundError`.
- `integrations/jinja2/renderer.py` : re-raise via l'exception
  publique.
- `forge.py`, `forge_cli/help.py`, `forge_cli/help_dispatch.py` :
  enregistrement de `forge run`.
- `forge_cli/run.py` (nouveau) : commande `forge run` officielle.
- `forge_cli/dev_reloader.py` (nouveau) : superviseur autoreload.
- `forge_cli/entities/crud/controller_builder.py`,
  `forge_cli/public_form.py`, `forge_cli/public_list.py`,
  `forge_cli/public_page.py` : skeletons typés.
- 9 contrôleurs de starters (`auth-mfa`, `carnet-contacts`,
  `communes-sejours`, `suivi-comportement-eleves`, `utilisateurs-auth`)
  alignés sur la convention typée.
- 6 nouveaux fichiers de tests + ~22 tests existants alignés sur les
  nouvelles signatures typées + `tests/fake_request.py` étendu.
- `tests/meta/test_cli_help_flags_closing_audit_001.py` aligné sur
  l'arrivée de `forge run`.

### Commit 2 — `b03d7af`

```
feat(starter): refonte pédagogique du starter d'entrée Bonjour Forge (STARTER-BONJOUR-FORGE-001)
```

Périmètre : 1 ticket (`STARTER-BONJOUR-FORGE-001`).

Contenu :
- `forge_cli/starters/data/welcome/files/mvc/controllers/welcome_controller.py`
  refondu autour du parcours `Response.text(...) → request.param(...) →
  Response.debug(request.data) → BaseController.render(...)`.
- Suppression de
  `forge_cli/starters/data/welcome/files/mvc/views/welcome/index.html`.
- `routes.py.snippet` et `starter.json` mis à jour.
- `tests/test_starter_bonjour_forge_001.py` (nouveau).
- `tests/meta/test_starter_welcome_001.py` réaligné.

### Commit 3 — `6b46281`

```
docs(dx): clôture documentaire beta 11 — Bonjour Forge (DX-DOCS-BONJOUR-FORGE-CLOSE-001)
```

Périmètre : 1 ticket (`DX-DOCS-BONJOUR-FORGE-CLOSE-001`).

Contenu :
- `docs/lts-policy.md`, `docs/starters/index.md`,
  `docs/starters/welcome/index.md` mis à jour.
- `tests/meta/test_doc_15min.py` supprimé.
- `tests/meta/test_doc_bonjour_forge.py` créé (réécriture autour
  du nouveau parcours).
- `tests/meta/test_getting_started_3_0_001.py`,
  `tests/meta/test_meta_tests_root_migration_001.py`,
  `tests/meta/test_docs_reference_split_001.py` réalignés.

### Commit 4 — `f19dc91`

```
docs(landing): finaliser le réalignement contrat public (LANDING-PUBLIC-CONTRACT-REALIGN-001)
```

Périmètre : finalisation de `LANDING-PUBLIC-CONTRACT-REALIGN-001`
(le gros du ticket était déjà committé en `07667f7` / `e7b1f6a`).

Contenu :
- `mvc/views/landing/index.html` et `docs/index.html`
  resynchronisés (modifications manuelles validées).
- `tests/meta/test_landing_post_2_2_refresh.py` réaligné sur le
  contrat public actuel (4 cards Installation, plus de marqueurs
  beta.10 obsolètes).
- `tests/meta/test_landing_public_contract.py` réaligné sur le
  chapeau actuel « Modules officiels opt-in installables séparément ».
- `docs/roadmap/forge-roadmap.md` : entrée
  `LANDING-PUBLIC-CONTRACT-REALIGN-001` enrichie (marqueurs réels
  des tests réalignés).

### Commit 5 — audit de clôture

Ce commit contient :

- `docs/history/audits/audit-beta11-post-docs-consolidation.md`
  (rapport de l'audit précédent, jamais commité).
- `docs/history/audits/audit-beta11-dx-closing.md` (présent rapport).
- `docs/roadmap/forge-roadmap.md` : ajout des entrées
  `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` et
  `BETA11-DX-CLOSING-AUDIT-001` marquées **livré**.

---

## 5. État documentation

- `docs/bonjour-forge.md` : parcours développeur livré.
- `docs/install/` : `index.md`, `pipx.md`, `core-dev.md`,
  `windows-wsl.md`, `mariadb.md`, `vm-debian.md`, `windows.md`,
  `production.md` — structure consolidée.
- `docs/reference/http.md` : convention d'inspection
  Request/Response documentée.
- `docs/starters/welcome/index.md` : refonte pédagogique.
- `mkdocs build --strict` : **OK** (10,54 s, uniquement quelques
  INFO sur liens relatifs sans cible MkDocs — non bloquants).

---

## 6. État landing

- `mvc/views/landing/index.html` : 4 cards Installation
  (`windows-wsl`, `pipx-user`, `core-dev`, `production`), aucune en
  `md:col-span-2` ; 7 cards Starters ; 6 cards API Forge ; 4 cards
  modules opt-in ; section positionnement ; contact statique
  `mailto:forgemvc@gmail.com`.
- `docs/index.html` : généré par `forge sync:landing` (banner
  GÉNÉRÉ PAR conservé).
- `forge sync:landing --check` : **OK** (`docs/index.html` et
  `docs/static/` synchronisés).

---

## 7. État tests

| Suite | Résultat |
|---|---|
| Tests DX ciblés (7 fichiers) | **348 passed** en 6,06 s |
| Tests docs/landing/install ciblés (8 fichiers) | **287 passed** en 56,18 s |
| `tests/meta` (suite complète) | **6 107 passed, 4 skipped** en 4 min 29 s |
| **Suite complète `pytest`** | **15 051 passed, 6 skipped** en 5 min 28 s |

Détail des suites DX :

```text
tests/test_forge_run_command_001.py                       passed
tests/test_dev_server_autoreload_001.py                   passed
tests/test_api_inspectable_objects_convention_001.py      passed
tests/test_dx_typed_controller_skeletons_001.py           passed
tests/test_dx_render_missing_template_error_001.py        passed
tests/test_starter_bonjour_forge_001.py                   passed
tests/test_dx_debug_dump_html_001.py                      passed
```

---

## 8. État packaging sans bump

Aucun bump version dans ce ticket. État actuel :

- `pyproject.toml` racine : `version = "1.0.0b10"` (inchangé).
- `packages/*/pyproject.toml` : versions opt-in inchangées.
- `CHANGELOG.md` : section `[1.0.0-beta.11]` **non encore présente**
  — bloquée par le hook PreToolUse `forge-write-if-new.sh`
  (CLAUDE.md §12 règle 3 : `CHANGELOG.md` fait partie des fichiers
  structurants toujours bloqués). Le texte exact à insérer est
  préparé en **annexe 1** ci-dessous et doit être appliqué
  manuellement par l'humain dans le cadre de `RELEASE-BETA11-001`
  (qui portera le bump version + tag).
- Aucun tag `v1.0.0-beta.11` créé.
- Aucune publication PyPI.

---

## 9. Risques restants

### 9.1 Bloquants

**Aucun.**

### 9.2 Non bloquants — à traiter dans `RELEASE-BETA11-001`

- **Section `[1.0.0-beta.11]` du `CHANGELOG.md`** : bloquée par hook,
  patch préparé en annexe — à appliquer manuellement à l'ouverture
  de `RELEASE-BETA11-001`.
- **Bump version** : `pyproject.toml` racine + 4 sous-paquets
  (`packages/forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`,
  `forge-mvc-stats`, plus `forge-mvc-media` côté CHANGELOG opt-in).
- **Tag SemVer** : `v1.0.0-beta.11` (jamais PEP 440).
- **Validation release** : `tools/release-validate.sh` (mode
  `--convert`), `pip-audit`, `npm audit --omit=dev`.
- **Publication PyPI** : conditionnée à validation explicite,
  comme pour beta.10.

### 9.3 Anomalies découvertes pendant ce ticket

- Le hook `forge-write-if-new.sh` bloque toute écriture sur
  `CHANGELOG.md`, ce qui empêche l'agent de préparer la section
  beta.11 dans le ticket de clôture. C'est aligné sur la politique
  charte Forge v2 §9 et CLAUDE.md §12 — l'écriture passe par
  l'humain ou un ticket dédié. Pour beta 12, on pourrait envisager
  un ticket `CHANGELOG-PRE-FILL-001` qui ajouterait au hook une
  exception « préparation de section non-version-bumpée » — hors
  périmètre actuel.

---

## 10. Décision GO / NO-GO

**Décision : GO pour `RELEASE-BETA11-001`.**

Justifications :

1. Les 14 tickets beta 11 sont confirmés livrés (code, tests,
   roadmap, commits).
2. Working tree propre après les 5 commits prévus.
3. Suite complète : 15 051 passed, 6 skipped.
4. 5 validations canoniques : OK (pytest, compileall, ruff,
   mkdocs --strict, git diff --check).
5. `forge sync:landing --check` : OK.
6. Aucun bloquant fonctionnel.
7. Roadmap mise à jour pour pointer vers `RELEASE-BETA11-001`.
8. `CHANGELOG.md` non modifié par l'agent (hook protégé) : patch
   exact préparé en annexe pour application humaine au tout début
   de `RELEASE-BETA11-001`.

Aucun ticket correctif intermédiaire requis.

---

## 11. Prochain ticket

**`RELEASE-BETA11-001`** — release `Forge 1.0.0-beta.11`.

Périmètre minimum recommandé :

1. Appliquer le patch CHANGELOG (annexe 1) sur `CHANGELOG.md`.
2. Bump `pyproject.toml` racine `1.0.0b10` → `1.0.0b11`.
3. Bump `packages/forge-mvc-mfa/pyproject.toml`,
   `packages/forge-mvc-rbac/pyproject.toml`,
   `packages/forge-mvc-workflow/pyproject.toml`,
   `packages/forge-mvc-stats/pyproject.toml`,
   `packages/forge-mvc-media/pyproject.toml` (cohérence opt-ins).
4. `tools/release-validate.sh` (mode `--convert` + audits dépendances
   bloquants).
5. `pip-audit` + `npm audit --omit=dev` clean.
6. Build et installation isolés (`twine check`, install locale).
7. Tag SemVer `v1.0.0-beta.11`.
8. Publication PyPI conditionnée à validation explicite (comme beta.10).
9. Mise à jour de la version affichée sur la landing
   (`mvc/views/landing/index.html` et `docs/index.html` via
   `forge sync:landing`).

---

## Annexe 1 — Patch `CHANGELOG.md` à appliquer manuellement

Le hook `forge-write-if-new.sh` empêche l'agent d'écrire dans
`CHANGELOG.md`. Voici le bloc exact à insérer **avant** la ligne
`## [1.0.0-beta.10] — 2026-05-25` :

```markdown
## [1.0.0-beta.11] — non encore taguée

Section préparée par `BETA11-DX-CLOSING-AUDIT-001`. Le bump version,
le tag `v1.0.0-beta.11` et la publication PyPI sont portés par
`RELEASE-BETA11-001`.

### Expérience développeur — point d'entrée unifié et inspectabilité

- `forge run` officialise le point d'entrée du serveur de développement
  (FORGE-RUN-COMMAND-001) — refus du serveur intégré en `APP_ENV=prod`
  avec message WSGI clair, délégation à `scripts/dev-server.sh` ou
  `python app.py` en `dev`.
- Superviseur d'autoreload `forge_cli.dev_reloader`
  (DEV-SERVER-AUTORELOAD-001) — polling `stat()` sur `app.py`,
  `config.py`, `env/dev`, `mvc/**/*.{py,html,json,sql}`, `core/**/*.py`,
  stdlib uniquement. Désactivable via `--no-reload`.
- Convention d'inspection des classes API publiques
  (API-INSPECTABLE-OBJECTS-CONVENTION-001) — `Request` et `Response`
  exposent `.data` avec masquage automatique
  (Authorization/Cookie/password/csrf/token/api_key/secret) ; helpers
  `text/html/json/debug` côté `Response` ; convention documentée dans
  `docs/reference/http.md`.
- Squelettes générés typés (DX-TYPED-SKELETONS-001) — imports
  `Request`/`Response` automatiques et annotations
  `def action(request: Request) -> Response:` sur toutes les actions
  publiques du starter `welcome`, des générateurs `make:crud`,
  `make:public-*` et des 6 starters officiels.
- Erreur développeur claire quand `BaseController.render(...)` cible une
  vue inexistante (DX-RENDER-ERROR-001) — `TemplateNotFoundError`
  pédagogique en `dev`, réponse minimale en `prod`, aucun stacktrace.
- Rendu HTML pédagogique pour `Response.debug(obj)`
  (DX-DEBUG-DUMP-HTML-001) — `core.http.debug_dumper` (masquage des clés
  sensibles, profondeur bornée, détection des cycles) ; comportement
  prod inchangé (404 minimal, aucune fuite).

### Starter d'entrée — Bonjour Forge

- Refonte pédagogique du starter `welcome` (STARTER-BONJOUR-FORGE-001) —
  alias `bonjour` / `bonjour-forge` / `bienvenue` / `7`. Progression :
  `index` retourne `Response.text("Bonjour Forge")`, puis
  `/welcome/greet?name=…` (`request.param(...)`),
  `/welcome/inspect` (`Response.debug(request.data)`), enfin
  `/welcome/cycle` introduit `BaseController.render(...)`. Vue
  `welcome/index.html` retirée.

### Documentation, installation et landing

- Clôture documentaire « Bonjour Forge » (DX-DOCS-BONJOUR-FORGE-CLOSE-001)
  — renommage `docs/15-minutes.md` → `docs/bonjour-forge.md`, refonte
  autour du parcours développeur livré.
- Guide officiel d'installation Windows + WSL (INSTALL-WSL-DOCS-001 +
  INSTALL-WSL-DOCS-FIELD-FIX-001) — `docs/install/windows-wsl.md`,
  parcours WSL Ubuntu 24.04 + VS Code Remote WSL + pipx + Node 20 +
  MariaDB avec compte `forge_admin@localhost` dédié.
- Section « Installer Forge selon votre usage » de la landing
  (LANDING-INSTALL-CARDS-001) — 4 cards homogènes
  (`windows-wsl`, `pipx-user`, `core-dev`, `production`).
- Consolidation `docs/install/core-dev.md`
  (INSTALL-CORE-DEV-DOCS-AUDIT-001) — 9 sections couvrant l'installation
  éditable, les 5 validations canoniques avant commit, Tailwind, opt-ins.
- Réorganisation `docs/install/` (INSTALL-DOCS-STRUCTURE-001) —
  `git mv` des 7 pages d'installation sous `docs/install/{index,pipx,
  core-dev,mariadb,vm-debian,windows,github,production}.md`, mise à jour
  des liens internes et de la nav MkDocs.
- Réalignement de la landing canonique sur son contrat public actuel
  (LANDING-PUBLIC-CONTRACT-REALIGN-001) — décisions de suppression
  assumées (5e card Installation, FAQ, Stack technos, compteur tests) ;
  tests landing réalignés.

### Audit

- `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` — audit de l'état réel
  après tous les tickets DX/docs/install/landing ; décision OK pour
  lancer `BETA11-DX-CLOSING-AUDIT-001`.
- `BETA11-DX-CLOSING-AUDIT-001` — découpe et commit du WIP en
  5 commits cohérents, suite complète à 15 051 tests passants
  (6 skipped), décision GO pour `RELEASE-BETA11-001`.

### Notes

- Aucun bump version dans cette section : c'est une préparation. Le
  bump est porté par `RELEASE-BETA11-001`.
- Forge core reste autonome ; les opt-ins (`forge-mvc-rbac`,
  `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`,
  `forge-mvc-media`) restent indépendants.
- La production publique reste WSGI + Gunicorn + reverse proxy.
  `forge run` reste explicitement un outil de développement.

```
