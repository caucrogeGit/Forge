# Créer un projet sur la dernière version GitHub

Cette page s'adresse à l'utilisateur **avant-garde** : celui qui veut créer une application avec la **dernière version de Forge poussée sur GitHub** (`main`), en avance sur PyPI, sans cloner le dépôt pour contribuer.

!!! warning "Avant-garde = non publié"
    La branche `main` peut contenir des changements non stabilisés et non publiés.
    Utilisez ce parcours pour tester des nouveautés ou préparer une montée de version, pas pour un déploiement de production.
    Pour la production, restez sur la version PyPI.

---

## 1. Installer le CLI Forge depuis GitHub

Installez le paquet `forge-mvc` (qui fournit la commande `forge` et le squelette) directement depuis le dépôt, avec `pipx` :

```bash
pipx install "git+https://github.com/caucrogeGit/Forge.git@main"
```

Vous récupérez ainsi le **CLI et le squelette les plus récents**, ceux de `main`.
Vous pouvez viser une autre référence à la place de `main` : un tag, une branche ou un commit précis (`...Forge.git@<tag-ou-commit>`).

!!! warning "Si `forge-mvc` est déjà installé"
    Si vous avez déjà installé Forge par `pipx` (par exemple la version stable PyPI), pipx refuse d'écraser l'installation existante :
    `'forge-mvc' already seems to be installed. Pass '--force' to force installation.`
    Ajoutez alors `--force` :

    ```bash
    pipx install --force "git+https://github.com/caucrogeGit/Forge.git@main"
    ```

    Cela remplace votre `forge` global : tous vos `forge new` suivants seront basés sur GitHub.
    Pour revenir à la version stable PyPI :

    ```bash
    pipx install --force --pip-args="--pre" forge-mvc
    ```

!!! tip "Sans toucher à votre installation stable"
    Pour créer un projet avant-garde ponctuel sans modifier votre `forge` installé, exécutez Forge depuis GitHub de façon éphémère avec `pipx run` :

    ```bash
    pipx run --spec "git+https://github.com/caucrogeGit/Forge.git@main" forge new mon-app
    ```

    Votre `forge` global reste intact ; le projet généré est tout de même épinglé sur git (son propre venv est créé normalement).

Vérifiez la commande :

```bash
forge --help
```

---

## 2. Créer le projet

```bash
forge new mon-app
cd mon-app
forge run
```

Comme le CLI a été installé depuis Git, `forge new` **épingle automatiquement** la dépendance du projet généré sur la même source Git, au lieu de la version PyPI (souvent non publiée pour une version de `main`).
C'est le comportement décrit par l'[ADR-062](../adr/062-forge-new-install-source.md).

En fin de génération, `forge new` l'annonce :

```text
Version GitHub (ADR-062) : forge-mvc suit forge-mvc @ git+https://github.com/caucrogeGit/Forge.git@<commit>.
Le projet suit la dernière version poussée sur GitHub, épinglée au commit installé.
```

Le `requirements.txt` du projet reflète alors honnêtement cette source :

```text
forge-mvc @ git+https://github.com/caucrogeGit/Forge.git@<commit>
```

Le **commit exact** est épinglé, donc le projet reste **reproductible** : une réinstallation redonne la même version, même si `main` a avancé entretemps.

---

## 3. Choisir une base de données

Le projet généré est nu, sans backend de base de données ([ADR-060](../adr/060-backend-free-skeleton.md)).
Installez le backend de votre choix, exactement comme pour un projet PyPI :

```bash
source .venv/bin/activate
pip install forge-mvc-sqlite     # fichier local, sans serveur
```

Détails et autres backends : [Bases de données (backends)](../guide/bases-de-donnees.md).

---

## Comment ça marche

`forge new` ne prend **aucune option** pour cela : le comportement découle de la façon dont vous avez installé Forge.

- Si `forge-mvc` a été installé depuis Git (détecté via le `direct_url.json` de la norme PEP 610), le projet généré dépend de `forge-mvc @ git+<url>@<commit>`.
- Sinon, il épingle la version PyPI (`forge-mvc==<version>`), comme d'habitude.

La détection est **purement locale** (lecture des métadonnées déjà installées), sans accès réseau ni magie cachée.
Voir [ADR-062](../adr/062-forge-new-install-source.md).

!!! note "Suivre les mises à jour de main"
    Le projet est épinglé au commit installé.
    Pour passer à un `main` plus récent : réinstallez le CLI (`pipx install --force "git+https://github.com/caucrogeGit/Forge.git@main"`), puis mettez à jour la ligne `forge-mvc @ git+...@<commit>` de votre `requirements.txt` avec le nouveau commit, et réinstallez les dépendances.

---

## Autres installations de projet Forge

Cette page couvre l'installation sur la dernière version GitHub.
D'autres façons de créer un projet Forge existent, selon votre besoin :

* [Installation stable (poste Linux)](poste-linux.md) : la version publiée sur PyPI, le choix par défaut et le seul recommandé pour la production.
* [Contribuer au cœur de Forge](core-dev.md) : installer un projet pour modifier Forge lui-même (clone du dépôt, installation éditable, validations).
