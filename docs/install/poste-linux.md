# Installation sur Debian, Ubuntu et leurs dérivées

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page explique comment installer Forge sur un poste de développement utilisant Debian, Ubuntu, Linux Mint ou une distribution compatible avec `apt`.

Pour les autres distributions Linux, le principe reste le même, mais les noms des paquets système peuvent changer.

---

## Objectif

À la fin de cette installation, le poste doit permettre de lancer la commande globale :

```bash
forge
```

Puis de créer un projet Forge avec :

```bash
forge new MonProjet
```

Forge est installé avec `pipx`, afin de garder la commande `forge` isolée du Python système.

---

## Prérequis système

Mettre à jour les paquets du système :

```bash
sudo apt update
```

Installer les outils nécessaires :

```bash
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  pipx \
  git \
  openssl \
  build-essential \
  python3-dev \
  libmariadb-dev
```

Activer le chemin de `pipx` :

```bash
pipx ensurepath
exec $SHELL -l
```

Vérifier que `pipx` est disponible :

```bash
pipx --version
```

---

## Pourquoi `libmariadb-dev` est nécessaire ?

Forge utilise MariaDB comme base de données principale.

Le connecteur Python `mariadb` peut nécessiter une compilation native lors de l’installation. Pour cela, l’outil `mariadb_config` doit être disponible sur le système.

Il est fourni par le paquet :

```text
libmariadb-dev
```

Vérifier sa présence :

```bash
mariadb_config --version
```

Si cette commande échoue, l’installation de Forge peut échouer avec une erreur du type :

```text
mariadb_config not found
```

---

## Installer Forge

Forge est publié sur PyPI sous la version :

```text
{{forge_version}}
```

Comme il s’agit d’une version bêta, l’option `--pre` doit être transmise à `pip`.

Installer Forge avec `pipx` :

```bash
pipx install --pip-args="--pre" forge-mvc
```

Vérifier l’installation :

```bash
forge --version
```

La commande doit afficher une version de Forge.

---

## Mettre à jour Forge plus tard

Pour mettre à jour Forge vers une nouvelle version bêta publiée sur PyPI :

```bash
pipx upgrade --pip-args="--pre" forge-mvc
forge --version
```

---

## Configurer Git

`forge new` initialise un dépôt Git pour le projet et crée un commit initial.
Git doit donc connaître votre identité, sinon ce commit échoue.

Configurer une identité Git, une fois par machine :

```bash
git config --global user.name "Prénom Nom"
git config --global user.email "vous@example.com"
git config --global init.defaultBranch main
```

Vérifier que Git est configuré :

```bash
git config --global user.name
git config --global user.email
```

---

## Créer un nouveau projet Forge

Créer un projet vide :

```bash
forge new MonProjet
```

Entrer dans le dossier du projet :

```bash
cd MonProjet
```

Activer l’environnement Python du projet :

```bash
source .venv/bin/activate
```

Vérifier l’état du projet :

```bash
forge doctor
```

---

## Lancer le serveur de développement

Depuis le dossier du projet :

```bash
forge run
```

Par défaut, `forge run` démarre le projet en mode développement.

---

## Résultat attendu

Après installation, l’environnement doit être dans cet état :

| Commande | Résultat attendu |
| -------- | ---------------- |
| `forge --version` | affiche la version de Forge |
| `forge help` | liste les commandes disponibles |
| `forge doctor` | diagnostic du projet sans erreur bloquante |
| `forge run` | démarre le serveur de développement |

Les deux dernières commandes se lancent depuis le dossier d’un projet Forge.

---

## Poursuivre la configuration

Pour compléter l’environnement selon votre besoin, poursuivez avec les pages suivantes :

* [Configurer MariaDB](mariadb.md) : installer MariaDB Server, créer un utilisateur applicatif et préparer la base du projet.
* [Installer les opt-ins Forge](opt-ins.md) : ajouter les extensions officielles comme IoT, RBAC, MFA, Images, Stats ou Workflow.
* [Préparer un déploiement en production](production.md) : comprendre les prérequis serveur, WSGI, reverse proxy et limites de production.
* [Installer depuis GitHub](github.md) : travailler depuis le dépôt source de Forge pour contribuer ou développer le framework.
* [Développer le cœur de Forge](core-dev.md) : préparer un environnement local pour modifier Forge lui-même.

Cette page constitue donc le point d’entrée Linux.
Les autres pages permettent d’aller progressivement vers une installation complète, un projet connecté à MariaDB, ou un environnement de contribution.
