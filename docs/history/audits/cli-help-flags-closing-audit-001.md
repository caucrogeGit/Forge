# CLI-HELP-FLAGS-CLOSING-AUDIT-001 — Clôture du chantier `--help`

## Résumé

Audit final du chantier `CLI-HELP-FLAGS-*` (dispatcher + 10 tickets
d'enrichissement). **62 commandes** dispatchées par `forge.py` ont été
classifiées :

| Catégorie | Nombre | Part |
|---|---:|---:|
| `AIDE_RICHE` — entrée dans `HELP_TEXTS_RICH` | **45** | 73 % |
| `AIDE_NATIVE_ARGPARSE` — `auth:user:*` | **8** | 13 % |
| `AIDE_NATIVE_MANUELLE` — `make:entity`, `make:relation`, `db:apply`, `migration:make`, `starter:build`, `module:*` | **9** | 14 % |
| `CAS_SPECIAL_DOCUMENTE` — aucune aujourd'hui | 0 | 0 % |
| `MANQUANT` | **0** | 0 % |

**Le chantier `--help` est clos.** Aucune commande connue ne tombe
dans le gabarit générique fallback. Le filet de sécurité reste en
place pour l'avenir.

---

## Méthode

1. Recensement des commandes via parsing AST de `forge.py` : tous les
   `if command == "…"` et `if command in (…)` sont parcourus, les
   chaînes littérales sont extraites. Cette extraction est vérifiée
   par `TestForgePyMatchesAuditedList::test_dispatched_commands_match_audited_list`.
2. Classification de chaque commande en l'une des 4 catégories
   ci-dessus (test `test_categories_partition_dispatched_commands`).
3. Vérification que les catégories sont disjointes (test
   `test_categories_are_disjoint`).
4. Vérification runtime : chaque commande riche retourne 0 avec
   `--help` et `-h` ; chaque commande argparse imprime
   `usage: forge <cmd>` minuscule ; chaque commande manuelle retourne 0.
5. Garde-fou des 6 commandes critiques (`db:init`, `mail:init`,
   `i18n:init`, `upload:init`, `media:init`, `deploy:init`) : aucun
   marqueur d'effet de bord (`[OK]`, `[ERREUR]`, `Provisioning`,
   `[PRÉSERVÉ]`, `Dossier prêt`) dans la sortie de `--help`/`-h`.

---

## Commandes auditées (62)

Liste alphabétique. Source : `forge.py` au commit de clôture.

| Commande | Type | Source |
|---|---|---|
| `auth:doctor` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `auth:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `auth:list-sql` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `auth:status` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `auth:user:create` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `auth:user:disable` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `auth:user:enable` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `auth:user:list` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `auth:user:password` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `auth:user:role:add` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `auth:user:role:remove` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `auth:user:roles` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `auth:user:show` | AIDE_NATIVE_ARGPARSE | `forge_cli/auth.py` |
| `build:model` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `check:model` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `db:apply` | AIDE_NATIVE_MANUELLE | `forge.py` (lignes 661-666) |
| `db:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `deploy:check` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `deploy:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `docs:pdf` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `doctor` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `entity:validate` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `i18n:check` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `i18n:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `js:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `mail:doctor` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `mail:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `mail:logs` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `mail:render` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `mail:test` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:crud` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:entity` | AIDE_NATIVE_MANUELLE | `forge_cli/entities/make_entity.py:289` |
| `make:pivot-crud` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:public-contact` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:public-form` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:public-list` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:public-page` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:public-show` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `make:relation` | AIDE_NATIVE_MANUELLE | `forge_cli/entities/make_relation.py` |
| `media:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `migration:apply` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `migration:diff` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `migration:make` | AIDE_NATIVE_MANUELLE | `forge_cli/entities/migrations.py:460` |
| `migration:status` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `module:files` | AIDE_NATIVE_MANUELLE | `forge_cli/modules.py` |
| `module:install` | AIDE_NATIVE_MANUELLE | `forge_cli/modules.py` |
| `module:list` | AIDE_NATIVE_MANUELLE | `forge_cli/modules.py` |
| `module:routes` | AIDE_NATIVE_MANUELLE | `forge_cli/modules.py` |
| `new` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `project:audit` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `project:check` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `rbac:audit` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `rbac:validate` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `routes:list` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `schema:doctor` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `schema:list` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `starter:build` | AIDE_NATIVE_MANUELLE | `forge_cli/starters/__init__.py:34` |
| `starter:list` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `sync:entity` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `sync:landing` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `sync:relations` | AIDE_RICHE | `HELP_TEXTS_RICH` |
| `upload:init` | AIDE_RICHE | `HELP_TEXTS_RICH` |

---

## Couverture finale

