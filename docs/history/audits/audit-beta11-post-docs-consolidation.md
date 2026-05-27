# Audit BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001

**Date** : 2026-05-27
**Branche** : `main`
**Périmètre** : reconstruire l'état réel de la beta 11 après les
travaux DX, documentation, installation et landing — sans rien
ajouter, sans rien corriger massivement.

---

## 1. Résumé de l'audit

La phase beta 11 a livré 14 tickets : 7 tickets DX
(`FORGE-RUN-COMMAND-001` → `DX-DEBUG-DUMP-HTML-001`), 1 ticket de
clôture documentaire (`DX-DOCS-BONJOUR-FORGE-CLOSE-001`), 2 tickets
d'installation WSL (`INSTALL-WSL-DOCS-001` /
`INSTALL-WSL-DOCS-FIELD-FIX-001`), 4 tickets landing/install
(`LANDING-INSTALL-CARDS-001`, `INSTALL-CORE-DEV-DOCS-AUDIT-001`,
`INSTALL-DOCS-STRUCTURE-001`, `LANDING-PUBLIC-CONTRACT-REALIGN-001`).

Les 14 tickets sont marqués **livré** dans la roadmap, et tout le code
correspondant existe — soit déjà committé, soit présent dans le
working tree. Les 5 validations canoniques passent (`pytest`,
`compileall`, `ruff`, `mkdocs --strict`, `git diff --check`), plus
`forge sync:landing --check`.

La seule anomalie significative : **9 fichiers neufs et 67 fichiers
modifiés sont encore non commités** dans le working tree. C'est le
code livré par les tickets DX (run/autoreload/inspect/skeletons/render/
starter Bonjour Forge/debug-dump) et la finalisation landing/install,
qui n'a jamais été poussé dans un commit. C'est exactement le travail
attendu de `BETA11-DX-CLOSING-AUDIT-001` (regrouper et commiter).

Décision : **OK pour lancer `BETA11-DX-CLOSING-AUDIT-001`**.

---

## 2. État Git

```text
Branche : main
Dernier commit : 7a9c671 fix(docs): réparer mkdocs --strict après
                          suppression installation-github.md
```

5 derniers commits (préfixes beta.10 + finalisation install/landing) :

| Commit | Sujet |
|---|---|
| `7a9c671` | fix(docs): réparer mkdocs --strict après suppression installation-github.md |
| `e7b1f6a` | docs(landing): harmoniser fonds de section + retoucher contenu (LANDING-PUBLIC-CONTRACT-REALIGN-001) |
| `07667f7` | docs: restructurer docs/install/ + réaligner landing (INSTALL-DOCS-STRUCTURE-001 + LANDING-PUBLIC-CONTRACT-REALIGN-001) |
| `86b90c2` | fix(landing): simplify static contact link |
| `c789f8a` | test(meta): aligner RELEASE-BETA10-001 livré (RELEASE-BETA10-001) |

Le tag courant côté roadmap reste **`v1.0.0-beta.10`**. Aucun tag
`v1.0.0-beta.11` n'a été posé.

`git diff --stat` (résumé) :

```
66 files changed, 1093 insertions(+), 967 deletions(-)
```

Plus 9 fichiers neufs non suivis (`??`) et 2 suppressions
non commitées (`D`).

---

## 3. Tickets confirmés livrés

Les 14 tickets ci-dessous sont **livrés au sens roadmap + code +
tests**. Pour les tickets « WIP », le code et les tests sont présents
et passent localement, mais ne sont pas encore committés.

| Ticket | État réel | Commit |
|---|---|---|
| `FORGE-RUN-COMMAND-001` | **livré (WIP non commité)** | — |
| `DEV-SERVER-AUTORELOAD-001` | **livré (WIP non commité)** | — |
| `API-INSPECTABLE-OBJECTS-CONVENTION-001` | **livré (WIP non commité)** | — |
| `DX-TYPED-SKELETONS-001` | **livré (WIP non commité)** | — |
| `DX-RENDER-ERROR-001` | **livré (WIP non commité)** | — |
| `STARTER-BONJOUR-FORGE-001` | **livré (WIP non commité)** | — |
| `DX-DEBUG-DUMP-HTML-001` | **livré (WIP non commité)** | — |
| `DX-DOCS-BONJOUR-FORGE-CLOSE-001` | **livré (WIP non commité)** | — |
| `INSTALL-WSL-DOCS-001` | **livré (committé)** | inclus dans commits antérieurs |
| `INSTALL-WSL-DOCS-FIELD-FIX-001` | **livré (committé)** | inclus dans commits antérieurs |
| `LANDING-INSTALL-CARDS-001` | **livré (partiellement WIP)** | landing finale dans `e7b1f6a`, retouches WIP |
| `INSTALL-CORE-DEV-DOCS-AUDIT-001` | **livré (committé)** | `07667f7` |
| `INSTALL-DOCS-STRUCTURE-001` | **livré (committé)** | `07667f7` |
| `LANDING-PUBLIC-CONTRACT-REALIGN-001` | **livré (committé + WIP final)** | `07667f7`, `e7b1f6a`, retouches WIP |

