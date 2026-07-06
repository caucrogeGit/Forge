# Mode développement : contribuer au core Forge

Cette page guide un développeur qui veut **modifier Forge lui-même** : corriger un bug du noyau, ajouter une commande à la CLI, étendre la documentation, faire évoluer la convention HTTP.
Ce n'est pas le parcours pour créer une application **avec** Forge, voir la distinction ci-dessous.

---

## Public : le développeur du cœur, pas l'utilisateur du framework

Cette page ne couvre **pas** l'installation d'un projet Forge classique.
Si votre but est de créer une application **avec** Forge, vous êtes un **utilisateur du framework** : suivez plutôt [Poste Linux](poste-linux.md), cette page n'est pas pour vous.

Le **développeur du core** (le public de cette page) ne crée pas d'application : il clone le dépôt et l'installe en mode éditable pour **modifier Forge lui-même** (`core/`, `cli/`, `tests/`, `docs/`, `packages/`), au moyen des étapes ci-dessous.

!!! warning "Ne pas utiliser `pipx` pour développer le core"
    `pipx` installe Forge dans un environnement isolé, en lecture seule pour l'utilisateur.
    Vous ne pourrez **pas** modifier les sources Forge depuis là.
    Pour développer le core, il faut une installation éditable depuis le dépôt cloné (voir étapes ci-dessous).

---

## Prérequis

- Python 3.12+ ([ADR-006](../adr/006-python-version.md))
- Git, `make` (optionnel), `openssl`
- Une base de données **uniquement** pour les tests d'intégration optionnels (marqués `db`, ciblant MariaDB aujourd'hui).
  La suite par défaut n'en a pas besoin.
  Le choix du backend est libre ([ADR-054](../adr/054-database-backend-optins.md)), voir la section 10.
- Node.js 24.17.0 LTS, uniquement pour recompiler le CSS Tailwind (`docs/static/tailwind.css` est déjà commité, donc pas requis pour les tests ni `mkdocs build`)

---

## 1. Cloner le dépôt Forge

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
```

L'URL SSH (`git@github.com:caucrogeGit/Forge.git`) fonctionne aussi si vous avez une clé SSH configurée sur GitHub.

---

## 2. Créer et activer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate
```

Le `.venv` reste local au dépôt cloné, jamais commité.
Si vous travaillez sur plusieurs versions de Forge en parallèle, recréez un `.venv` par clone, ne réutilisez pas un venv d'un autre clone.

---

