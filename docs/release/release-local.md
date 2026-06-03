# Validation locale d'une wheel Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Ce document est destiné au développeur du framework. Il décrit la procédure complète pour valider une wheel Forge avant publication.

---

## Environnement de validation release

### Objectif

Permettre à un auditeur de reproduire la validation locale d'une release Forge
sans publier.

### Préconditions

- Dépôt sur `main`, état propre (hors `.claude/settings.json` et fichiers
  locaux explicitement exclus de Git).
- Environnement virtuel dédié.
- Python 3.12+ (version recommandée : 3.12.13 via pyenv — voir ADR-006).
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

Ce script couvre : cohérence de version, CHANGELOG, pytest, ruff, compileall,
mkdocs build --strict, état git propre, whitespace, tag absent.

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

`tools/check_version_sync.py` n'existe pas encore — la synchronisation des
versions entre core et opt-ins est assurée par `tools/release-validate.sh`.

### Résultats attendus

| Commande | Résultat attendu |
|---|---|
| `pytest` | 0 échec |
| `python -m compileall -q .` | Aucune sortie |
| `mkdocs build --strict` | 0 avertissement |
| `git diff --check` | Aucune sortie |
| `python -m build` | `dist/*.whl` et `dist/*.tar.gz` générés |
| `twine check dist/*` | `PASSED` pour wheel et sdist |
| `tools/release-validate.sh <VERSION>` | `RÉSULTAT : OK — prêt à releaser.` |

### Artefacts produits

Les répertoires `dist/`, `build/` et `*.egg-info/` sont des artefacts locaux.
Ils sont exclus de Git (`.gitignore`). **Ils ne doivent pas être commités.**

### Limites

- Cette procédure ne publie rien sur PyPI.
- Elle ne crée aucun tag.
- `twine check` valide les métadonnées localement — `twine upload` est
  l'opération de publication, réservée au ticket **2.3 BETA-2-RELEASE-001**.

---

## 1. Construire la wheel

Depuis la racine du dépôt Forge :

```bash
cd /chemin/vers/Forge
rm -rf dist build *.egg-info
PYENV_VERSION=3.12.13 python -m build
```

Le préfixe `PYENV_VERSION=3.12.13` permet de forcer la version de développement recommandée pour Forge. Alternative permanente pour le dossier :

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

Le shim pyenv intercepte la commande. Forcer la résolution :

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
forge starter:list
```

`forge starter:list` doit afficher les 41 starters sans erreur. C'est la vérification minimale que les ressources sont bien incluses dans la wheel.

---

## 4. Vérifier les starters sans base de données

`--dry-run` affiche ce que le starter produirait sans rien écrire et sans toucher MariaDB :

```bash
cd ~/Projets/TestForge101
forge starter:build 1 --force --dry-run
forge starter:build 2 --force --dry-run
forge starter:build 3 --force --dry-run
forge starter:build 4 --force --dry-run
forge starter:build 5 --force --dry-run
forge starter:build 6 --force --dry-run
forge starter:build 7 --force --dry-run
forge starter:build 8 --force --dry-run
forge starter:build 9 --force --dry-run
forge starter:build 10 --force --dry-run
forge starter:build 11 --force --dry-run
forge starter:build 12 --force --dry-run
forge starter:build 13 --force --dry-run
forge starter:build 14 --force --dry-run
forge starter:build 15 --force --dry-run
forge starter:build 16 --force --dry-run
forge starter:build 17 --force --dry-run
forge starter:build 18 --force --dry-run
forge starter:build 19 --force --dry-run
forge starter:build 20 --force --dry-run
forge starter:build 21 --force --dry-run
forge starter:build 22 --force --dry-run
forge starter:build 23 --force --dry-run
forge starter:build 24 --force --dry-run
forge starter:build 25 --force --dry-run
forge starter:build 26 --force --dry-run
forge starter:build 27 --force --dry-run
forge starter:build 28 --force --dry-run
forge starter:build 29 --force --dry-run
forge starter:build 30 --force --dry-run
forge starter:build 31 --force --dry-run
forge starter:build 32 --force --dry-run
forge starter:build 33 --force --dry-run
forge starter:build 34 --force --dry-run
forge starter:build 35 --force --dry-run
forge starter:build 36 --force --dry-run
forge starter:build 37 --force --dry-run
forge starter:build 38 --force --dry-run
forge starter:build 39 --force --dry-run
forge starter:build 40 --force --dry-run
forge starter:build 41 --force --dry-run
```

!!! note "Ce que --dry-run valide"
    `--dry-run` est une validation de **packaging et de chemin d'exécution CLI**. Il confirme que :

    - la commande est disponible ;
    - les ressources du starter sont trouvées dans le package installé ;
    - la logique de génération est atteignable.

    Il ne valide **pas** :

    - la connexion MariaDB ;
    - l'exécution réelle de `db:apply` ;
    - la création effective des tables ;
    - le fonctionnement final de l'application.

    Pour une validation complète, utiliser `forge db:init` puis `forge starter:build N --force` dans un projet neuf par starter.

---

## 5. Tester les starters avec base de données

Chaque starter doit être testé dans un **projet séparé**. Lancer plusieurs starters dans le même projet laisse les entités du starter précédent en place et fausse le test.

### Prérequis — renseigner `env/dev` de chaque projet

Avant `forge db:init`, les variables suivantes doivent être renseignées dans `env/dev` :

```
DB_NAME=nom_de_la_base
DB_ADMIN_USER=root
DB_ADMIN_PWD=mot_de_passe_admin
DB_APP_USER=utilisateur_applicatif
DB_APP_PWD=mot_de_passe_applicatif
```

!!! note "Erreur db:apply sans db:init"
    Le message `Connexion MariaDB applicative impossible. Lancez d'abord forge db:init` est **normal** si `db:init` n'a pas été exécuté. Ce n'est pas un bug du starter.