À ne pas confondre :

| Ticket | État réel |
|---|---|
| `BETA11-DX-CLOSING-AUDIT-001` | **pas encore** (clôture WIP à venir) |
| `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` | **présent ticket** |
| `RELEASE-BETA11-001` | **pas encore** |

---

## 4. Tickets partiels ou couverts indirectement

Aucun ticket de la liste n'est partiel sur le périmètre fonctionnel.
La couverture est complète côté code et tests. Le seul écart est le
**statut Git** : les 7 tickets DX + `DX-DOCS-BONJOUR-FORGE-CLOSE-001`
+ finalisation landing/install ne forment pas encore de commits
séparés ; ils sont mêlés dans le working tree.

Décision : ce n'est **pas une régression fonctionnelle**, c'est un
travail de découpe en commits — qui appartient explicitement à
`BETA11-DX-CLOSING-AUDIT-001`.

---

## 5. Fichiers WIP restants

### 5.1 Nouveaux fichiers (untracked)

| Fichier | Ticket associé |
|---|---|
| `core/http/debug_dumper.py` | `DX-DEBUG-DUMP-HTML-001` |
| `core/templating/errors.py` | `DX-RENDER-ERROR-001` |
| `forge_cli/dev_reloader.py` | `DEV-SERVER-AUTORELOAD-001` |
| `forge_cli/run.py` | `FORGE-RUN-COMMAND-001` |
| `tests/meta/test_doc_bonjour_forge.py` | `DX-DOCS-BONJOUR-FORGE-CLOSE-001` |
| `tests/test_api_inspectable_objects_convention_001.py` | `API-INSPECTABLE-OBJECTS-CONVENTION-001` |
| `tests/test_dev_server_autoreload_001.py` | `DEV-SERVER-AUTORELOAD-001` |
| `tests/test_dx_debug_dump_html_001.py` | `DX-DEBUG-DUMP-HTML-001` |
| `tests/test_dx_render_missing_template_error_001.py` | `DX-RENDER-ERROR-001` |
| `tests/test_dx_typed_controller_skeletons_001.py` | `DX-TYPED-SKELETONS-001` |
| `tests/test_forge_run_command_001.py` | `FORGE-RUN-COMMAND-001` |
| `tests/test_starter_bonjour_forge_001.py` | `STARTER-BONJOUR-FORGE-001` |

### 5.2 Fichiers modifiés non commités (par ticket)

- **`FORGE-RUN-COMMAND-001`** : `forge.py`, `forge_cli/help.py`,
  `forge_cli/help_dispatch.py`,
  `tests/meta/test_cli_help_flags_closing_audit_001.py`.
- **`API-INSPECTABLE-OBJECTS-CONVENTION-001`** : `core/http/request.py`,
  `core/http/response.py`, `core/http/helpers.py`,
  `tests/fake_request.py`.
- **`DX-RENDER-ERROR-001`** : `integrations/jinja2/renderer.py`,
  `core/http/helpers.py` (partagé avec `API-INSPECTABLE`).
- **`DX-DEBUG-DUMP-HTML-001`** : `core/http/response.py` (helper
  `Response.debug` recâblé sur `debug_dumper.render_debug_html`).
- **`DX-TYPED-SKELETONS-001`** :
  `forge_cli/entities/crud/controller_builder.py`,
  `forge_cli/public_form.py`, `forge_cli/public_list.py`,
  `forge_cli/public_page.py`, tous les contrôleurs de
  `forge_cli/starters/data/*/files/mvc/controllers/*.py`,
  les ~20 tests `tests/test_make_*`, `tests/test_crud_*`,
  `tests/test_rbac_security.py`, `tests/test_runtime_errors_jsonl.py`.
