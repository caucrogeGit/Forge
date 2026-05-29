# Audit pré-release Forge 1.0.0-beta.12

> Ticket : `RELEASE-BETA12-PRE-AUDIT-001`. Audit **documentaire** — aucun
> changement fonctionnel, aucun bump de version, aucun tag, aucune
> publication. Ce document **dit si on est prêt** ; il ne fait pas la
> release. Instantané pris après `712d008` (`OPTINS-CLOSING-AUDIT-001`).

!!! success "Suivi — RELEASE-BETA12-FULLSUITE-FIX-001 (résolu)"
    Le verdict ci-dessous (**NO-GO**, 56 échecs) est l'instantané au
    moment de l'audit. Le ticket de correction `RELEASE-BETA12-FULLSUITE-FIX-001`
    a ramené la suite complète à **0 échec** (`16613 passed, 7 skipped`) :
    les ~41 échecs introduits par les chantiers IoT/opt-ins ont été
    corrigés (allow-lists `forge_mvc_iot`/`optins`, `importorskip` dans
    les tests IoT, `release-local.md` starter 15, classifier PyPI
    `forge-mvc-iot`, version `{{forge_version}}` dans `doctor.md`), et la
    baseline pré-existante (migration `forgemvc.com`, README simplifié) a
    été traitée en alignant les garde-fous stale sur l'état canonique
    (sans les supprimer). La voie est libre pour `RELEASE-BETA12-001`.

## Verdict

**NO-GO** pour `1.0.0-beta.12` en l'état.

