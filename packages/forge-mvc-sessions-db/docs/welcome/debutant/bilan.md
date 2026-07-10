# Bilan : niveau débutant (Sessions BDD)

Récapitulatif du **niveau débutant** de la progression Sessions BDD.
Ce niveau pose les bases : créer la table, brancher le store, écrire une session et la retrouver après un redémarrage.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1, [Première session persistante](sessions-db-welcome.md) | Créer la table `forge_sessions`, brancher `DbSessionStore` avec `forge.configure`, créer (`create`) et relire (`get`). |
| 2, [Une session qui survit au redémarrage](sessions-db-persist.md) | Écrire avec `set`, retrouver la donnée après redémarrage, contraster avec `MemorySessionStore`. |

Vous savez brancher un store de session persistant, y écrire une donnée et la retrouver après l'arrêt du processus.

## Et ensuite

Place au niveau **intermédiaire** : partager les sessions entre plusieurs workers Gunicorn et nettoyer les sessions expirées.

[Niveau intermédiaire : Sessions partagées entre workers](../intermediaire/sessions-db-multiworker.md)