## 3. Installer Forge en mode éditable + outils de développement

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` fait trois choses simultanément :

1. inclut `requirements.txt` (les dépendances runtime du cœur : `python-dotenv`, `jinja2`, `argon2-cffi`, `jsonschema`).
   Le cœur est **agnostique de la base de données** ([ADR-054](../adr/054-database-backend-optins.md), [ADR-060](../adr/060-backend-free-skeleton.md)) : le pilote (`mariadb`, `sqlite3`, `psycopg`, etc.) est apporté par le backend choisi, pas par le cœur.
   De même, Pillow a quitté le cœur et relève de l'opt-in `forge-mvc-images` ([ADR-018](../adr/018-image-module-extraction.md)) ;
2. installe les outils de développement (`pytest`, `ruff`, `pyright`, `bandit`, `build`, `setuptools`, `twine`, `mkdocs`, `mkdocs-material`, `mkdocs-monorepo-plugin`, `mkdocs-glightbox`, `pymdown-extensions`, `pip-audit`) ;
3. installe **tous les paquets du monorepo** en mode éditable depuis `packages/` : les backends de base de données, les opt-ins fonctionnels et l'infrastructure de test partagée.
   La liste complète et à jour est le contenu de `packages/` (détaillée en section 8) ; ne figez pas un compte ici, il évolue à chaque nouvel opt-in.

!!! note "Sans `requirements-dev.txt`, pytest casse"
    De nombreux fichiers de tests importent les modules opt-in (`forge_mvc_mfa`, `forge_mvc_rbac`, etc.).
    Sans installation éditable depuis `packages/`, la collecte pytest échoue.
    Le ticket de fond reste documenté dans `requirements-dev.txt`.

Une **installation éditable** signifie que toute modification dans `core/`, `cli/` ou `packages/forge-mvc-*/` est prise en compte immédiatement, sans réinstallation.
C'est la condition pour itérer sur le code Forge.

### Variante : installation minimale (sans les modules opt-in)

Si vous ne touchez ni aux opt-ins ni aux tests qui les importent, vous pouvez vous limiter à :

```bash
python -m pip install -e .
python -m pip install pytest ruff mkdocs mkdocs-material pymdown-extensions
```

Cette variante est **plus rapide** mais provoque des erreurs de collecte sur les tests opt-in.
À réserver aux cas spécifiques (profilage, bisection, environnements sans accès aux paquets locaux).

---

## 4. Vérifier l'installation : les 5 validations canoniques

Toute contribution Forge doit passer ces 5 validations avant commit :

```bash
python -m pytest -x -q          # complet, 0 régression
python -m compileall -q .       # syntaxe Python OK partout
ruff check .                    # lint, zéro avertissement
mkdocs build --strict           # doc sans lien brisé
git diff --check                # pas d'erreur d'espaces / mélange tabs
```

| Commande | Rôle |
|---|---|
| `python -m pytest -x -q` | Suite complète : runtime, générateurs, doc, CLI, sécurité, méta. `-x` s'arrête au premier échec. |
| `python -m compileall -q .` | Vérifie que tous les `.py` du dépôt sont syntaxiquement valides. |
| `ruff check .` | Lint et style, **aucun** avertissement n'est toléré sur `main`. |
| `mkdocs build --strict` | Construit la doc complète et échoue si un lien est cassé ou si la nav est incohérente. |
| `git diff --check` | Détecte les espaces en fin de ligne, les marqueurs de conflit oubliés, les mélanges tabs/espaces. |

Le typage statique est vérifié à part avec `pyright` (le cœur est en mode strict, [ADR-036](../adr/036-core-static-typing.md)) et la CI lance aussi `bandit` et `pip-audit`.

### Tests d'intégration base de données (optionnels)

Certains tests valident l'intégration avec une **base de données réelle**.
Ils sont marqués `db`, désactivés par défaut, et ne s'exécutent que si vous fournissez une base de test dédiée.
Ils ciblent actuellement MariaDB.

```bash
# Le nom de la base doit commencer par forge_e2e_ (garde-fou anti-écrasement).
FORGE_TEST_DB_HOST=127.0.0.1 \
FORGE_TEST_DB_NAME=forge_e2e_test \
FORGE_TEST_DB_USER=forge_e2e_user \
FORGE_TEST_DB_PASSWORD=secret \
python -m pytest -m db
```

Détails dans [Tests E2E](../reference/tests-e2e.md) et, pour le choix du moteur, la section 10.

Voir [Contribuer à Forge](../philosophy/contributing.md) pour le processus complet (branche, message de commit, PR, checklist).

---

## 5. CSS Tailwind : quand le recompiler ?

`docs/static/tailwind.css` est **commité** dans le dépôt.
La doc et les tests fonctionnent sans Node.
Recompiler le CSS n'est nécessaire que si vous modifiez :

- `docs/static/src/input.css`
- des templates Jinja2 qui introduisent de nouvelles classes Tailwind utilitaires

```bash
nvm use            # lit .nvmrc -> Node 24.17.0
npm install
npm run build:css
```

Le script `build:css` est défini dans `package.json` : `npx @tailwindcss/cli -i ./docs/static/src/input.css -o ./docs/static/tailwind.css --minify`.

La version de Node est **imposée** : `.nvmrc` épingle `24.17.0`, `package.json` déclare `engines.node >= 24.17.0`, et `.npmrc` active `engine-strict=true`, `npm` refuse donc de s'exécuter sous une version de Node inférieure.

---

## 6. Lancer un serveur HTTP pour tester : passer par `forge new`

Le dépôt Forge ne porte **que le framework** ([ADR-044](../adr/044-framework-only-repo.md)) : il n'y a plus d'`app.py` ni de dossier `mvc/` à la racine, l'application de dogfooding a été relocalisée en fixture de test (`tests/fixtures/app/`).
Par conséquent, `forge run` **ne fonctionne pas** depuis la racine du dépôt cloné, il n'y a pas d'application à y servir.

Pour tester manuellement un comportement HTTP pendant que vous modifiez le cœur, générez un projet jetable qui pointe vers votre working tree, via `FORGE_DEV_SRC` (section 7 juste en dessous) :

```bash
# .venv du clone activé, depuis un dossier de travail (ex. /tmp)
cd /tmp
FORGE_DEV_SRC=/home/roger/Projets/Forge forge new essai-http
cd essai-http
forge run
```

!!! note "Le quotidien du contributeur"
    Dans un projet généré par `forge new`, `forge run` est le **point d'entrée principal** du développement.
    Côté dépôt cœur, générer un projet jetable est un **outil de validation manuelle** secondaire : le quotidien du contributeur, c'est `pytest`, `ruff`, `mkdocs build --strict`, pas `forge run`.
    La différence avec un projet généré est donc nette.

---

## 7. `forge new` qui pointe vers ton clone (`FORGE_DEV_SRC`)

Par défaut, `forge new` épingle `forge-mvc` à la version publiée sur PyPI (via le `requirements.txt` du projet généré).
Sur ta machine de développement, tu veux souvent l'inverse : qu'un projet généré exécute **ton clone**, pour valider sur le terrain une modification du noyau avant toute publication.
C'est le « retour terrain optimum ».

La variable d'environnement `FORGE_DEV_SRC` fait exactement cela.

### Principe

Quand `FORGE_DEV_SRC` pointe vers le dépôt Forge cloné, `forge new` installe `forge-mvc` en **éditable depuis ce dépôt**, au lieu de la version PyPI épinglée.
Le projet généré exécute alors le working tree : toute modification de `core/` ou `cli/` est prise en compte immédiatement, sans réinstaller ni régénérer le projet.

C'est explicite et opt-in ([principe 3](../philosophy/charter.md)) : sans la variable, `forge new` reste sur la version publiée.

### Commande de lancement

Depuis le clone Forge, `.venv` activé (l'installation éditable de la section 3 fournit déjà la commande `forge`) :

```bash
# .venv du clone Forge activé
FORGE_DEV_SRC=/home/roger/Projets/Forge forge new mon-app
cd mon-app
forge run
```

| Élément | Rôle |
|---|---|
| `FORGE_DEV_SRC=/home/roger/Projets/Forge` | Chemin **absolu** de ton clone Forge. |
| `forge new mon-app` | Génère le projet et installe `forge-mvc` en éditable depuis le clone. |
| `forge run` | Lance le projet, qui exécute donc ton working tree. |

À la génération, `forge new` confirme le mode : `Mode dev (FORGE_DEV_SRC=…) : forge-mvc installé en éditable.`

!!! note "Rendre le mode permanent"
    Pour que **tous** tes `forge new` de développement pointent vers le clone, exporte la variable dans ton shell : `echo 'export FORGE_DEV_SRC=/home/roger/Projets/Forge' >> ~/.bashrc`.
    Retire l'export (ou ouvre un shell neuf) pour revenir au comportement normal, sur la version PyPI publiée.

### Tester aussi un backend depuis le working tree

Le projet généré est nu, sans backend de base de données ([ADR-060](../adr/060-backend-free-skeleton.md)).
Pour faire tourner un backend depuis ton clone plutôt que depuis PyPI, installe-le en éditable dans le projet :

```bash
cd mon-app
source .venv/bin/activate
pip install -e /home/roger/Projets/Forge/packages/forge-mvc-sqlite
```

`forge new` rappelle cette commande en fin de sortie quand `FORGE_DEV_SRC` est actif.

---

## 8. Travailler sur les opt-ins (packages/)

Les paquets du monorepo vivent dans `packages/`, chacun avec son propre `pyproject.toml`.
Le **contenu de `packages/` est la source canonique** de la liste ([CLAUDE.md, section 8](https://github.com/caucrogeGit/Forge/blob/main/CLAUDE.md)) : elle évolue à chaque nouvel opt-in, ne vous fiez pas à un compte figé.
Ils se répartissent en trois familles.

**Backends de base de données** (exclusifs, un seul actif à la fois, [ADR-054](../adr/054-database-backend-optins.md)) :

```text
forge-mvc-mariadb    MariaDB (pool de connexions, provisioning)
forge-mvc-sqlite     SQLite (module sqlite3 de la bibliothèque standard)
forge-mvc-postgres   PostgreSQL (psycopg)
forge-mvc-mssql      Microsoft SQL Server (pyodbc)
```

**Opt-ins fonctionnels** :

```text
forge-mvc-mfa            Authentification MFA (TOTP, codes de récupération)
forge-mvc-rbac           Rôles, permissions, helpers Jinja
forge-mvc-workflow       Statuts et transitions applicatives
forge-mvc-stats          Événements génériques, agrégats, tracking
forge-mvc-files          Upload générique (storage, service HTTP Range)
forge-mvc-images         Traitement d'image (Pillow) + couche médias
forge-mvc-audio          Upload, sondage, transcodage MP3, lecture HTTP Range
forge-mvc-video          Upload, transcodage MP4, lecture HTTP Range
forge-mvc-iot            Réception/exposition de données IoT (MQTT)
forge-mvc-pivot          Tables pivot enrichies (many_to_many avec attributs)
forge-mvc-mail           Envoi de courriels (composition, transports, templates)
forge-mvc-i18n           Internationalisation (catalogues JSON, trans(), fallback)
forge-mvc-qrcode         Génération de QR Codes (PNG/SVG)
forge-mvc-settings       Paramètres applicatifs persistés en base
forge-mvc-admin          Back-office applicatif (CRUD générique)
forge-mvc-import-export  Échange CSV (import validé, export)
forge-mvc-audit          Journal d'audit applicatif (table audit_log)
forge-mvc-jobs           File de tâches de fond adossée à MariaDB
forge-mvc-notifications  Notifications in-app
forge-mvc-deploy         Outillage de déploiement (opt-in CLI, ADR-053)
```

**Infrastructure de test** (réservée au développement, [ADR-041](../adr/041-shared-test-support.md)) :

```text
forge-mvc-testing        FakeRequest + plugin pytest partagés
```

`requirements-dev.txt` les installe **tous** en éditable, donc les modifications dans `packages/forge-mvc-*/` sont prises en compte sans réinstallation.

Pour publier un opt-in sur PyPI, suivre la procédure release dédiée ([release-policy.md](../release/release-policy.md)).

---

## 9. Architecture rapide du dépôt

```text
core/          Briques génériques du framework (HTTP, sessions, sécurité, …)
cli/           Commandes et générateurs Forge (make:entity, sync:entity, …)
packages/      Backends BDD et opt-ins officiels en mode monorepo
forge.py       Point d'entrée de la CLI Forge
integrations/  Adaptateurs d'intégration (registre de loaders Jinja, ADR-046)
tools/         Outils de développement et de maintenance
scripts/       Scripts shell (dev-server, smoke IoT, release_check)
tests/         Suite de tests pytest
tests/meta/    Tests documentaires et architecturaux
tests/fixtures/app/  Application de dogfooding relocalisée (ADR-044)
docs/          Documentation MkDocs, dont la landing (docs/index.html)
docs/static/   CSS Tailwind compilé + assets de la doc et de la landing
overrides/     Surcharges du thème MkDocs Material
official-site/ Publication du site officiel (ADR-045)
```

!!! note "Dépôt framework uniquement"
    Depuis [ADR-044](../adr/044-framework-only-repo.md), le dépôt ne contient plus d'application métier à la racine (`app.py`, `mvc/`, `config.py`, `env/`).
    Ces éléments vivent désormais soit dans le squelette généré par `forge new`, soit dans la fixture de test `tests/fixtures/app/`.

Détails complets dans [Contribuer à Forge](../philosophy/contributing.md) (section « Comprendre l'architecture »).

---

## 10. Bases de données : choisir un backend

Le cœur de Forge est **agnostique** de la base de données ([ADR-054](../adr/054-database-backend-optins.md)) : il découvre le backend installé et n'en active qu'un seul par projet.
Vous n'avez donc pas besoin de base pour la suite de tests par défaut.
Vous en installez une seulement pour les tests d'intégration (`pytest -m db`) ou pour faire tourner un projet généré.

Quatre backends officiels, **exclusifs entre eux** :

| Backend | Moteur | Serveur requis |
|---|---|---|
| `forge-mvc-sqlite` | SQLite (module `sqlite3` de la bibliothèque standard) | Non (fichier local, idéal pour un essai rapide) |
| `forge-mvc-mariadb` | MariaDB / MySQL | Oui |
| `forge-mvc-postgres` | PostgreSQL (`psycopg`) | Oui |
| `forge-mvc-mssql` | Microsoft SQL Server (`pyodbc`) | Oui |

Installation, configuration de l'environnement et provisionnement détaillés : [Bases de données (backends)](../guide/bases-de-donnees.md).

---

## 11. Pour aller plus loin

| Étape | Ressource |
|---|---|
| Processus de contribution complet | [Contribuer à Forge](../philosophy/contributing.md) |
| Conventions de code et de tests | [Conventions de travail](../contributing/conventions.md) |
| Charte philosophique du projet | [Charte v2](../philosophy/charter.md) |
| Décisions architecturales | [ADR](../adr/index.md) |
| Procédure de release | [Politique de release](../release/release-policy.md) |
| Bases de données et backends | [Bases de données](../guide/bases-de-donnees.md) |
| Tests d'intégration base de données | [Tests E2E](../reference/tests-e2e.md) |

---

## Voir aussi

- [Poste Linux (pipx, utilisateur du framework)](poste-linux.md)
- [Windows + WSL (parcours complet)](windows-wsl.md)
- [Démarrer avec Forge](../guide/getting-started.md)
- [Roadmap Forge](../roadmap/forge-roadmap.md), ticket `INSTALL-CORE-DEV-DOCS-AUDIT-001`
