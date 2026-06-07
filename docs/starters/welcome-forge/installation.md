# Installation — Progression « Bonjour Forge »

Ce préambule installe Forge et génère le projet de départ de la progression
pédagogique. C'est la **seule page du parcours** qui contient des commandes de
création : tous les paliers suivants supposent le projet **déjà créé** et se
concentrent sur le code.

!!! info "Référence complète"
    Cette page suffit pour démarrer la progression. Pour les parcours
    spécifiques (Windows + WSL, VM Debian, base MariaDB, mode contributeur),
    voir le guide d'installation complet : [Installer Forge](../../install/index.md).

## Prérequis

- **Python 3.12+** (Forge n'est pas compatible avec les versions antérieures).
- Aucune base de données n'est requise pour les premiers paliers : ils tournent
  **sans `db:init`**. La base MariaDB n'est nécessaire qu'à partir du palier
  « Première base SQL » — voir [Préparer MariaDB](../../install/mariadb.md).

## 1. Installer Forge

Méthode recommandée pour utiliser le framework — installation isolée avec
**pipx** (bêta publique, `--pre` requis) :

```bash
pipx install --pip-args="--pre" forge-mvc
```

Vérifier :

```bash
forge --version
```

Alternatives (Linux/macOS, Windows, depuis les sources) : voir
[Installation avec pipx](../../install/pipx.md) et
[Installer Forge](../../install/index.md).

## 2. Créer le projet de départ

`forge new` crée un projet Forge **nu**, sans starter :

```bash
forge new mon-projet
```

## 3. Construire le starter Bonjour Forge

La progression démarre sur le starter `welcome` (Bonjour Forge). On le
construit dans le projet courant avec `forge starter:build` :

```bash
cd mon-projet
source .venv/bin/activate
forge starter:build welcome
```

## 4. Lancer le projet

```bash
forge run
```

Ouvrez `https://localhost:8000/welcome` : la page affiche **« Bonjour Forge »**.

## 5. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` contrôle l'environnement (version Python, configuration,
dépendances) de façon non invasive.

## Après l'installation

Le projet tourne : vous pouvez attaquer le premier palier de code.

[Continuer avec Bonjour Forge](debutant/welcome.md)
