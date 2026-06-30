# Démarrer avec Forge

De zéro à une application qui tourne, en trois étapes.
Chaque commande est en copier-coller ; les détails complets sont reliés au fil du texte.

## 1. Installer Forge

Choisissez l'onglet correspondant à votre poste.
La commande d'installation est la même partout (`pipx`) ; seule la préparation système change, détaillée dans chaque parcours complet.

=== "Poste Linux (recommandé)"

    Prérequis : Python 3.12+ et `pipx`.

    ```bash
    pipx install --pip-args="--pre" forge-mvc
    forge --version
    ```

    Parcours complet : [Poste Linux (pipx)](../install/poste-linux.md).

=== "Windows + WSL"

    Forge s'utilise sous WSL2 (Ubuntu), pas en Windows natif.

    ```bash
    # dans le terminal Ubuntu (WSL2)
    pipx install --pip-args="--pre" forge-mvc
    forge --version
    ```

    Résumé : [Installation Windows](../install/windows.md).
    Pas-à-pas complet : [Windows + WSL](../install/windows-wsl.md).

=== "VM Debian vierge"

    Après installation des paquets système (Python 3.12, `pipx`) :

    ```bash
    pipx install --pip-args="--pre" forge-mvc
    forge --version
    ```

    Parcours complet : [VM Debian vierge](../install/vm-debian.md).

=== "Depuis les sources (GitHub)"

    Pour contribuer au framework ou figer une version précise :

    ```bash
    git clone https://github.com/caucrogeGit/Forge.git
    cd Forge
    python -m pip install -e .
    python -m pip install -r requirements.txt
    ```

    Détails : [Installation depuis GitHub](../install/github.md).

!!! tip "Toutes les options"
    Comptes MariaDB, opt-ins, configuration VS Code : voir la [page Installation](../install/index.md).

## 2. Créer le projet

```bash
forge new MonProjet
cd MonProjet
source .venv/bin/activate
```

`forge new` crée le projet, installe les dépendances et génère les certificats HTTPS de développement.

!!! note "Deux étapes manuelles avant la base de données"
    Renseignez les identifiants MariaDB dans `env/dev`, puis lancez `forge db:init`.
    Les premiers paliers tournent sans base de données ; pour choisir un moteur (SQLite sans serveur, MariaDB en production), voir [Bases de données](bases-de-donnees.md).

## 3. Lancer

```bash
forge run
```

Forge démarre en HTTPS sur `https://localhost:8000` et redémarre automatiquement dès que vous modifiez un fichier de l'application (autoreload).

!!! note "En production"
    `forge run` refuse de servir en production.
    Le seul chemin supporté est WSGI + Gunicorn derrière un reverse proxy : [Déploiement WSGI](../deployment/wsgi-deployment.md).

!!! tip "Toutes les commandes"
    Diagnostic, génération, migrations, CRUD : voir la [Référence CLI](../reference/cli-commands.md).

## Et après ?

- [Bonjour Forge](bonjour-forge.md) : le premier contact (route, contrôleur, réponse).
- [Progression des starters](../starters/index.md#progression-recommandee) : neuf paliers, de « Bonjour Forge » au premier CRUD.
- [Application complète](app-complete-tutorial.md) : CRUD, relations, formulaires.
- [Guide de démarrage](guide.md) : configurer MariaDB, créer une entité, générer le CRUD.
