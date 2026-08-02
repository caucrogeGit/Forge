# Validation locale d'une wheel Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Ce document est destiné au développeur du framework.
Il décrit la procédure complète pour valider une wheel Forge avant publication.

---

## Environnement de validation release

### Objectif

Permettre à un auditeur de reproduire la validation locale d'une release Forge sans publier.

### Préconditions

- Dépôt sur `main`, état propre (hors `.claude/settings.json` et fichiers locaux explicitement exclus de Git).
- Environnement virtuel dédié.
- Python 3.12+ (version recommandée : 3.12.13 via pyenv, voir ADR-006).
- Dépendances de développement installées depuis `requirements-dev.txt`.
- Aucun accès réseau requis pour la validation une fois les dépendances installées.

### Commandes de validation manuelle

```bash
# Préparer un environnement virtuel dédié
python -m venv .venv-release-check
source .venv-release-check/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Puis exécuter la validation complète (script existant) :

```bash
bash tools/release-validate.sh <VERSION>
# ex. : bash tools/release-validate.sh {{forge_version}}
```

Ce script couvre : cohérence de version, CHANGELOG, pytest, ruff, compileall, mkdocs build --strict, état git propre, whitespace, tag absent.

Compléter avec la validation packaging :

```bash
rm -rf dist build *.egg-info
python -m build
twine check dist/*
```

**Alternative rapide** si l'environnement de développement est déjà actif :

```bash
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
rm -rf dist build *.egg-info
python -m build
twine check dist/*
```

### Script `scripts/release_check.sh` (disponible depuis le ticket 2.2)

La procédure manuelle ci-dessus peut désormais être lancée via :

```bash
bash scripts/release_check.sh          # mode standard
bash scripts/release_check.sh --full   # mode complet (+ build wheel + twine check)
bash scripts/release_check.sh --help   # aide
```

Le script valide localement, ne publie rien et ne crée aucun tag.
La publication reste le ticket **2.3 BETA-2-RELEASE-001**.

`tools/check_version_sync.py` vérifie la cohérence des versions entre le cœur et les opt-ins ; `tools/release-validate.sh` l'appelle.

### Résultats attendus

| Commande | Résultat attendu |
|---|---|
| `pytest` | 0 échec |
| `python -m compileall -q .` | Aucune sortie |
| `mkdocs build --strict` | 0 avertissement |
| `git diff --check` | Aucune sortie |
| `python -m build` | `dist/*.whl` et `dist/*.tar.gz` générés |
| `twine check dist/*` | `PASSED` pour wheel et sdist |
| `tools/release-validate.sh <VERSION>` | `RÉSULTAT : OK - prêt à releaser.` |

### Artefacts produits

Les répertoires `dist/`, `build/` et `*.egg-info/` sont des artefacts locaux.
Ils sont exclus de Git (`.gitignore`).
**Ils ne doivent pas être commités.**

### Limites

- Cette procédure ne publie rien sur PyPI.
- Elle ne crée aucun tag.
- `twine check` valide les métadonnées localement, `twine upload` est l'opération de publication, réservée au ticket **2.3 BETA-2-RELEASE-001**.

---

## 1. Construire la wheel

Depuis la racine du dépôt Forge :

```bash
cd /chemin/vers/Forge
rm -rf dist build *.egg-info
PYENV_VERSION=3.12.13 python -m build
```

Le préfixe `PYENV_VERSION=3.12.13` permet de forcer la version de développement recommandée pour Forge.
Alternative permanente pour le dossier :

```bash
pyenv local 3.12.13
python -m build
```

---

## 2. Installer avec pipx

Vérifier le nom exact de la wheel générée :

```bash
ls dist/
```

Puis installer :

```bash
pipx install dist/forge_mvc-{{forge_version}}-py3-none-any.whl --force
```

### Vérifier que c'est bien la bonne installation qui répond

```bash
pipx list
which forge
forge --version
```

Résultat attendu : `Forge {{forge_version}}`

Si le terminal indique :

```
forge was already on your PATH at /home/roger/.pyenv/shims/forge
```

Le shim pyenv intercepte la commande.
Forcer la résolution :

```bash
pyenv rehash
hash -r
which forge   # doit pointer vers ~/.local/bin/forge
forge --version
```

---

## 3. Créer un projet test et vérifier le socle

```bash
cd ~/Projets
forge new TestForge101
cd TestForge101
source .venv/bin/activate
forge doctor
forge --version
```

`forge doctor` doit confirmer un socle sain et `forge --version` afficher la version installée.

!!! note "Plus de génération de starter (ADR-035)"
    Depuis ADR-035, les commandes `forge starter:list` et `forge starter:build` n'existent plus.
    Les parcours pédagogiques se réalisent **à la main**, palier après palier, en suivant les progressions `welcome-<module>` de la documentation.
    La validation locale d'une release ne repose donc plus sur la génération de starters, mais sur le socle CLI, le packaging et la documentation.

---

## 4. Vérifier le socle CLI sans base de données

Vérifier que le socle CLI répond sans toucher MariaDB :

```bash
cd ~/Projets/TestForge101
forge help
forge routes:list
forge make:entity --help
```

Ces commandes confirment que la CLI est disponible dans le package installé et que les ressources du squelette sont bien incluses dans la wheel.

---

## 5. Tester un parcours pédagogique avec base de données

Les parcours `welcome-<module>` se réalisent **à la main** (ADR-035) : il n'y a plus de génération automatique.
Pour valider une release de bout en bout, dérouler au moins un parcours dans un projet neuf, palier après palier, en suivant la progression documentée.
Chaque parcours doit être réalisé dans un **projet séparé** : mélanger les entités de plusieurs parcours dans le même projet fausse le test.

### Prérequis : renseigner `env/dev` de chaque projet

Avant `forge db:init`, les variables suivantes doivent être renseignées dans `env/dev` :

```
DB_NAME=nom_de_la_base
DB_ADMIN_LOGIN=admin_de_la_base
DB_ADMIN_PWD=mot_de_passe_admin
DB_APP_LOGIN=utilisateur_applicatif
DB_APP_PWD=mot_de_passe_applicatif
```

!!! note "Erreur db:apply sans db:init"
    Le message `Connexion MariaDB applicative impossible. Lancez d'abord forge db:init` est **normal** si `db:init` n'a pas été exécuté.
    Ce n'est pas un défaut du parcours.

### Premier pas : Bienvenue dans Forge (sans BDD)

Ce parcours ne nécessite aucune base de données.
Il se réalise à la main dans le projet courant, en suivant la progression `welcome-forge`.

```bash
cd ~/Projets
forge new TestStarter7
cd TestStarter7
source .venv/bin/activate
# réaliser le parcours « welcome-forge » à la main (6 pages éducatives, sans BDD)
python app.py
```

Dans le navigateur, ouvrir `https://localhost:8000/welcome` et naviguer entre les 6 pages éducatives.

---

### Paramètres d'URL (sans BDD)

Palier 2 de la [progression officielle des starters](../starters/index.md#progression-recommandee).
Aucune base de données : le parcours `query-params` se réalise à la main.

```bash
cd ~/Projets
forge new TestStarterQueryParams
cd TestStarterQueryParams
source .venv/bin/activate
# réaliser le parcours « query-params » à la main (deux routes, lecture de la query string)
python app.py
```

Dans le navigateur, vérifier les deux routes :

- `https://localhost:8000/query-params` → message d'aide ;
- `https://localhost:8000/query-params/hello?name=Roger` → `Bonjour Roger`.

---

## 6. Tests automatiques et documentation

```bash
cd /chemin/vers/Forge

# Garde-fous de structure et de packaging (sans base de données)
PYENV_VERSION=3.12.13 python -m pytest -m meta -q

# Vérification des ancres et liens de documentation
PYENV_VERSION=3.12.13 python -m mkdocs build --strict
```

Les garde-fous `meta` vérifient notamment :

- que chaque distribution du dépôt est construite et publiée (complétude, `RELEASE-PYPI-COMPLETENESS-GUARD-001`) ;
- que les versions sont cohérentes entre le cœur et les vingt-sept opt-ins ;
- que la documentation ne nomme que du code existant, imports, commandes et signatures ;
- que les conventions de structure du squelette et des paquets tiennent.

Le build MkDocs `--strict` détecte les ancres cassées et les liens internes invalides.

---

## 7. Récapitulatif : validation réussie

| Étape | Résultat attendu |
|---|---|
| `python -m build` | wheel créée dans `dist/` |
| `forge --version` | `Forge {{forge_version}}` |
| `forge help` / `forge routes:list` | socle CLI disponible sans erreur |
| parcours « welcome-forge » à la main | pages éducatives HTTP sans BDD |
| un parcours d'opt-in joué dans un projet neuf | ses routes répondent en 2xx |
| `pytest -m meta -q` | tous passants |
| `mkdocs build --strict` | 0 avertissement d'ancre |

---

## 8. Limites connues

- Les garde-fous `meta` valident la structure et les conventions, pas le comportement applicatif.
- `--dry-run` ne valide pas la connexion MariaDB ni l'exécution de `db:apply`.
