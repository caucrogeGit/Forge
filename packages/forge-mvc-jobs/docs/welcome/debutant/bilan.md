# Bilan : niveau débutant (Jobs)

Récapitulatif du **niveau débutant** de la progression Jobs.
Ce niveau pose les bases : enfiler une tâche depuis un contrôleur, puis la
traiter avec un gestionnaire.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1, [Première tâche en file](jobs-welcome.md) | Enfiler une tâche avec `enqueue` ; la requête répond tout de suite. |
| 2, [Définir un gestionnaire](jobs-handler.md) | Écrire un gestionnaire, le placer dans `handlers`, vider la file avec `drain`. |

Vous savez enfiler une tâche côté requête et la traiter côté gestionnaire.

## Et ensuite

Place au niveau **intermédiaire** : lancer un process worker séparé qui traite
la file en continu, indépendamment du serveur web.

[Niveau intermédiaire : Le process worker](../intermediaire/jobs-worker.md)