### Contacts

```bash
cd ~/Projets
forge new TestStarter1
cd TestStarter1
source .venv/bin/activate
# éditer env/dev → DB_NAME, DB_ADMIN_USER, DB_ADMIN_PWD, DB_APP_USER, DB_APP_PWD
forge doctor
forge db:init
forge starter:build 1 --force
python app.py
```

Dans le navigateur, à l'URL affichée par Forge :

- vérifier `/contacts` (liste vide attendue) ;
- créer un contact via `/contacts/new` ;
- vérifier que la fiche apparaît dans la liste.

### Utilisateurs / authentification

```bash
cd ~/Projets
forge new TestStarter2
cd TestStarter2
source .venv/bin/activate
# éditer env/dev → DB_NAME, DB_ADMIN_USER, DB_ADMIN_PWD, DB_APP_USER, DB_APP_PWD
forge doctor
forge db:init
forge starter:build 2 --force
```

Créer l'utilisateur de test :

```bash
python scripts/create_auth_user.py
```

Le script crée un utilisateur fixe et affiche ses identifiants :

```
Utilisateur de test prêt :
  login    admin
  password secret123
```

Lancer l'application :

```bash
python app.py
```

Dans le navigateur, à l'URL affichée par Forge :

- aller sur `/login` ;
- se connecter avec `admin` / `secret123` ;
- vérifier l'accès à `/dashboard` (route protégée).

### Carnet de contacts

```bash
cd ~/Projets
forge new TestStarter3
cd TestStarter3
source .venv/bin/activate
# éditer env/dev → DB_NAME, DB_ADMIN_USER, DB_ADMIN_PWD, DB_APP_USER, DB_APP_PWD
forge doctor
forge db:init
forge starter:build 3 --force
```

Optionnellement, injecter des villes de référence :

```bash
python scripts/seed_villes.py
```

Lancer l'application :

```bash
python app.py
```

Dans le navigateur, à l'URL affichée par Forge :

- vérifier `/contacts` (liste) ;
- vérifier `/villes` (liste, peuplée si seed lancé) ;
- créer un contact et lui associer une ville.

### Suivi pédagogique

```bash
cd ~/Projets
forge new TestStarter4
cd TestStarter4
source .venv/bin/activate
# éditer env/dev → DB_NAME, DB_ADMIN_USER, DB_ADMIN_PWD, DB_APP_USER, DB_APP_PWD
forge doctor
forge db:init
forge starter:build 4 --force
```

Créer l'utilisateur de test et injecter les données de démonstration :

```bash
python scripts/create_auth_user.py
python scripts/seed_suivi.py
```

`create_auth_user.py` crée `admin` / `secret123` (identiques au starter 2).

Lancer l'application :

```bash
python app.py
```

Dans le navigateur, à l'URL affichée par Forge :

- se connecter sur `/login` avec `admin` / `secret123` ;
- vérifier le tableau de bord `/suivi` ;
- vérifier la liste des élèves `/eleves` ;
- vérifier la liste des cours `/cours`.

### Communes & Séjours

Démonstrateur avancé : pages publiques, formulaire de demande, notifications mail.

```bash
cd ~/Projets
forge new TestStarter5
cd TestStarter5
source .venv/bin/activate
# éditer env/dev → DB_NAME, DB_ADMIN_USER, DB_ADMIN_PWD, DB_APP_USER, DB_APP_PWD
forge doctor
forge db:init
forge starter:build 5 --force
```

