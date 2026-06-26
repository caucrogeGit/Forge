# Bilan : niveau intermédiaire (Jobs)

Récapitulatif du **niveau intermédiaire** de la progression Jobs.
Ce niveau sépare les deux côtés : un process worker traite la file, et les
tâches savent réessayer en cas d'échec.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1, [Le process worker](jobs-worker.md) | Lancer `run_worker` dans un process séparé ; enfiler côté web, traiter côté worker. |
| 2, [Réessais et inspection](jobs-retry.md) | Régler `max_attempts` ; inspecter avec `get_job` et `pending_count`. |

Vous savez faire tourner un worker et suivre l'état des tâches.

## Et ensuite

Place au niveau **avancé** : savoir quand recourir à une file, comprendre le
modèle sans broker, et connaître les limites de la version actuelle.

[Niveau avancé : Quand utiliser Jobs](../avance/jobs-perimeter.md)
