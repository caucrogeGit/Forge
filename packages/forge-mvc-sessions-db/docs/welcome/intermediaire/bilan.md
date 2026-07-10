# Bilan : niveau intermédiaire (Sessions BDD)

Récapitulatif du **niveau intermédiaire** de la progression Sessions BDD.
Ce niveau ajoute le partage entre workers et l'entretien de la table dans le temps.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1, [Sessions partagées entre workers](sessions-db-multiworker.md) | Comprendre le multi-worker Gunicorn ; partager l'état via la base avec `DbSessionStore`. |
| 2, [Nettoyer les sessions expirées](sessions-db-cleanup.md) | Supprimer les sessions expirées avec `cleanup_expired()` depuis un cron applicatif. |

Vous savez déployer un store de session en multi-worker et garder sa table propre.

## Et ensuite

Place au niveau **avancé** : la portabilité du SQL sur tous les backends et l'injection des exécuteurs pour tester.

[Niveau avancé : Un SQL portable, tous backends](../avance/sessions-db-portable.md)
