# ADR-024 — Bootstrap par squelette dédié et dépendance core via pip

## Statut

Accepté — Forge 1.0.0-beta.13 (ticket `BOOTSTRAP-SKELETON-ADR-024`).

---

## Date

2026-06-07

---

## Contexte

`forge new <NomProjet>` doit produire un projet Forge **nu** (ADR-023 :
`forge new` ne construit aucun starter). Or l'implémentation actuelle ne
produit pas un projet nu.

### État avant la décision

1. **Le squelette est le dépôt entier.** `_clone_skeleton` exécute
   `git clone --branch v1.0.0-beta.13 --depth=1 https://github.com/caucrogeGit/Forge.git`.
   Le projet généré hérite donc de **tout le monorepo** : `core/`,
   `forge_cli/`, `integrations/`, `packages/`, `tests/`, `docs/`,
   `mkdocs.yml`, `pyproject.toml`, et le `mvc/` de dogfooding (l'application
   de démonstration qui sert à développer Forge).

2. **Le `mvc/` livré est l'app de démo.** Même si `mvc/routes.py` est neutre
   (une seule route `/`, garde-fou `tests/test_skeleton_routes_neutral_001.py`),
   les *fichiers* de démonstration arrivent sur le disque sans être routés :
   `auth_controller.py`, `mfa_challenge_controller.py`, `welcome_controller.py`,
   `entities/media/`, `mail/templates/`, `models/auth_model.py`, et surtout
   `views/landing/index.html` (la landing marketing de Forge, source de
   `forge sync:landing`).

3. **Le projet importe le `core/` cloné, pas le paquet.** Le `requirements.txt`
   du squelette ne dépend pas de `forge-mvc` : il ne liste que les libs
   runtime (`mariadb`, `python-dotenv`, `jinja2`, `argon2-cffi`,
   `jsonschema`). Le projet généré importe donc le `core/` présent localement
   grâce au clone, ce qui justifie a posteriori le clone du dépôt entier.

Ce modèle contredit les principes 1 (séparer framework et application
métier) et 8 (noyau minimal, briques opt-in) de la charte : un projet nu ne
devrait contenir ni le framework, ni sa suite de tests, ni sa documentation,
ni son application de démonstration.

### Faits techniques établis (audit)

- Le paquet `forge-mvc` **embarque déjà** `core`, `forge_cli` et
  `integrations` (`pyproject.toml` : `include = ["core*", "forge_cli*", "integrations*"]`).
  Un projet sans `core/` local fonctionne donc en important le paquet installé.
- `app.py` surcharge `views_dir` via `forge.configure(views_dir="mvc/views")`
  (chemin relatif au répertoire de travail) : aucun couplage au chemin du
  dépôt.
- Le superviseur d'autoreload ignore proprement un dossier `core/` absent
  (`if not base.is_dir(): continue`).
- Les layouts (`layouts/base.html`, etc.) n'utilisent ni `{% extends %}` ni
  `{% include %}` : une page d'accueil neutre s'affiche sans layout ni
  partial.
- Le `mvc/` racine du dépôt reste l'application de dogfooding, référencée par
  la grande majorité de la suite de tests. Un squelette **distinct** ne la
  touche pas.

---

## Décision

1. **Squelette dédié et curé.** Le squelette de projet vit dans le dépôt sous
   `forge_cli/skeleton/data/` (même modèle que `forge_cli/starters/data/`).
   Il contient un projet Forge minimal : `app.py`, `config.py`,
   `requirements.txt`, `env/example`, un `mvc/` minimal (route `/`, contrôleur
   d'accueil neutre, vue d'accueil autonome, `views/errors/*`, paquets vides
   `forms`/`validators`/`entities`/`models`/`helpers`), `static/` (avec
   `tailwind.css` compilé commité) et `storage/` vide.

2. **Dépendance core via pip.** Le `requirements.txt` du squelette dépend de
   `forge-mvc==<version>`. Le projet généré importe `core` depuis le paquet
   installé, **pas** depuis un `core/` local. Le squelette ne contient ni
   `core/`, ni `forge_cli/`, ni `integrations/`, ni `packages/`, ni `tests/`,
   ni `docs/`.

3. **Distribution en package-data.** L'arbre `forge_cli/skeleton/data/` est
   déclaré en `package-data` (`pyproject.toml` + `MANIFEST.in`) afin qu'un
   `forge` installé via `pipx`/`pip` puisse matérialiser un projet **sans
   réseau ni git**. `forge new` **copie** cet arbre (`shutil.copytree`) au lieu
   de cloner le dépôt.

