# Spec d'exécution — `REMOVE-MEDIA-PKG-001` (ticket 7, ADR-018)

> **Statut : préparé, en attente.** Ce document est un **brouillon de spec**
> (page hors-nav). Il décrit l'exécution du dernier ticket de l'extraction
> `forge-mvc-images` (ADR-018). **Il n'est pas exécutable tant que la
> précondition de publication n'est pas levée.**

## Précondition bloquante

`forge-mvc-images` doit être **publié sur PyPI** (action de release, mainteneur).

Tant que ce n'est pas fait :

- on ne peut pas dire aux utilisateurs `pip install --pre forge-mvc-images`
  (les garde-fous `test_optin_pypi_publish_prepare_001`,
  `test_optin_cli_verbs_001`, `test_optins_count_consistency_001` exigent qu'un
  opt-in officiel du catalogue soit publiable) ;
- on ne peut pas renommer la clé catalogue `media` → `images` ni supprimer
  `forge-mvc-media` (encore la cible d'installation documentée).

Étapes de release attendues avant ce ticket :

1. Aligner la version de `packages/forge-mvc-images/pyproject.toml` sur le core.
2. `python -m build packages/forge-mvc-images` puis publication PyPI (`twine`).
3. Mettre à jour `release-policy.md` : `forge-mvc-images` passe de « non publié »
   à « publié sur PyPI depuis `1.0.0-beta.x` ».

## Ce que fait le ticket

1. Renomme l'opt-in officiel **`media` → `images`** dans le catalogue CLI.
2. **Supprime** `packages/forge-mvc-media/` (paquet + shims transitoires).
3. Repointe les derniers consommateurs de `forge_mvc_media` (tests fonctionnels,
   contrats opt-in, docs) vers `forge_mvc_images`.
4. Finalise la documentation et `CLAUDE.md` (retrait de la mention « shim
   transitoire »).
5. Entrée `CHANGELOG`.

## Ce qu'il ne fait pas

- Aucune nouvelle fonctionnalité image (cf. tickets `IMAGES-FEATURE-*`).
- Ne touche pas au comportement runtime de `forge_mvc_images` (déjà en place).
- Ne ré-introduit pas d'alias `forge-mvc-media` (convention pré-1.0 : suppression
  sèche).

## Fichiers concernés (audit au moment de la préparation)

> Listes établies par audit ; à re-valider au moment de l'exécution
> (`grep -rn "forge_mvc_media\|forge-mvc-media" --include=*.py` + docs).

### A. Code

- `forge_cli/optins/catalog.py` — entrée `"media"` → `"images"`
  (`"images", "forge-mvc-images", "forge_mvc_images", KIND_LIBRARY, "…"`).
- `packages/forge-mvc-media/` — **suppression du dossier entier** (incl.
  `forge_mvc_media/__init__.py`, `media_repository.py`, `media_gallery.py` qui
  sont des shims depuis `IMAGES-MOVE-APPLICATIVE-001`).

### B. CI

- `.github/workflows/tests.yml` — retirer `packages/forge-mvc-media` de la
  boucle « Build optional distributions ».

### C. Tests fonctionnels — repointer `forge_mvc_media` → `forge_mvc_images`

- `tests/test_media_attach.py`
- `tests/test_media_delete.py`
- `tests/test_media_gallery.py`
- `tests/test_media_integration.py`
- `tests/test_media_repository.py`

Pour chacun : remplacer l'import `forge_mvc_media` par `forge_mvc_images` et la
garde `pytest.importorskip("forge_mvc_media")` par `importorskip("forge_mvc_images")`.

### D. Contrats opt-in / packaging — remplacer `forge-mvc-media` par `forge-mvc-images`

- `tests/meta/test_pypi_classifiers_001.py` (table `EXPECTED_CLASSIFIERS`)
- `tests/meta/test_optin_pypi_publish_prepare_001.py`
- `tests/meta/test_optins_count_consistency_001.py`
- `tests/meta/test_packages_optin_no_pypi_001.py`
- `tests/meta/test_optin_pypi_names_check_001.py`
- `tests/meta/test_version_sync_optin_extras_001.py`
- `tests/meta/test_package_lock_sync_001.py`
- `tests/release/test_optin_extras_sync_001.py`
- `tests/release/test_packaging_multi_dist_001.py`
- `tests/meta/test_release_current_version_001.py`
- `tests/test_optin_cli_verbs_001.py` — `optin_names()` attend `images` à la
  place de `media` (liste figée).
- `tests/test_optin_cli_engine_001.py`, `tests/test_optin_kind_adapter_001.py`.

### E. Contrats d'import / sweep — remplacer `forge_mvc_media` par `forge_mvc_images`

- `tests/meta/test_pytest_core_only_contract_001.py` (clé `OPTIN_MODULES`)
- `tests/meta/test_optin_tests_importorskip_001.py` (set `_OPTIN_MODULES`)
- `tests/meta/test_docs_imports_validity_sweep_001.py` (`_FRAMEWORK_ROOTS`)
- `tests/meta/test_docs_python_examples_executable_001.py`

