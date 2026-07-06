# Bilan : niveau débutant (Deploy)

Récapitulatif du **niveau débutant** de la progression Deploy.
Ce niveau pose les bases : comprendre l'opt-in et générer les fichiers de déploiement.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1, [Premier déploiement](deploy-welcome.md) | Comprendre la recette Gunicorn derrière Nginx et les deux commandes `deploy:*`. |
| 2, [Générer les fichiers](deploy-init.md) | Générer `wsgi.py` et le dossier `deploy/` avec `forge deploy:init` (write-if-new). |

Vous savez générer les fichiers de déploiement sans toucher à votre code applicatif.

## Et ensuite

Place au niveau **intermédiaire** : vérifier l'environnement de production avec `forge deploy:check`, lire les tags de résultat et adapter les gabarits.

[Niveau intermédiaire : Vérifier l'environnement](../intermediaire/deploy-check.md)
