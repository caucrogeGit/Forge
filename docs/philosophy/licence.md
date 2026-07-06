# Licence de Forge

## Statut actuel

Forge est distribué sous **licence propriétaire / source disponible**.

Forge n'est pas un logiciel open source.
Le code source est rendu disponible pour lecture, étude et évaluation, mais son utilisation professionnelle ou commerciale nécessite une autorisation écrite préalable.

## Usages autorisés sans autorisation écrite

- lire le code source ;
- étudier le fonctionnement du framework ;
- évaluer Forge à titre personnel avant une éventuelle demande d'autorisation ;
- utiliser Forge dans un cadre éducatif personnel ou pédagogique non commercial.

## Usages interdits sans autorisation écrite

- usage professionnel, quel que soit le secteur ;
- usage commercial ou monétisé, direct ou indirect ;
- usage institutionnel (entreprise, administration, association, école) ;
- prestation client intégrant Forge ;
- intégration dans un produit, service ou SaaS déployé pour un tiers ;
- redistribution du code source, modifié ou non ;
- publication d'une version dérivée ou modifiée ;
- vente, location ou sous-licence de Forge.

## Pourquoi cette licence ?

Forge est encore en phase de construction active.
La licence actuelle permet de partager le code pour étude et évaluation, tout en conservant le contrôle sur les usages professionnels pendant la maturation du framework.

Cette approche est courante pour les frameworks en développement qui souhaitent rester ouverts à l'examen sans autoriser l'exploitation commerciale avant d'être prêts.

## Trajectoire de licence

Pendant toute sa phase bêta, Forge reste sous licence propriétaire / source disponible : ce n'est pas un logiciel open source aujourd'hui.

À partir de la version 1.0.0 stable, Forge bascule sous licence open source MIT.
Cette trajectoire n'est plus suspendue à un jalon indéfini : la bascule intervient dès que les conditions ci-dessous, toutes vérifiables, sont réunies, et au plus tard le **31 décembre 2026** :

- une release candidate `1.0.0-rc1` publiée ;
- au moins deux mois de tests terrain après la bêta consolidée (T0, ADR-009) sans changement d'API publique ;
- aucun bloquant de sécurité ouvert (un avis sans correctif amont, documenté et accepté dans `SECURITY.md`, n'est pas bloquant) ;
- suite de tests verte et portes CI au vert (pyright, pip-audit, mkdocs strict).

MIT dès que c'est solide, et au plus tard à la date plafond.

Jusqu'à cette publication, la licence présente dans le dépôt au moment de la récupération fait foi : toute version récupérée avant la 1.0.0 stable reste soumise à la licence propriétaire / source disponible.

## Fichier de référence

Le texte complet de la licence se trouve dans le fichier `LICENSE` à la racine du dépôt.

## Contact

Pour toute demande d'autorisation d'usage professionnel ou commercial, contacter Roger Lequette directement.