La suite **ciblée** (IoT, opt-ins, garde-fous CLI) et les validations
standard (`compileall`, `ruff`, `mkdocs --strict`, `git diff --check`)
sont **vertes**. Mais la **suite complète** révèle **56 échecs**, dont
**~41 ont été introduits par les chantiers IoT + opt-ins eux-mêmes** et
n'ont jamais été détectés parce que chaque ticket ne lançait que ses
tests *ciblés*, jamais `pytest` complet. Ces échecs ne sont **pas
fonctionnels** (allow-lists de tests méta, compteurs de doc, imports
d'exemples), mais ils doivent être **résolus avant** une release. S'y
ajoutent **~15 échecs de baseline** de consolidation (README/landing/
version/packaging) antérieurs à IoT.

→ Ouvrir un (ou des) **ticket(s) correctif(s)** avant `RELEASE-BETA12-001`.

## Résumé exécutif

- Version courante : **`1.0.0b11`** (beta.11) — pas encore bumpée (normal).
- Branche `main`, working tree **propre**.
- Blocs livrés depuis beta.11 : **Forge IoT** (30 tickets) + **opt-ins
  projet** (6 tickets) + audits de clôture.
- Tests **ciblés** : IoT **776 passed**, opt-ins **119 passed**, garde-fous
  CLI **160 passed**. Validations standard **OK**.
- Suite **complète** : **56 failed, 16517 passed, 7 skipped**.
- **Découverte clé** : ~41 des 56 échecs viennent des chantiers IoT/opt-ins
  (jamais vus car seuls les tests ciblés étaient lancés par ticket).

## État Git

```text
branche : main
status  : propre
version : 1.0.0b11  (pyproject.toml)
```

Commits récents (extrait) : `712d008` OPTINS-CLOSING-AUDIT-001 →
`0cafbe1` IOT-CLOSING-AUDIT-001 → bloc opt-ins (`2cc45e2`…`efc2f70`) →
bloc IoT. Les commits IoT et opt-ins sont bien présents.

## Tickets livrés depuis beta.11

- **Forge IoT** : `IOT-ARCHITECTURE-001` → `IOT-CLI-COMMANDS-DOCS-REFERENCE-001`
  + `IOT-CLOSING-AUDIT-001` (voir [audit de clôture IoT](audit-iot-closing.md)).
- **Opt-ins projet** : `OPTINS-PROJECT-STRUCTURE-001`,
  `OPTINS-IOT-PROJECT-BRIDGE-001`, `OPTINS-CLI-ENABLE-AUDIT-001`,
  `OPTINS-CLI-ENABLE-IOT-001`, `OPTINS-CLI-ENABLE-ROUTES-APPLY-001`,
  `OPTINS-CLI-LIST-001`, `OPTINS-CLOSING-AUDIT-001` (voir
  [audit de clôture opt-ins](audit-optins-closing.md)).

## Bloc Forge IoT

Paquet **`forge-mvc-iot`** : contrat MQTT, subscriber, stockage
`iot_events`, API HTTP + Bearer token, TLS, CLI (`iot:doctor`/`init`/
`listen`/`simulate`), starter `welcome-iot`. Tests ciblés
(`tests/test_iot_*.py` + `tests/meta/test_iot_*.py`) : **776 passed**.
Bloc fonctionnellement sain.

## Bloc opt-ins projet

Couche `optins/` + commandes **`forge optin:enable iot`** (dry-run par
défaut, `--apply`) et **`forge optin:list`** (lecture seule). Tests
ciblés (`tests/test_optins_*.py` + `tests/meta/test_optins_*.py`) :
**119 passed**. Bloc fonctionnellement sain.

## CLI et commandes

Garde-fous `test_forge_help_coverage_001` + `test_cli_help_flags_closing_audit_001`
**160 passed** : les commandes IoT (`iot:*`) et opt-ins (`optin:enable`,
`optin:list`) sont dispatchées, documentées dans `cli-commands.md` et
classées. Pas de régression CLI.

## Documentation

`mkdocs build --strict` : **OK** (rc 0). Les pages IoT (TLS, Bearer
token) et opt-ins sont dans la nav et se construisent. **Mais** la suite
de tests *méta docs* révèle des incohérences (voir Tests) : pages doc
non reconnues par des allow-lists, et `docs/release-local.md` non mis à
jour pour le starter 15 (`welcome-iot`).

## Tests

| Lot | Résultat |
|---|---|
| `compileall -q .` | **OK** |
| `ruff check .` | **OK** |
| `mkdocs build --strict` | **OK** |
| `git diff --check` | **OK** |
| IoT ciblé | **776 passed** |
| opt-ins ciblé | **119 passed** |
| garde-fous CLI | **160 passed** |
| **suite complète `pytest`** | **56 failed, 16517 passed, 7 skipped** |

### Classement des 56 échecs

**A. Introduits par les chantiers IoT / opt-ins / welcome-iot (~41)** —
non fonctionnels, jamais vus car les tickets ne lançaient que les tests
ciblés :

- **`test_docs_imports_validity_sweep_001` (36)** : cause **unique et
  triviale** — `forge_mvc_iot` **absent** de `_FRAMEWORK_ROOTS` (alors
  que ses 5 paquets frères `forge_mvc_mfa/rbac/workflow/stats/media` y
  sont) et `optins` absent de `_USER_PROJECT_ROOTS`. Touche
  `storage-events.md`, `mqtt-subscriber.md`, `http-api.md`,
  `configuration.md`, `index.md` (IoT) + `optins-project-structure.md`,
  `optins-cli-enable-audit.md`, `index.md` (opt-ins).
- **`test_docs_python_examples_executable_001::test_all_imports_resolve`
  (1 / 6 imports)** : exemples `optins.registry` / `optins.iot.routes`
  dans 3 pages (audit/structure opt-ins + `welcome-iot`) non importables
  — `optins.*` est du **code projet** (généré chez l'utilisateur), à
  traiter comme `mvc.*` (import non résolu = normal).
- **`test_pytest_core_only_contract_001::test_no_unknown_top_level_imports`
  (1)** : `forge_mvc_iot` importé en tête de **19 fichiers de test** IoT,
  non présent dans l'allow-list de ce contrat.
- **`test_docs_release_local_starters_001` (3)** : `docs/release-local.md`
  ne référence pas le **starter 15 (`welcome-iot`)** et annonce encore
  « 14 starters » (il y en a 15).

**B. Baseline de consolidation, antérieure à IoT (~15)** — non liée aux
chantiers IoT/opt-ins (README/landing/version/packaging) :

- `test_landing_install_cards_001` (4), `test_publication_2_0_version_001`
  (2), `test_getting_started_3_0_001` (2), `test_security_md_001` (1),
  `test_readme_runtime_deps_001` (1), `test_pypi_classifiers_001` (1),
  `test_tls_defaults_001` (1, README https), `test_starter_cli.py`
  (1, domaine `caucrogegit.github.io` vs `forgemvc.com`),
  `test_consolidation_profiles_001` (1), `test_docs_version_variable_001`
  (1, version en dur dans la doc active — à confirmer).

## Packaging

`packages/forge-mvc-iot/` existe avec son `pyproject.toml`. **Point à
vérifier avant release** : `forge-mvc-iot` est-il bien inclus dans le
plan de publication PyPI au même titre que `forge-mvc-rbac/workflow/
stats/mfa/media` ? (hors périmètre de cet audit ; à traiter dans
`RELEASE-BETA12-001`). `test_pypi_classifiers_001` échoue (baseline) — à
revoir lors de la prépa packaging.

## Sécurité

IoT : Bearer token optionnel sur l'API HTTP, TLS MQTT branché (`tls_set`,
sans mTLS), mot de passe / chemin CA masqués. Pas de secret en clair
introduit. `optin:list` est lecture seule, `optin:enable` ne fait pas
d'écrasement silencieux. Rien de bloquant côté sécurité dans les
chantiers audités.

## Dettes restantes

| Dette | Nature | Bloquant release ? |
|---|---|---|
| `forge_mvc_iot` absent des allow-lists de tests méta (sweep + core-only) | test (trivial) | **oui** (suite rouge) |
| `optins` non reconnu (sweep + python-examples) | test (trivial) | **oui** |
| `docs/release-local.md` pas à jour (starter 15) | doc | **oui** |
| ~15 échecs baseline README/landing/version/packaging | doc/consolidation | **à trancher** |
| `forge-mvc-iot` dans le plan PyPI | packaging | à vérifier en `RELEASE-BETA12-001` |
| version encore `b11` | normal (pas de bump ici) | non |
| changelog beta.12 non préparé | normal (RELEASE-BETA12-001) | non |

## Points bloquants

1. **Suite complète rouge** (56 échecs). Une release ne doit pas partir
   sur une suite rouge.
2. **~41 échecs introduits par IoT/opt-ins** non détectés faute de
   `pytest` complet par ticket — à corriger (tous mécaniques).
3. **Process** : la discipline « tests ciblés par ticket » a laissé
   s'accumuler des régressions de suite complète. À intégrer dans la
   prépa release (lancer `pytest` complet avant tout tag).

## Points non bloquants

- Validations standard (`compileall`, `ruff`, `mkdocs --strict`,
  `git diff --check`) vertes.
- Blocs IoT et opt-ins fonctionnellement sains (tests ciblés verts).
- Pas de régression CLI ni de fuite de secret.

## Décision GO / NO-GO

**NO-GO** pour `1.0.0-beta.12` tant que la suite complète n'est pas
remise au vert (ou la baseline explicitement classée et acceptée).

Plan recommandé avant `RELEASE-BETA12-001` :

1. **Ticket correctif `RELEASE-BETA12-FULLSUITE-FIX-001`** (test/doc, non
   fonctionnel) :
   - ajouter `forge_mvc_iot` à `_FRAMEWORK_ROOTS`
     (`test_docs_imports_validity_sweep_001`) et à l'allow-list de
     `test_pytest_core_only_contract_001` ;
   - reconnaître `optins` comme racine projet utilisateur
     (sweep + `test_docs_python_examples_executable_001`) ;
   - mettre à jour `docs/release-local.md` (starter 15 `welcome-iot`,
     « 15 starters », commande `--dry-run`).
2. **Triage de la baseline (~15)** : décider page par page
   (README version, landing cards, `SECURITY.md`, classifiers PyPI…) —
   corriger ou acter comme dette connue documentée.
3. Relancer **`pytest` complet** → exiger **0 échec** (ou baseline
   explicitement listée) avant d'ouvrir `RELEASE-BETA12-001`.

Cet audit **ne corrige rien** : il classe et tranche. Aucun code
fonctionnel, aucun test, aucune doc applicative n'est modifié ici.
