# Installation avec pipx

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

!!! info "Forge {{forge_version}} — bêta disponible sur PyPI"

    Le core `forge-mvc` est publié sur [PyPI](https://pypi.org/project/forge-mvc/)
    sous la version `{{forge_version}}`. L'option `--pip-args="--pre"` est nécessaire car
    `{{forge_version}}` est une préversion bêta PEP 440.

    Depuis `1.0.0-beta.9`, **tous les opt-ins officiels** (MFA, RBAC, workflow,
    statistiques, media) sont publiés sur PyPI — voir
    [Installation](index.md#contrat-dinstallation-des-opt-ins).

`pipx` est la méthode la plus simple pour utiliser Forge comme commande globale.

## Prérequis

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip pipx git openssl
pipx ensurepath
exec $SHELL -l
```

## Installer Forge

```bash
pipx install --pip-args="--pre" forge-mvc
forge --version
```

## Créer un projet

```bash
forge new MonProjet
cd MonProjet
source .venv/bin/activate
forge doctor
```

`forge new` clone la référence stable par défaut, prépare l'environnement Python
du projet et réinitialise l'historique Git pour votre application.
