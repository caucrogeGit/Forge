# Installation

[Accueil](index.html){ .md-button } <button class="md-button" onclick="window.history.back()">← Retour</button>

Forge peut s'installer de plusieurs façons selon votre contexte. Choisissez le
chemin le plus simple pour votre usage, puis passez au [guide de démarrage](guide.md).

## Chemins recommandés

| Usage | Méthode |
|---|---|
| Préparer une machine complète | [Installation sur une VM Debian vierge](installation-vm-debian.md) |
| Utiliser Forge comme outil installé | [Installation avec pipx](installation-pipx.md) |
| Créer un projet depuis une version stable | [Installation depuis GitHub](installation-github.md) |
| Contribuer au framework Forge | [Mode développement](installation-developpement.md) |
| Préparer la base locale | [Préparer MariaDB](installation-mariadb.md) |

## Version stable

Forge 1.0.1 utilise la référence stable `v1.0.1` par défaut.

```bash
forge --version
forge new MonProjet
```

Pour travailler explicitement depuis la branche de développement :

```bash
forge new MonProjet --ref main
```

## Après installation

Une fois Forge disponible :

```bash
cd MonProjet
source .venv/bin/activate
forge doctor
```

Le guide suivant couvre la création d'une première entité et d'un CRUD complet.
