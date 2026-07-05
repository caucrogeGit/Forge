# ADR-063 : Le squelette livre l'apparat qualité Forge complet ; noyau applicatif minimal, échappatoire `--bare`

## Statut

Acceptée, Forge 1.0.0-rc.x (ticket `SKELETON-STANDARDS-CONFORMANCE-001`).
Décision actée et **implémentation livrée** : F1 et F6 (registre), T1 (config pyright/ruff), T2 (socle test), T3 (chaîne documentaire), T4 (CI et `make check`), T5 (scaffold ADR, `.editorconfig`, `CHANGELOG`, pointeurs ADR de F7) et T6 (`forge new --bare`).
Les deux installations sont vérifiées de bout en bout : le défaut passe `make check` (lint, typage strict, tests, documentation), la variante `--bare` reste dépouillée mais fonctionnelle.

Cet ADR **révise la portée d'ADR-024** : « projet nu » ne signifie plus « dépouillé de tout », mais « noyau applicatif minimal, apparat qualité maximal ».

---

## Date

2026-07-05

---

## Contexte

Forge s'impose à lui-même un standard de qualité : cœur en typage `# pyright: strict` par fichier vérifié en CI (ADR-036), lint `ruff`, tests `pytest` avec `forge-mvc-testing` (ADR-041), documentation `mkdocs`, validation avant chaque commit.