Lancer l'application :

```bash
python app.py
```

Dans le navigateur, à l'URL affichée par Forge :

- vérifier une page publique (liste ou fiche de commune) ;
- vérifier le formulaire de demande de séjour ;
- si la configuration mail est présente, vérifier la notification.

### Auth MFA (TOTP)

**Prérequis** : `forge-mvc-mfa` installé (`pip install --pre forge-mvc-mfa` — publié sur PyPI depuis `1.0.0-beta.9`, statut Alpha).

```bash
cd ~/Projets
forge new TestStarter6
cd TestStarter6
source .venv/bin/activate
# éditer env/dev → DB_NAME, DB_ADMIN_USER, DB_ADMIN_PWD, DB_APP_USER, DB_APP_PWD
forge doctor
forge db:init
forge starter:build 6 --force
```

Créer l'utilisateur de test :

```bash
python scripts/create_auth_user.py
```

Lancer l'application :

```bash
python app.py
```

Dans le navigateur, à l'URL affichée par Forge :

- aller sur `/login` ;
- se connecter avec `admin` / `secret123` ;
- vérifier la challenge MFA sur `/login/mfa` ;
- vérifier l'accès à `/dashboard` après validation TOTP.

---

### Premier pas — Bienvenue dans Forge (sans BDD)

Ce starter ne nécessite aucune base de données. Il s'applique directement via `forge new --starter welcome`.

```bash
cd ~/Projets
forge new TestStarter7 --starter welcome
cd TestStarter7
source .venv/bin/activate
python app.py
```

Dans le navigateur, ouvrir `https://localhost:8000/welcome` et naviguer entre les 6 pages éducatives.

---

### Paramètres d'URL (sans BDD)

Palier 2 de la [progression officielle des starters](../starters/index.md#progression-recommandee). Aucune base de données — le starter s'applique par son identifiant public `query-params`.

```bash
cd ~/Projets
forge new TestStarterQueryParams --starter query-params
cd TestStarterQueryParams
source .venv/bin/activate
python app.py
```

Dans le navigateur, vérifier les deux routes :

- `https://localhost:8000/query-params` → message d'aide ;
- `https://localhost:8000/query-params/hello?name=Roger` → `Bonjour Roger`.

---

## 6. Tests automatiques et documentation

```bash
cd /chemin/vers/Forge

# Tests de packaging (sans MariaDB)
PYENV_VERSION=3.12.13 python -m pytest tests/test_packaging.py -v

# Vérification des ancres et liens de documentation
PYENV_VERSION=3.12.13 python -m mkdocs build --strict
```

Les tests de packaging vérifient :

- que `pyproject.toml` utilise bien `find_packages` avec les bons patterns ;
- que tous les sous-packages `core`, `forge_cli` et `integrations` sont couverts ;
- que les fichiers représentatifs de chaque starter existent sur disque ;
- que le glob `starters/data/**/*` couvre tous les types (`.py`, `.json`, `.html`, `.snippet`).

Le build MkDocs `--strict` détecte les ancres cassées et les liens internes invalides.

---

## 7. Récapitulatif — validation réussie

| Étape | Résultat attendu |
|---|---|
| `python -m build` | wheel créée dans `dist/` |
| `forge --version` | `Forge {{forge_version}}` |
| `forge starter:list` | 41 starters affichés |
| `forge starter:build N --dry-run` | plan affiché sans erreur (×41) |
| `forge db:init` + `starter:build 1` | CRUD contacts fonctionnel |
| `forge db:init` + `starter:build 2` | login `admin` / `secret123` → `/dashboard` |
| `forge db:init` + `starter:build 3` | contacts + villes, seed optionnel |
| `forge db:init` + `starter:build 4` | auth + suivi + seed |
| `forge db:init` + `starter:build 5` | pages publiques + formulaire séjour |
| `forge db:init` + `starter:build 6` | auth + MFA TOTP (nécessite forge-mvc-mfa) |
| `forge new MonProjet --starter welcome` | pages éducatives HTTP sans BDD |
| `pytest tests/test_packaging.py` | 14/14 passants |
| `mkdocs build --strict` | 0 avertissement d'ancre |

---

## 8. Limites connues

- Les tests `test_packaging.py` ne valident pas le contenu des fichiers, uniquement leur présence.
- `--dry-run` ne valide pas la connexion MariaDB ni l'exécution de `db:apply`.
- `seed_suivi.py` requiert que les entités du starter 4 aient été créées (`db:apply` passé).