```
62 commandes dispatchées (forge.py)
├── 45 AIDE_RICHE             (HELP_TEXTS_RICH)
├──  8 AIDE_NATIVE_ARGPARSE   (auth:user:*)
├──  9 AIDE_NATIVE_MANUELLE   (make:entity, make:relation, db:apply,
│                              migration:make, starter:build, module:*)
├──  0 CAS_SPECIAL_DOCUMENTE
└──  0 MANQUANT
```

`62 = 45 + 8 + 9 + 0 + 0`. ✓

---

## Aides riches (45)

Couvertes par les 10 tickets d'enrichissement :

| Ticket | Commandes |
|---|---|
| `CLI-HELP-FLAGS-INIT-COMMANDS-001` | `db:init`, `mail:init`, `i18n:init`, `upload:init`, `media:init`, `deploy:init` (6) |
| `CLI-HELP-FLAGS-SCHEMA-RBAC-001` | `schema:list`, `schema:doctor`, `rbac:validate`, `rbac:audit` (4) |
| `CLI-HELP-FLAGS-PUBLIC-PAGES-001` | `make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`, `make:public-contact` (5) |
| `CLI-HELP-FLAGS-MAIL-001` | `mail:test`, `mail:render`, `mail:doctor`, `mail:logs` (4) |
| `CLI-HELP-FLAGS-MIGRATIONS-001` | `migration:status`, `migration:apply`, `migration:diff` (3) |
| `CLI-HELP-FLAGS-PROJECT-DIAGNOSTICS-001` | `doctor`, `project:check`, `project:audit`, `routes:list` (4) |
| `CLI-HELP-FLAGS-ENTITY-MODEL-CRUD-001` | `entity:validate`, `build:model`, `check:model`, `make:crud`, `make:pivot-crud` (5) |
| `CLI-HELP-FLAGS-AUTH-COMPLETION-001` | `auth:init`, `auth:doctor`, `auth:status`, `auth:list-sql`, `auth:user:list` (5) |
| `CLI-HELP-FLAGS-REMAINING-MINOR-001` | `new`, `starter:list`, `sync:entity`, `sync:relations`, `sync:landing`, `js:init`, `docs:pdf`, `i18n:check`, `deploy:check` (9) |

Total : 45.

---

## Aides natives préservées (17)

### Argparse natif (8)

Toutes les `auth:user:*` non listées dans `HELP_TEXTS_RICH` :
`auth:user:create`, `auth:user:show`, `auth:user:disable`,
`auth:user:enable`, `auth:user:password`, `auth:user:role:add`,
`auth:user:role:remove`, `auth:user:roles`.

Le dispatcher central ne les intercepte pas (absence d'entrée dans
`HELP_DESCRIPTIONS`/`HELP_TEXTS_RICH`). Argparse imprime
`usage: forge auth:user:* [-h] …` et exit 0.

### Manuelle (9)

| Commande | Lieu du `if "--help" in args:` |
|---|---|
| `make:entity` | `forge_cli/entities/make_entity.py:289` |
| `make:relation` | `forge_cli/entities/make_relation.py` (analogue) |
| `db:apply` | `forge.py:661-666` (interception au dispatcher) |
| `migration:make` | `forge_cli/entities/migrations.py:460-472` |
| `starter:build` | `forge_cli/starters/__init__.py:34-44` |
| `module:list` | `forge_cli/modules.py` |
| `module:install` | `forge_cli/modules.py` |
| `module:files` | `forge_cli/modules.py` |
| `module:routes` | `forge_cli/modules.py` |

Garde-fou runtime : `TestNativeCommandsKeepTheirHelp` vérifie que ces
aides natives restent natives (pas écrasées par le gabarit central).

---

## Fallback générique

Le fallback générique de `format_command_help()` produit le gabarit
court (`Usage:` / `Description:` / `Options:` + renvoi à
`cli-commands.md`) **uniquement** si :

1. la commande est présente dans `HELP_DESCRIPTIONS` ;
2. ET absente de `HELP_TEXTS_RICH`.

Aujourd'hui, les 45 entrées de `HELP_DESCRIPTIONS` sont aussi dans
`HELP_TEXTS_RICH`. Le fallback **n'est plus atteint** pour aucune
commande connue.

Le test `TestSafetyNetDuplication::test_rich_entries_also_in_descriptions`
verrouille cette propriété.

---

## Décision sur `HELP_DESCRIPTIONS` / `HELP_TEXTS_RICH`

**Option A retenue — conserver la duplication comme filet de sécurité.**

Justification :

- Si une future commande est ajoutée à `HELP_DESCRIPTIONS` (par
  étourderie ou pas étape) sans entrée riche, elle reçoit immédiatement
  une aide minimale et le dispatcher l'intercepte avant tout effet de
  bord. Sans le filet, il faudrait ajouter en même temps l'entrée riche
  ET mettre à jour les natives → friction inutile.