Le squelette produit par `forge new` était volontairement nu (ADR-024), au sens dépouillé : hors `.vscode/settings.json` (qui passe déjà l'éditeur en strict) et la couche de guidance agent (`agents:init`, ADR-047), il ne livrait aucune configuration ni aucun socle qualité.

Un retour terrain (projet applicatif RéférenCiel Manager, monté au standard Forge) a révélé le coût de ce choix.
Le développeur qui veut tenir le même standard que le framework doit tout reconstituer à la main : configuration `pyright`/`ruff`, socle `pytest`, chaîne `mkdocs`, CI, journal d'ADR.
Une heure de mise en conformité, et un risque de divergence sur chaque valeur reconstituée.
Symptôme parlant : l'éditeur est strict (`.vscode`), mais la ligne de commande et la CI ne le sont pas, faute de `[tool.pyright]`.

L'intention réelle du squelette n'est pas « le moins de fichiers possible ».
C'est « le moins de code applicatif échafaudé possible, mais toute la philosophie Forge présente ».
Ces deux axes sont orthogonaux : on peut livrer zéro code métier et pourtant tout l'apparat qualité.

---

## Décision

Le squelette livre par défaut **l'apparat qualité Forge complet**, et garde le **noyau applicatif minimal**.
La frontière n'est plus « config livrée / machinerie opt-in », mais « code métier échafaudé (absent) / apparat qualité et philosophie (livré) ».

### 1. Livré par défaut : l'apparat qualité complet

- **Typage strict (F2)** : `pyproject.toml` outillage-only avec `[tool.pyright]` (`include` sur `mvc`, `optins`), et marqueur `# pyright: strict` par fichier sur les fichiers éditables générés (`optins/registry.py`, `mvc/routes.py`, contrôleurs). L'éditeur, la ligne de commande et la CI vérifient enfin la même chose.
- **Lint (F3)** : `[tool.ruff]` dans le même `pyproject.toml`, aligné sur les valeurs canoniques de Forge (`target-version = "py312"`, `line-length = 120`, `select = ["E", "F"]`, `ignore = ["E501", "E741", "E402"]`).
- **Tests (F4, A4)** : `pytest.ini` (`--strict-markers`, marqueurs `meta`/`smoke`/`db`), `tests/conftest.py` (constante `PROJECT_ROOT`), un smoke `tests/test_smoke_001.py` qui prouve que l'application démarre et que les routes se chargent, `requirements-dev.txt` épinglant `forge-mvc-testing` au commit du cœur (ADR-041).
- **Documentation (F5)** : `mkdocs.yml` (Material, français), `requirements-docs.txt`, `docs/index.md`.
- **Intégration continue (A1)** : `.github/workflows/quality.yml`, miroir du `tests.yml` de Forge, exécutant `pyright` (strict), `ruff`, `pytest`, `mkdocs build --strict`.
- **Point d'entrée unique de validation (A2)** : un `Makefile` avec une cible `check` lançant les quatre gardes en une commande, visible et sans magie (le développeur reproduit le bloc de validation Forge sans le réécrire).
- **Journal de décisions (F7, A5)** : `docs/adr/index.md` et `docs/adr/000-template.md`, en plus de `docs/adr/001-adopter-forge.md` déjà posé par `agents:init`. La couche de guidance agent référence explicitement les ADR fondateurs (ADR-024, 036, 041, 054/060, 061, 063), sans recopier leur corps.
- **Hygiène de dépôt (A6, A7)** : `.editorconfig` (cohérent avec `git diff --check` et la règle « une phrase par ligne »), `CHANGELOG.md` amorcé (Keep a Changelog, section `[Non publié]`).

Le `pyproject.toml` livré ne porte **ni `[project]` ni `[build-system]`** : c'est une configuration d'outillage, pas une déclaration de paquet distribuable.
Le noyau reste minimal à l'exécution : les dépendances de développement et de documentation vivent dans des `requirements-dev.txt` et `requirements-docs.txt` séparés, **non installés** par le `requirements.txt` runtime.
La compatibilité avec le pin de source d'ADR-062 est préservée : seule la ligne `forge-mvc` du `requirements.txt` reste concernée.

### 2. Reste absent : le code métier

Le squelette n'échafaude aucun code applicatif : pas d'entité, pas de CRUD, pas de contrôleur métier au delà de la page d'accueil.
Ce code se génère à la demande (`make:crud`, etc.), comme aujourd'hui.
« Minimal » qualifie le code métier, pas l'apparat qualité.

### 3. Échappatoire `forge new --bare`

Pour le cas rare où le développeur veut un squelette dépouillé (démonstration, intégration dans un dépôt existant déjà outillé), `forge new --bare` produit le squelette sans l'apparat qualité (ni `pyproject.toml` qualité, ni socle test, ni doc, ni CI, ni Makefile).
Les commandes `forge test:init` et `forge docs:init` restent disponibles comme chemin de rattrapage pour rajouter les socles à un projet `--bare`.
Le défaut, lui, est complet.

---

## Conséquences

- Un `forge new` neuf est conforme au standard Forge dès la première minute : `make check` passe (typage strict, lint, tests, doc), sans une ligne de configuration à écrire.
- L'éditeur, la ligne de commande et la CI vérifient la même chose : fin de l'incohérence strict-éditeur / non-strict-terminal.
- Les valeurs de qualité sont uniques et alignées sur le cœur : plus de dérive projet par projet.
- Le noyau reste léger à l'exécution : les deps dev et doc ne sont pas installées par défaut.
- La frontière « code métier échafaudé absent / apparat qualité livré » devient la règle de tri pour tout futur ajout au squelette.
- Des garde-fous vérifient que la config `ruff`/`pyright` livrée reste alignée sur les valeurs canoniques, que les fichiers éditables passent `pyright` strict, et que `--bare` produit bien un squelette dépouillé.
- Coût assumé : un `forge new` par défaut produit davantage de fichiers qu'avant. C'est le but ; `--bare` couvre le besoin inverse.

### Alternatives écartées

- **Statu quo (squelette dépouillé)** : le squelette trahit le standard qu'il incarne, chaque projet réinvente et diverge (retour terrain RéférenCiel Manager, une heure de mise en conformité, ADR-003 à 007 réécrits à la main).
- **Socles test/doc en générateurs opt-in** (première version de cet ADR) : ne correspond pas à l'intention ; un développeur qui choisit Forge veut sa philosophie d'office, pas une seconde étape manuelle.
- **Recopier les ADR de Forge dans le squelette** : duplication et dérive garanties, contraire au principe 11 ; les pointeurs suffisent.
- **Passer tout le projet en `pyright: strict` global** : impose le strict au code applicatif non encore écrit, alors que le cœur procède par marqueur par fichier (ADR-036).
- **pre-commit hooks livrés** : ajoutent un outil externe et un `pre-commit install` obligatoire, frôlent la magie cachée (principe 3) ; laissés hors périmètre.

---

## Charte appliquée

- **Principe 10 (une API publique est un contrat de complétude)** : le squelette ne se contente pas de respecter le standard, il le rend vérifiable et tenable d'emblée.
- **Principe 11 (une seule façon officielle de faire chaque chose)** : valeurs `ruff`/`pyright` uniques et alignées sur le cœur ; ADR référencés, jamais recopiés ; un seul défaut, l'échappatoire `--bare` étant explicite.
- **Principe 3 (refuser la magie cachée)** : toute la configuration livrée est lisible dans le projet (`pyproject.toml`, `Makefile`, `quality.yml`), aucun comportement implicite.
- **Principe 8 (noyau minimal, briques opt-in)** : réinterprété, non contredit. Le noyau applicatif reste minimal ; l'apparat qualité n'est pas une brique métier mais la philosophie du framework.

Révise ADR-024 (portée de « nu »).
Lié à ADR-036 (typage strict par fichier), ADR-041 (infrastructure de test partagée), ADR-047 (guidance agent), ADR-061 (registre d'opt-ins), ADR-062 (pin de source du `requirements.txt`).
Le retour terrain `SKELETON-STANDARDS-CONFORMANCE-001` porte le détail des écarts F1 à F7.
