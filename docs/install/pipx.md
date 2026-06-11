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
sudo apt install -y libmariadb-dev build-essential python3-dev
pipx ensurepath
exec $SHELL -l
```

!!! warning "Dépendance native MariaDB"

    Le paquet Python `mariadb` est compilé depuis les sources et a besoin de l'outil `mariadb_config`.
    Cet outil est fourni par `libmariadb-dev` ; `build-essential` et `python3-dev` couvrent la compilation de la roue.
    Sans eux, `pipx install` échoue avec `mariadb_config not found` lors du build de `mariadb`.

    Vérifier que l'outil est trouvable :

    ```bash
    mariadb_config --version
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
