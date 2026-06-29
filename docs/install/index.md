# Installation de Forge

Cette page rassemble les parcours d'installation de Forge selon votre poste.
Chaque parcours est complet et autonome ; choisissez celui qui correspond à votre environnement.

## 1. Installation rapide

```bash
pipx install --pip-args="--pre" forge-mvc
forge --version
```

Créer un projet et lancer le serveur de développement :

```bash
forge new mon-projet
cd mon-projet
source .venv/bin/activate
forge run
```

`forge new` prépare tout le projet : squelette, environnement Python avec `forge-mvc`, fichier `env/dev`, certificat HTTPS de développement et dépôt Git.

## 2. Parcours complets

| Poste | Guide |
|-------|-------|
| Windows + WSL | [Windows + WSL (parcours complet)](windows-wsl.md) |
| Poste Linux | [Poste Linux (parcours complet)](poste-linux.md) |
| VM Debian vierge | [VM Debian vierge](vm-debian.md) |
| Depuis GitHub (framework) | [Depuis GitHub](github.md) |
| Windows (résumé court) | [Windows](windows.md) |

!!! tip "Dépannage serveur de développement (WSL2)"
    En cas de souci avec le serveur de développement sous WSL2, voir [Dépannage serveur dev (WSL2)](wsl-dev-server.md).

## 3. Base de données

Le cœur de Forge est agnostique de la base de données (ADR-054) : vous ajoutez un backend en opt-in, un seul par projet.

Les premiers paliers tournent sans base de données.
Un backend SQL ne devient nécessaire qu'à partir du palier « Première base SQL ».

- Pour démarrer sans serveur : `pip install --pre forge-mvc-sqlite`.
- Pour la production : `pip install --pre forge-mvc-mariadb`, puis [Préparer MariaDB](mariadb.md) et [Comptes MariaDB d'un projet](mariadb-comptes.md).

Vue d'ensemble et choix du moteur : [Bases de données dans Forge](../guide/bases-de-donnees.md).

## 4. Environnement et outillage

- [Contrat d'installation des opt-ins](opt-ins.md) : comment installer et activer un opt-in.
- [Configurer VS Code (auto-import)](vscode.md) et [Environnement VS Code](vscode-environnement.md).
- [Mode développement](core-dev.md) : travailler sur le framework lui-même.
- [Production](production.md) : mise en production.

## Voir aussi

- [Démarrer avec Forge](../guide/getting-started.md) : votre première application, palier par palier.
- [Bonjour Forge](../guide/bonjour-forge.md) : le tout premier contact.
