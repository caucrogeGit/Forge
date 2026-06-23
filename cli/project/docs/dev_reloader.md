# Le superviseur de développement dans Forge

Ce document décrit le superviseur de développement avec autoreload.

Le fichier de code correspondant est `cli/project/dev_reloader.py`.

## 1. À quoi sert ce module ?

Il porte la mécanique d'autoreload de `forge run` en mode développement.
Il lance `python app.py` dans un sous-processus et le redémarre dès qu'un fichier surveillé change.
Il rend aussi `forge run` résilient : l'application survit à un crash et redémarre.

L'autoreload se fait par redémarrage de processus, sans rechargement à chaud magique (principe 3).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `DevReloader` | superviseur : spawn, surveillance, redémarrage |
| `iter_watched_files(root)` | énumère les fichiers surveillés |
| `snapshot(root)` | photographie les horodatages des fichiers |
| `diff_snapshots(before, after)` | liste les fichiers modifiés entre deux photos |
| `is_ignored_path(path, root)` | indique si un chemin est exclu de la surveillance |

## 3. Contextes d'utilisation

- **Développement** : recharger l'application à chaque modification de code.
- **Résilience** : relancer automatiquement après un crash.

## 4. Voir aussi

- [La commande run](run.md) : point d'entrée qui pilote ce superviseur.
