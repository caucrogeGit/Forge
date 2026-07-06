# Installation de forge-mvc-jobs

Objectif : installer l'opt-in Jobs et préparer sa table.

Le parcours qui suit montre, en trois niveaux, comment enfiler une tâche depuis un contrôleur, la traiter dans un gestionnaire, lancer un process worker séparé, puis comprendre quand recourir à une file de tâches.

`forge-mvc-jobs` déporte un travail lourd hors de la requête HTTP.
La requête enfile une tâche et répond tout de suite ; un worker distinct la traite plus tard.

## Installer le paquet

```bash
pip install --pre forge-mvc-jobs
```

En développement, depuis le dépôt, vous pouvez aussi l'installer en mode éditable :

```bash
pip install -e packages/forge-mvc-jobs
```

Le paquet dépend du cœur `forge-mvc`.
La file est une simple table MariaDB ; il n'y a ni broker, ni Celery, ni Redis, ni code asynchrone.

## Créer la table des tâches

Les tâches sont stockées dans une table `jobs`.
Forge la crée via une migration :

```bash
forge jobs:init
forge migration:apply
```

`forge jobs:init` dépose la migration de la table `jobs`.
`forge migration:apply` exécute cette migration sur votre base.

## Vérifier l'installation

```python
from forge_mvc_jobs import pending_count

print(pending_count(), "tâche(s) en attente")
```

Si ce script affiche un nombre (zéro au départ), l'opt-in fonctionne et la table est en place.

## Après cette étape

Place au niveau débutant : enfiler votre première tâche.

[Niveau débutant : Première tâche en file](debutant/jobs-welcome.md)