### F. Garde-fous d'ère MEDIA — à réécrire ou retirer

Ces tests vérifient la structure du paquet `forge-mvc-media` (qui disparaît) ou
l'invariant « code applicatif dans forge_mvc_media » (déjà inversé par
`IMAGES-MOVE-APPLICATIVE-001`). Décider au cas par cas : généraliser vers
`forge_mvc_images` (préféré) ou retirer avec test d'absence.

- `tests/meta/test_optin_media_build_001.py` (CI build du paquet média)
- `tests/meta/test_media_extract_package_scaffold_001.py`
- `tests/meta/test_media_repository_move_001.py`
- `tests/meta/test_media_core_boundary_audit_001.py`
- `tests/meta/test_media_crud_integration_optin_001.py` (parties README/pyproject
  `forge-mvc-media`)
- `tests/meta/test_media_docs_migration_001.py`
- Ajouter un **test d'absence** : `assert not Path("packages/forge-mvc-media").exists()`
  (convention de suppression).

### G. Tests générateur — faux positifs à vérifier

`tests/test_make_crud_media*.py` matchent « media » via les **noms d'entités /
rôles**, pas la clé opt-in. Vérifier qu'aucun ne référence encore
`forge_mvc_media` après le repointage du delegate (déjà fait en partie). Les
faux modules runtime monkeypatchent déjà `forge_mvc_images`.

### H. Documentation (hors `history/`) — `forge-mvc-media` → `forge-mvc-images`

- `README.md` (table des paquets, lien PyPI)
- `docs/install/core-dev.md`, `docs/install/index.md`
- `docs/reference/vocabulaire-opt-in.md`, `docs/reference/cli-commands.md`,
  `docs/reference/api.md`
- `docs/features/front.md`, `docs/features/media.md`
- `docs/release/release-policy.md`, `docs/release/compatibility.md`,
  `docs/release/stability-contract.md`
- `docs/iot/architecture.md` (mention comparative)
- `docs/roadmap/forge-roadmap.md` (entrée ticket 7 « livré »)
- `docs/adr/016-opt-in-unification.md` (référence catalogue, si pertinent)
- **Ne pas toucher** `docs/adr/018-image-module-extraction.md` ni `docs/history/**`
  (décrivent l'état historique / la décision).

### I. `CLAUDE.md` (fichier protégé — mainteneur ou hook levé)

- §1 / §3 : retirer la ligne « `forge-mvc-media` — shim transitoire … ».
- §9 : note `packages/` repasse de 8 à 7 sous-dossiers (retrait de
  `forge-mvc-media`).

### J. `CHANGELOG.md`

Entrée résumant l'extraction `forge-mvc-images` (ADR-018) et la suppression de
`forge-mvc-media`.

## Stratégie d'implémentation (ordre suggéré)

1. **Précondition** : confirmer `forge-mvc-images` publié + `release-policy.md`
   à jour.
2. Catalogue (`catalog.py`) : `media` → `images`.
3. Repointer les contrats opt-in / packaging (section D) et import (E) vers
   `forge-mvc-images` / `forge_mvc_images`.
4. Repointer les tests fonctionnels (C).
5. Réécrire / retirer les garde-fous d'ère MEDIA (F) + test d'absence.
6. Supprimer `packages/forge-mvc-media/` (`git rm -r`).
7. Retirer le build CI média (B).
8. Documentation (H) + `CLAUDE.md` (I) + `CHANGELOG` (J).
9. Roadmap : marquer `REMOVE-MEDIA-PKG-001` livré.

Faire la suppression du dossier (étape 6) **après** avoir repointé tous les
importeurs, sinon la suite casse en collecte.

## Validations attendues

- `python -m pytest -x -q` — suite complète, 0 régression.
- `python -m compileall -q .`
- `ruff check .`
- `mkdocs build --strict`
- `git diff --check`
- Vérifier qu'aucun `forge_mvc_media` / `forge-mvc-media` ne subsiste hors
  `docs/history/**` et `docs/adr/018-*` :
  `grep -rn "forge_mvc_media\|forge-mvc-media" --include=*.py . | grep -v history`
  doit être vide (hors tests d'absence).

## Limites restantes après le ticket

- L'historique (`docs/history/**`, `CHANGELOG`) conserve les mentions
  `forge-mvc-media` (mémoire brute — ne pas réécrire).
- Les tickets `IMAGES-FEATURE-*` (profils configurables, WebP, crop, qualité…)
  restent à venir, sur la base propre obtenue.

## Charte appliquée

- Principe 1 (séparer framework / métier) et 8 (noyau minimal) : aboutissement
  de l'extraction.
- Principe 11 (une seule façon officielle) : `forge-mvc-images` devient l'unique
  propriétaire ; `forge-mvc-media` disparaît.
- Règle C (rupture d'API publique) : acceptable en bêta pré-1.0, sans alias.
- Convention de tests : tests d'absence après suppression (section F).
