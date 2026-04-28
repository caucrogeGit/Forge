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

Si `python -m build` échoue avec :

```
pyenv: python: command not found
The `python' command exists in these Python versions: 3.14.4
```

Deux options :

```bash
# Option A — variable d'environnement ponctuelle
PYENV_VERSION=3.14.4 python -m build

# Option B — version locale permanente dans le dossier
pyenv local 3.14.4
python -m build
```

---

## 2. Installer avec pipx

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
forge starter:build 3 --force --dry-run
forge starter:build 4 --force --dry-run
```

C'est suffisant pour confirmer que les fichiers JSON/Python/HTML sont bien présents dans le package.

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
```

### Starter 3 — Carnet de contacts

```bash
cd ~/Projets
forge new TestStarter3
cd TestStarter3
source .venv/bin/activate
# éditer env/dev
forge doctor
forge db:init
forge starter:build 3 --force
```

### Starter 4 — Suivi pédagogique

```bash
cd ~/Projets
forge new TestStarter4
cd TestStarter4
source .venv/bin/activate
# éditer env/dev
forge doctor
forge db:init
forge starter:build 4 --force
```

!!! note "Erreur db:apply sans db:init"
    Le message `Connexion MariaDB applicative impossible. Lancez d'abord forge db:init` est **normal** si `db:init` n'a pas été exécuté. Ce n'est pas un bug du starter.

---

## 6. Tests de packaging automatiques

```bash
cd /chemin/vers/Forge
pytest tests/test_packaging.py -v
```

Ces tests vérifient sans MariaDB :

- que `pyproject.toml` utilise bien `find_packages` avec les bons patterns ;
- que tous les sous-packages `core`, `forge_cli` et `integrations` sont couverts ;
- que les fichiers représentatifs de chaque starter existent sur disque ;
- que le glob `starters/data/**/*` couvre tous les types (`.py`, `.json`, `.html`, `.snippet`).

---

## 7. Limites connues

- Les tests `test_packaging.py` ne valident pas le contenu des fichiers, uniquement leur présence.
- Le starter 2 (utilisateurs/auth) n'est pas couvert par la procédure MariaDB ci-dessus car il nécessite une configuration supplémentaire (création d'utilisateur auth).
- `--dry-run` ne vérifie pas que le SQL généré est valide.