- La duplication est verrouillée par
  `TestSafetyNetDuplication::test_descriptions_keys_match_rich_keys` :
  toute divergence future est détectée.
- Coût mémoire/maintenance négligeable (45 chaînes d'une ligne).
- Documenté explicitement dans le docstring de
  `forge_cli/help_dispatch.py` et dans un commentaire au-dessus de
  `HELP_DESCRIPTIONS`.

L'Option B (supprimer la duplication) a été écartée parce qu'elle
augmenterait la charge cognitive sans gain réel.

---

## Tests ajoutés

**Nouveau fichier** :
`tests/meta/test_cli_help_flags_closing_audit_001.py` — **125 tests** :

- `TestEveryDispatchedCommandIsClassified` (3) — partition des
  catégories, disjonction, pas d'entrée orpheline dans `HELP_TEXTS_RICH`.
- `TestForgePyMatchesAuditedList` (1) — AST de `forge.py` ↔
  `ALL_DISPATCHED_COMMANDS`.
- `TestRichCommandsAllExitZero` (90 = 2 × 45) — `--help` ET `-h` exit 0
  pour chaque commande riche.
- `TestNativeCommandsKeepTheirHelp` (17 = 8 + 9) — argparse imprime
  `usage:` minuscule sans gabarit central ; manuelles exit 0.
- `TestCriticalCommandsRemainSafe` (12 = 2 × 6) — `--help` ET `-h` ne
  déclenchent aucun marqueur d'effet de bord sur les 6 commandes
  critiques.
- `TestSafetyNetDuplication` (2) — verrouillage de la duplication
  `HELP_DESCRIPTIONS` ↔ `HELP_TEXTS_RICH`.

**Total chantier `CLI-HELP-FLAGS-*`** :

| Fichier de test | Tests |
|---|---:|
| `test_cli_help_flags_dispatcher_001.py` | 25 |
| `test_cli_help_flags_init_commands_001.py` | 48 |
| `test_cli_help_flags_schema_rbac_001.py` | 32 |
| `test_cli_help_flags_public_pages_001.py` | 40 |
| `test_cli_help_flags_mail_001.py` | 33 |
| `test_cli_help_flags_migrations_001.py` | 25 |
| `test_cli_help_flags_project_diagnostics_001.py` | 35 |
| `test_cli_help_flags_entity_model_crud_001.py` | 43 |
| `test_cli_help_flags_auth_completion_001.py` | 50 |
| `test_cli_help_flags_remaining_minor_001.py` | 81 |
| `test_cli_help_flags_closing_audit_001.py` | **125** |
| **Total** | **537** |

Le test global pré-existant `test_forge_help_coverage_001.py` continue
de passer (19 tests).

---

## Limites restantes

1. **Aides natives manuelles non testées en contenu** — `make:entity`,
   `make:relation`, `db:apply`, `migration:make`, `starter:build`,
   `module:*` sont testées en code de sortie uniquement
   (`test_manual_help_returns_zero`), pas en présence de sections
   spécifiques. La granularité de leur aide reste à l'appréciation
   du mainteneur de chaque module. Aucun ticket ne le réclame
   aujourd'hui.
2. **Pas de vérification que `forge --help` (global) cite toutes les
   commandes dispatchées** — c'est le rôle existant de
   `tests/meta/test_forge_help_coverage_001.py`, qui vérifie l'inverse
   (toute commande de `forge --help` est documentée dans
   `cli-commands.md`).
3. **Pas de migration `argparse` généralisée** — délibéré : la
   convention « parseur manuel + filet `HELP_TEXTS_RICH` » est plus
   pédagogique pour Forge et compatible avec l'existant. Une éventuelle
   migration argparse serait un autre chantier (`CLI-ARGPARSE-MIGRATION-001`).
4. **Le gabarit générique fallback n'est plus exercé par aucun
   utilisateur connu** — il existe pour les commandes futures. Test
   unitaire spécifique non ajouté ici (le code est trivial, 10 lignes,
   et l'invariant principal — pas d'effet de bord — est testé via
   les commandes critiques).

---

## Conclusion

Le chantier **`CLI-HELP-FLAGS-*` est officiellement clos**.

- 62 commandes audités, 100 % classifiées, 0 manquant.
- 45 commandes ont une aide riche multi-sections, 17 conservent leur
  aide native, aucune ne tombe dans le fallback générique.
- 537 tests garantissent que toute régression future (nouvelle commande
  non classée, écrasement d'une aide native, retour de marqueur
  d'effet de bord sur les 6 critiques, divergence
  `HELP_DESCRIPTIONS`/`HELP_TEXTS_RICH`) sera détectée immédiatement.
- Le filet de sécurité `HELP_DESCRIPTIONS` est conservé et documenté.

La roadmap bêta 9 peut reprendre sur les sujets hors `--help` (audits
sécurité/runtime restants).
