# Mode développement — contribuer au core Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page guide un développeur qui veut **modifier Forge lui-même** :
corriger un bug du noyau, ajouter une commande à la CLI, étendre la
documentation, faire évoluer la convention HTTP. Ce n'est pas le
parcours pour créer une application **avec** Forge — voir la
distinction ci-dessous.

---

## Utilisateur du framework vs développeur du core

Deux parcours **distincts**, qui ne se mélangent pas :

| | **Utilisateur du framework** | **Développeur du core (cette page)** |
|---|---|---|
| But | Créer une application avec Forge | Modifier Forge lui-même |
| Installation | `pipx install --pip-args="--pre" forge-mvc` | `git clone` du dépôt + `pip install -e .` |
| Point d'entrée projet | `forge new mon-app` | `cd Forge` (le dépôt cloné) |
| Fichiers modifiés | `mvc/`, `env/`, `mvc/entities/...` | `core/`, `forge_cli/`, `tests/`, `docs/`, `packages/` |
| Lancement | `forge run` dans le projet généré | `python -m pytest` + outils de dev |
| Référence | [Installation avec pipx](pipx.md) | cette page + [Contribuer](../contributing.md) |

!!! warning "Ne pas utiliser `pipx` pour développer le core"
    `pipx` installe Forge dans un environnement isolé, en lecture seule
    pour l'utilisateur. Vous ne pourrez **pas** modifier les sources
    Forge depuis là. Pour développer le core, il faut une installation
    éditable depuis le dépôt cloné (voir étapes ci-dessous).

---

## Prérequis

- Python 3.12+ ([ADR-006](../adr/006-python-version.md))
- Git, `make` (optionnel), `openssl`
- MariaDB local — uniquement pour les tests E2E
  (`tests/test_e2e_mariadb.py`), pas pour la suite par défaut
- Node.js 20 LTS — uniquement pour recompiler le CSS Tailwind
  (`static/tailwind.css` est déjà commité, donc pas requis pour les
  tests ni `mkdocs build`)

---

## 1. Cloner le dépôt Forge

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
```

L'URL SSH (`git@github.com:caucrogeGit/Forge.git`) fonctionne aussi si
vous avez une clé SSH configurée sur GitHub.

---

## 2. Créer et activer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate
```

Le `.venv` reste local au dépôt cloné, jamais commité. Si vous
travaillez sur plusieurs versions de Forge en parallèle, recréez un
`.venv` par clone — ne réutilisez pas un venv d'un autre clone.

---