- **`STARTER-BONJOUR-FORGE-001`** :
  `forge_cli/starters/data/welcome/files/mvc/controllers/welcome_controller.py`,
  suppression de
  `forge_cli/starters/data/welcome/files/mvc/views/welcome/index.html`,
  `forge_cli/starters/data/welcome/routes.py.snippet`,
  `forge_cli/starters/data/welcome/starter.json`,
  `docs/starters/welcome/index.md`, `docs/starters/index.md`,
  `tests/meta/test_starter_welcome_001.py`.
- **`DX-DOCS-BONJOUR-FORGE-CLOSE-001`** :
  suppression de `tests/meta/test_doc_15min.py`,
  `tests/meta/test_getting_started_3_0_001.py`,
  `tests/meta/test_meta_tests_root_migration_001.py`,
  `tests/meta/test_docs_reference_split_001.py`,
  `docs/lts-policy.md`.
- **`LANDING-INSTALL-CARDS-001` / `LANDING-PUBLIC-CONTRACT-REALIGN-001`** :
  `mvc/views/landing/index.html`, `docs/index.html`,
  `tests/meta/test_landing_post_2_2_refresh.py`,
  `tests/meta/test_landing_public_contract.py`.
- **roadmap** : `docs/roadmap/forge-roadmap.md`
  (entrée `LANDING-PUBLIC-CONTRACT-REALIGN-001` réajustée).
- **Divers** : `integrations/jinja2/renderer.py` (`DX-RENDER-ERROR-001`).

**Total** : 67 fichiers modifiés + 9 nouveaux + 2 supprimés.

---

## 6. Tests lancés

| Suite | Résultat |
|---|---|
| DX ciblés (7 fichiers) | **348 passed** en 5,92 s |
| Docs / landing / install (8 fichiers) | **287 passed** en 54,80 s |
| `tests/meta` (suite complète) | **6 107 passed, 4 skipped** en 4 min 21 s |
| Suite complète `pytest` | **15 051 passed, 6 skipped** en 5 min 28 s |

Détail des tests ciblés DX :

```text
tests/test_forge_run_command_001.py                       passed
tests/test_dev_server_autoreload_001.py                   passed
tests/test_api_inspectable_objects_convention_001.py      passed
tests/test_dx_typed_controller_skeletons_001.py           passed
tests/test_dx_render_missing_template_error_001.py        passed
tests/test_starter_bonjour_forge_001.py                   passed
tests/test_dx_debug_dump_html_001.py                      passed
```

Détail des tests ciblés docs/landing/install :

```text
tests/meta/test_doc_bonjour_forge.py                      passed
tests/meta/test_install_windows_wsl_docs_001.py           passed
tests/meta/test_install_core_dev_docs_001.py              passed
tests/meta/test_install_docs_structure_001.py             passed
tests/meta/test_landing_install_cards_001.py              passed
tests/meta/test_landing_post_2_2_refresh.py               passed
tests/meta/test_docs_landing_page_3_0_001.py              passed
tests/meta/test_landing_public_contract.py                passed
```

---

## 7. Tests échoués

**Aucun.** La suite globale passe à 15 051 tests (6 skipped), sans
échec, dans l'état actuel du working tree.

---

## 8. État landing

- Source canonique : `mvc/views/landing/index.html` — conserve les
  modifications manuelles validées comme contrat public actuel.
- Section Installation : 4 cards homogènes
  (`windows-wsl`, `pipx-user`, `core-dev`, `production`), aucune
  en `md:col-span-2`.
- Section starters : 7 cards (`welcome` + 01 à 04 + `communes-sejours`
  + `auth-mfa`).
