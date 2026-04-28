# Mode développement

[Accueil](index.html){ .md-button }

Le mode développement sert à travailler sur le framework Forge lui-même.

## Cloner la branche de développement

```bash
git clone --branch main https://github.com/caucrogeGit/Forge.git Forge
cd Forge
```

## Installer les dépendances

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

## Vérifier le dépôt

```bash
python -m pytest
python -m build
mkdocs build --strict
```

Pour générer un projet applicatif depuis `main`, utilisez l'option explicite :

```bash
forge new MonProjet --ref main
```
