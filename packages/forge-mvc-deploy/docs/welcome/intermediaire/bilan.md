# Bilan : niveau intermédiaire (Deploy)

Récapitulatif du **niveau intermédiaire** de la progression Deploy.
Ce niveau ajoute la vérification de l'environnement et l'adaptation des gabarits.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1, [Vérifier l'environnement](deploy-check.md) | Lancer `forge deploy:check`, lire les tags `[OK]`/`[WARN]`/`[ERREUR]`, corriger `env/prod`. |
| 2, [Adapter les gabarits](deploy-templates.md) | Ajuster `User`, workers, `client_max_body_size` et chemins des gabarits Nginx et systemd. |

Vous savez diagnostiquer l'environnement de production et personnaliser les fichiers générés.

## Et ensuite

Place au niveau **avancé** : la notion d'opt-in CLI-only et l'indépendance du cœur vis-à-vis de l'outillage de déploiement.

[Niveau avancé : Opt-in CLI-only](../avance/deploy-optin.md)
