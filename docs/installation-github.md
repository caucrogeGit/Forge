# Installation depuis GitHub

[Accueil](index.html){ .md-button }

Cette méthode est utile si vous voulez créer un projet directement depuis la
référence stable du dépôt.

## Cloner la version stable

```bash
git clone --branch v1.0.1 --depth=1 https://github.com/caucrogeGit/Forge.git MonProjet
cd MonProjet
```

## Réinitialiser votre dépôt applicatif

```bash
rm -rf .git
git init
git add -A
git commit -m "init: MonProjet — based on Forge 1.0.1"
```

## Installer l'environnement local

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
forge doctor
```

Cette méthode reste explicite : vous voyez exactement ce que `forge new` automatise.
