# Validation locale d'une wheel Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Ce document est destiné au développeur du framework. Il décrit la procédure complète pour valider une wheel Forge avant publication.

---

## 1. Construire la wheel

Depuis la racine du dépôt Forge :

```bash
cd /chemin/vers/Forge
rm -rf dist build *.egg-info
PYENV_VERSION=3.14.4 python -m build
```

Le préfixe `PYENV_VERSION=3.14.4` est nécessaire si `python` n'est pas défini dans la version active de pyenv. Alternative permanente pour le dossier :

```bash
pyenv local 3.14.4
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
pipx install dist/forge_mvc-1.0.1-py3-none-any.whl --force
```

### Vérifier que c'est bien la bonne installation qui répond

```bash
pipx list
which forge
forge --version
```

Résultat attendu : `Forge 1.0.1`

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

`forge starter:list` doit afficher les 4 starters sans erreur. C'est la vérification minimale que les ressources sont bien incluses dans la wheel.

---

## 4. Vérifier les starters sans base de données

`--dry-run` affiche ce que le starter produirait sans rien écrire et sans toucher MariaDB :

```bash
cd ~/Projets/TestForge101
forge starter:build 1 --force --dry-run
forge starter:build 2 --force --dry-run
forge starter:build 3 --force --dry-run
forge starter:build 4 --force --dry-run
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

### Starter 1 — Contacts

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

### Starter 2 — Utilisateurs / authentification

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

### Starter 3 — Carnet de contacts

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

### Starter 4 — Suivi pédagogique

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

---

## 6. Tests automatiques et documentation

```bash
cd /chemin/vers/Forge

# Tests de packaging (sans MariaDB)
PYENV_VERSION=3.14.4 python -m pytest tests/test_packaging.py -v

# Vérification des ancres et liens de documentation
PYENV_VERSION=3.14.4 python -m mkdocs build --strict
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
| `forge --version` | `Forge 1.0.1` |
| `forge starter:list` | 4 starters affichés |
| `forge starter:build N --dry-run` | plan affiché sans erreur (×4) |
| `forge db:init` + `starter:build 1` | CRUD contacts fonctionnel |
| `forge db:init` + `starter:build 2` | login `admin` / `secret123` → `/dashboard` |
| `forge db:init` + `starter:build 3` | contacts + villes, seed optionnel |
| `forge db:init` + `starter:build 4` | auth + suivi + seed |
| `pytest tests/test_packaging.py` | 14/14 passants |
| `mkdocs build --strict` | 0 avertissement d'ancre |

---

## 8. Limites connues

- Les tests `test_packaging.py` ne valident pas le contenu des fichiers, uniquement leur présence.
- `--dry-run` ne valide pas la connexion MariaDB ni l'exécution de `db:apply`.
- `seed_suivi.py` requiert que les entités du starter 4 aient été créées (`db:apply` passé).