4. **Le `git clone` du dépôt est retiré** de `forge new`, ainsi que les
   options associées (`--ref`, `_FORGE_REPO`, `_FORGE_DEFAULT_REF`). La
   dépendance à `git` n'est plus requise pour créer un projet (`openssl` reste
   nécessaire pour les certificats de développement).

5. **Anti-dérive.** `app.py` et `config.py` existent en double (racine du
   dépôt pour le dogfood, et squelette). Un test de cohérence garantit que la
   copie du squelette reste identique à la version racine, ou que toute
   divergence est intentionnelle et documentée.

### Précision sur « sans réseau »

La **matérialisation des fichiers** du squelette ne requiert ni réseau ni
git. En revanche, l'installation des dépendances (`pip install -r
requirements.txt`, qui tire `forge-mvc` depuis PyPI ou un index local) reste
une étape réseau normale, inchangée.

---

## Conséquences

### Positives

- Un projet nu est réellement nu : pas de framework, pas de tests, pas de
  docs, pas d'app de démo embarqués (principes 1 et 8).
- Plus de landing marketing, d'auth, de MFA, de media ni de mail pré-livrés :
  ces capacités passent par leurs starters et opt-ins respectifs, cohérent
  avec la trajectoire « un parcours welcome par opt-in » et avec ADR-023.
- Création de projet sans `git` ni réseau pour la partie fichiers ; plus
  rapide et plus robuste (pas de clone `--depth=1` du dépôt entier).
- Le `core` du projet provient du paquet versionné : le projet n'est plus
  couplé à une copie locale du framework.

### Limites

- `app.py`/`config.py` sont dupliqués (dogfood vs squelette) : géré par le
  test de cohérence anti-dérive.
- Rupture de l'API CLI : `forge new --ref <branche>` disparaît. En phase bêta
  pré-1.0, retrait direct, sans alias (convention pré-1.0 de `CLAUDE.md`).
- Le squelette doit être maintenu à la main au fil des évolutions runtime ;
  des garde-fous (tests d'inventaire et de neutralité) limitent la dérive.

---

## Alternatives écartées

### A — Élagage post-clone

Conserver le `git clone` du dépôt, puis supprimer les chemins non désirés et
réécrire un `mvc/` minimal.

Rejeté : on clone toujours tout le dépôt (lent, dépend de git/réseau), et la
liste d'élagage dérive à chaque évolution du dépôt. Ne traite pas la cause
(règle A) : le projet importerait encore un `core/` local.

### B — Amincir le `mvc/` racine

Rendre le `mvc/` racine du dépôt minimal et déplacer l'app de démo ailleurs.

Rejeté : le `mvc/` racine est l'application de dogfood référencée par la quasi
totalité de la suite de tests. Le déplacer casse ou déplace des centaines de
tests, pour un bénéfice qu'un squelette distinct obtient sans risque.

### C — Squelette sur une branche dédiée clonée

`forge new` clonerait une branche `skeleton` au lieu du dépôt entier.

Rejeté : conserve la dépendance git/réseau et la fragilité au tag, et empêche
la création hors-ligne. Le `package-data` est la seule option compatible avec
un `forge` pipx-installé.

---

## Hors périmètre de cet ADR

- Le contenu pédagogique exact de la page d'accueil neutre du squelette.
- La décision « source unique vs copie contrôlée » pour `app.py`/`config.py`
  (tranchée à l'implémentation, sous contrainte du test anti-dérive).
- L'éventuelle publication d'un index pip local pour les environnements
  totalement hors-ligne.

---

## Référence

- Tickets d'implémentation (séquence) : `SKELETON-TREE-001`,
  `SKELETON-PKGDATA-001`, `SKELETON-REGISTRY-001`, `NEW-MATERIALIZE-001`,
  `NEW-CORE-DEP-001`, `SKELETON-GUARD-001`, `NEW-CLI-CLEANUP-001`.
- Code concerné : `forge.py` (`cmd_new`, `_clone_skeleton`),
  `pyproject.toml`, `MANIFEST.in`, futur `forge_cli/skeleton/`.
- ADR-004 Périmètre du core : `docs/adr/004-core-perimeter.md`.
- ADR-005 Packaging : `docs/adr/005-packaging.md`.
- ADR-023 `forge starter:build` canonique : `docs/adr/023-starter-build-canonical.md`.
- Garde-fou existant : `tests/test_skeleton_routes_neutral_001.py`.
- Charte : `CHARTE_DOC.md` (principes 1, 2, 8 ; règle A).
