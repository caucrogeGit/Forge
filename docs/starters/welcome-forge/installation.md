# Installation : progression « Bonjour Forge »

Ce préambule installe Forge et génère le projet de départ de la progression
pédagogique. C'est la **seule page du parcours** qui contient des commandes de
création : tous les paliers suivants supposent le projet **déjà créé** et se
concentrent sur le code, que vous écrivez vous-même au fil des paliers.

!!! info "Référence complète"
    Cette page suffit pour démarrer la progression. Pour les parcours
    spécifiques (Windows + WSL, VM Debian, base MariaDB, mode contributeur),
    voir le guide d'installation complet : [Installer Forge](../../install/poste-linux.md).

## Prérequis

- **Python 3.12+** (Forge n'est pas compatible avec les versions antérieures).
- Aucune base de données n'est requise pour les premiers paliers : ils tournent
  **sans `db:init`**. La base MariaDB n'est nécessaire qu'à partir du palier
  « Première base SQL », voir [Préparer MariaDB](../../install/mariadb.md).

## 1. Installer Forge

Méthode recommandée pour utiliser le framework : installation isolée avec
**pipx** (bêta publique, `--pre` requis) :

```bash
pipx install --pip-args="--pre" forge-mvc
```

Vérifier :

```bash
forge --version
```

Alternatives : [Poste Linux (pipx)](../../install/poste-linux.md),
[Windows + WSL](../../install/windows-wsl.md) ou [depuis GitHub](../../install/github.md).

## 2. Créer le projet de départ

`forge new` crée un projet Forge **nu**, sans starter :

```bash
forge new mon-projet
```

## 3. Activer l'environnement

Le projet généré contient son propre environnement virtuel :

```bash
cd mon-projet
source .venv/bin/activate
```

## 4. Lancer le projet

```bash
forge run
```

Ouvrez `https://localhost:8000/` : la page d'accueil du squelette s'affiche. La
route `/welcome` n'existe pas encore : vous la créerez vous-même au premier
palier. Ce parcours est un **tutoriel continu** où vous construisez, à la main,
un seul projet qui grandit palier après palier.

## 5. Vérifier l'installation

```bash
forge doctor
```

`forge doctor` contrôle l'environnement (version Python, configuration,
dépendances) de façon non invasive.

## Après l'installation

Le projet tourne : vous pouvez attaquer le premier palier de code.

[Continuer avec Bonjour Forge](debutant/welcome.md)