- Section API Forge : 6 cards.
- Section modules opt-in : 4 cards
  (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`,
  `forge-mvc-stats`).
- Section positionnement + état (Forge 1.0.0-beta.10).
- Section contact : `mailto:forgemvc@gmail.com` statique
  (`LANDING-CONTACT-NAV-FORM-001` verrouillé par le test
  `test_public_contact_identity_001.py`).
- `forge sync:landing --check` : **OK** (`docs/index.html` et
  `docs/static/` synchronisés).

---

## 9. État docs/install

- Structure `docs/install/` en place avec `index.md`, `pipx.md`,
  `core-dev.md`, `windows-wsl.md`, `mariadb.md`, `vm-debian.md`,
  `windows.md`, `production.md` (`INSTALL-DOCS-STRUCTURE-001`).
- `docs/install/windows-wsl.md` : parcours complet WSL Ubuntu 24.04
  avec compte `forge_admin@localhost` + secrets `env/dev`
  (`INSTALL-WSL-DOCS-001` + `INSTALL-WSL-DOCS-FIELD-FIX-001`).
- `docs/install/core-dev.md` : consolidation 9 sections
  (`INSTALL-CORE-DEV-DOCS-AUDIT-001`).
- `docs/install/production.md` : entrée vers
  `wsgi-deployment.md` / `production-limits.md` / `deployment.md`.
- `docs/bonjour-forge.md` (anciennement `docs/15-minutes.md`) :
  parcours `forge run` → route → contrôleur → `Response.text` →
  `request.param` → `Response.debug` → `BaseController.render`
  (`DX-DOCS-BONJOUR-FORGE-CLOSE-001`).
- `docs/reference/http.md` mentionne la convention d'inspection
  des objets API (`API-INSPECTABLE-OBJECTS-CONVENTION-001`).
- `mkdocs build --strict` : **OK** (10,58 s, uniquement quelques
  INFO sur des liens relatifs sans cible MkDocs — non bloquants).

---

## 10. État roadmap

- `docs/roadmap/forge-roadmap.md` mentionne les 14 tickets attendus,
  tous marqués **livré**.
- Le ticket `BETA11-DX-CLOSING-AUDIT-001` n'apparaît pas encore dans la
  roadmap (à créer en clôture).
- Le ticket `RELEASE-BETA11-001` n'apparaît pas encore.
- Note historique de l'entrée `LANDING-PUBLIC-CONTRACT-REALIGN-001`
  réajustée pour refléter les vrais marqueurs des tests réalignés
  (modification non commitée).

---

## 11. Risques avant clôture beta 11

### 11.1 Bloquants

Aucun bloquant fonctionnel : la suite complète passe, les 5
validations canoniques passent, `forge sync:landing --check` est OK.

### 11.2 Non bloquants — à traiter dans `BETA11-DX-CLOSING-AUDIT-001`

- **Volume WIP non committé** : 67 fichiers modifiés + 9 nouveaux + 2
  supprimés. Le découpage en commits par ticket (un commit par ticket
  DX + un commit clôture pour landing/docs/install) reste à faire.
- **Cohérence Git ↔ roadmap** : actuellement la roadmap déclare des
  tickets « livré » dont les commits n'existent pas. Ce n'est
  acceptable que tant que la clôture beta 11 produit les commits avant
  la release.
- **Pas de tag `v1.0.0-beta.11`** : prérequis explicite de
  `RELEASE-BETA11-001`, dépendance de
  `BETA11-DX-CLOSING-AUDIT-001`.
- **Pas de section CHANGELOG `[1.0.0-beta.11]`** : à ajouter dans la
  clôture (référence : section `[1.0.0-beta.10]` de `CHANGELOG.md`).

### 11.3 Risques découverts pendant l'audit

- **Aucun** : pas de fichier orphelin, pas de test cassé, pas
  d'incohérence majeure entre roadmap et code, pas de lien cassé,
  pas de double définition.

---

## 12. Décision

**Décision : OK pour lancer `BETA11-DX-CLOSING-AUDIT-001`.**

Justifications :

1. Les 14 tickets DX / docs / install / landing sont **livrés** au
   sens code + tests + roadmap.
2. La suite complète (15 051 tests) passe sans échec.
3. Les 5 validations canoniques passent.
4. La landing actuelle (contrat public assumé) est synchronisée
   avec `docs/index.html`.
5. Aucun bloquant fonctionnel n'a été découvert.
6. Le seul travail restant (découpe et commit du WIP, ajout
   section CHANGELOG, tag) est exactement le périmètre du ticket
   suivant.

Aucun ticket correctif court n'est nécessaire avant
`BETA11-DX-CLOSING-AUDIT-001`.

---

## 13. Prochain ticket

**`BETA11-DX-CLOSING-AUDIT-001`** — clôture DX beta 11.

Périmètre attendu (résumé) :

1. Découper le WIP en commits par ticket (8 à 9 commits cohérents).
2. Ajouter la section `[1.0.0-beta.11]` à `CHANGELOG.md`.
3. Ajouter `BETA11-DX-CLOSING-AUDIT-001` à la roadmap (livré dès
   réalisation).
4. Préparer (sans poser) le tag `v1.0.0-beta.11`.
5. Audit pré-release léger (`pytest`, `compileall`, `ruff`,
   `mkdocs --strict`, `git diff --check`, `forge sync:landing --check`)
   reproduisant les résultats de cet audit.
6. Recommandation explicite GO / NO-GO pour `RELEASE-BETA11-001`.

Ticket suivant après celui-là : **`RELEASE-BETA11-001`**.
