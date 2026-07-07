# La commande skeleton:upgrade dans Forge

Cette page décrit `forge skeleton:upgrade`, qui met à jour le squelette d'un projet existant.

Le code correspondant est `cli/commands/skeleton_upgrade.py`, sous-paquet CLI commands regroupé par l'ADR-043.

## 1. Rôle

`forge new` crée un projet à partir du squelette, mais rien ne le met à jour quand Forge évolue et enrichit ce squelette (nouvel outillage, configuration qualité).

`skeleton:upgrade` comble ce manque : il ajoute au projet courant les fichiers du squelette qui lui manquent.

## 2. Write-if-new strict

La commande n'écrit que les fichiers **absents** du projet.

Elle ne modifie ni ne supprime jamais un fichier existant : aucune édition utilisateur n'est perdue.

Les fichiers substitués à la création (`env/*`, nom applicatif) préexistent dans tout projet et sont donc préservés : `skeleton:upgrade` n'a rien à substituer.

## 3. Options

- `--check` : liste les fichiers qui seraient ajoutés, sans rien écrire (mode revue) ;
- `--bare` : ignore l'apparat qualité, comme `forge new --bare` (ADR-063).

## 4. Limites

- hors d'un projet Forge (ni `config.py` ni `mvc/`), la commande s'arrête proprement ;
- elle ne met pas à jour le **contenu** d'un fichier déjà présent (write-if-new strict) ;
- elle ne re-télécharge pas `forge-mvc` : un pin git à version inchangée n'est pas re-récupéré par pip sans `--force-reinstall`.

## Voir aussi

- [Commandes CLI](../reference/cli-commands.md) : vue d'ensemble.