## 3. Installer Forge en mode éditable + outils de développement

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` fait deux choses simultanément :

1. inclut `requirements.txt` (les 5 dépendances runtime `mariadb`,
   `python-dotenv`, `jinja2`, `Pillow`, `argon2-cffi`) ;
2. installe les outils de développement (`pytest`, `build`,
   `setuptools`, `twine`, `mkdocs`, `mkdocs-material`,
   `pymdown-extensions`, `pip-audit`, `ruff`) ;
3. installe les **5 modules opt-in** Forge en mode éditable depuis
   le monorepo (`forge-mvc-mfa`, `forge-mvc-rbac`,
   `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-media`).

!!! note "Sans `requirements-dev.txt`, pytest casse"
    Environ 46 fichiers de tests importent les modules opt-in
    (`forge_mvc_mfa`, `forge_mvc_rbac`, etc.). Sans installation
    éditable depuis `packages/`, la collecte pytest échoue. Le ticket
    de fond reste documenté dans `requirements-dev.txt`.

Une **installation éditable** signifie que toute modification dans
`core/`, `forge_cli/` ou `packages/forge-mvc-*/` est prise en compte
immédiatement, sans réinstallation. C'est la condition pour itérer
sur le code Forge.

### Variante : installation minimale (sans les modules opt-in)

Si vous ne touchez ni aux opt-ins ni aux tests qui les importent, vous
pouvez vous limiter à :

```bash
python -m pip install -e .
python -m pip install pytest ruff mkdocs mkdocs-material pymdown-extensions
```

Cette variante est **plus rapide** mais provoque des erreurs de
collecte sur les tests opt-in. À réserver aux cas spécifiques
(profilage, bisection, environnements sans accès aux paquets locaux).

---

## 4. Vérifier l'installation — les 5 validations canoniques

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
| `python -m pytest -x -q` | Suite complète (~14 900 tests) — runtime, générateurs, doc, CLI, sécurité, méta. `-x` s'arrête au premier échec. |
| `python -m compileall -q .` | Vérifie que tous les `.py` du dépôt sont syntaxiquement valides. |
| `ruff check .` | Lint et style — **aucun** avertissement n'est toléré sur `main`. |
| `mkdocs build --strict` | Construit la doc complète et échoue si un lien est cassé ou si la nav est incohérente. |
| `git diff --check` | Détecte les espaces en fin de ligne, les marqueurs de conflit oubliés, les mélanges tabs/espaces. |

Pour les tests E2E MariaDB (optionnels, désactivés par défaut) :

```bash
FORGE_E2E_MARIADB=1 python -m pytest tests/test_e2e_mariadb.py
```

Voir [Contribuer à Forge](../contributing.md) pour le processus complet
(branche, message de commit, PR, checklist).

---

## 5. CSS Tailwind — quand le recompiler ?

`static/tailwind.css` est **commité** dans le dépôt. La doc et les
tests fonctionnent sans Node. Recompiler le CSS n'est nécessaire que
si vous modifiez :

- `static/src/input.css`
- des templates Jinja2 qui introduisent de nouvelles classes Tailwind
  utilitaires

```bash
npm install
npm run build:css
```

Le script `build:css` est défini dans `package.json` :
`npx @tailwindcss/cli -i ./static/src/input.css -o ./static/tailwind.css --minify`.

---

## 6. `forge run` dans le dépôt Forge — possible mais limité

Le dépôt Forge contient lui-même un `app.py` et un dossier `mvc/`
(squelette de référence utilisé par les tests d'intégration et la
documentation). Par conséquent, `forge run` **fonctionne depuis la
racine du dépôt cloné** : Forge se dogfoode.

```bash
# Depuis la racine du dépôt Forge cloné, .venv activé
forge run
```

Ce mode est utile pour :

- vérifier qu'une modification du noyau ne casse pas le démarrage ;
- tester manuellement un comportement HTTP en développement.

Ce mode n'est **pas** utile pour :

- développer une application métier — utilisez plutôt un projet
  séparé créé avec `forge new mon-projet` ailleurs sur votre disque ;
- vérifier un starter spécifique — utilisez
  `forge starter:build <id>` dans un projet généré.

!!! note "Différence avec un projet généré"
    Dans un projet utilisateur Forge créé par `forge new`, `forge run`
    est le **point d'entrée principal** du développement. Dans le
    dépôt core, c'est un **outil de validation manuelle** secondaire :
    le quotidien du contributeur, c'est `pytest`, `ruff`,
    `mkdocs build --strict`, pas `forge run`.

---

## 7. Travailler sur les opt-ins (packages/)

Les 5 modules opt-in vivent dans `packages/` :

```text
packages/
├── forge-mvc-mfa/        Authentification MFA (TOTP, codes de récupération)
├── forge-mvc-rbac/       Rôles et permissions
├── forge-mvc-workflow/   Statuts et transitions
├── forge-mvc-stats/      Agrégats statistiques
└── forge-mvc-media/      Helpers applicatifs upload
```

Chacun a son propre `pyproject.toml`. `requirements-dev.txt` les
installe **tous** en éditable, donc les modifications dans
`packages/forge-mvc-*/` sont prises en compte sans réinstallation.

Pour publier un opt-in sur PyPI, suivre la procédure release dédiée
([release-policy.md](../release-policy.md)).

---

## 8. Architecture rapide du dépôt

```text
core/          Briques génériques du framework (HTTP, sessions, sécurité, …)
forge_cli/    Commandes et générateurs Forge (make:entity, sync:entity, …)
mvc/          Squelette applicatif de référence (dogfood)
packages/      Modules opt-in officiels en mode monorepo
tests/         Suite de tests pytest (~14 900 tests)
tests/meta/   Tests documentaires et architecturaux
docs/          Documentation MkDocs
static/        CSS Tailwind compilé + assets de la landing
mvc/views/landing/  Source canonique de la landing page
```

Détails complets dans [Contribuer à Forge](../contributing.md) (section
« Comprendre l'architecture »).

---

## 9. Pour aller plus loin

| Étape | Ressource |
|---|---|
| Processus de contribution complet | [Contribuer à Forge](../contributing.md) |
| Conventions de code et de tests | [Conventions de travail](../contributing/conventions.md) |
| Charte philosophique du projet | [Charte v2](../charter.md) |
| Décisions architecturales | [ADR](../adr/) |
| Procédure de release | [Politique de release](../release-policy.md) |
| Tests E2E MariaDB | [Tests E2E](../reference/tests-e2e.md) |

---

## Voir aussi

- [Installation — vue d'ensemble](index.md)
- [Installation avec pipx (utilisateur du framework)](pipx.md)
- [Windows + WSL (parcours complet)](windows-wsl.md)
- [Démarrer avec Forge](../getting-started.md)
- [Roadmap Forge](../roadmap/forge-roadmap.md) — ticket `INSTALL-CORE-DEV-DOCS-AUDIT-001`
