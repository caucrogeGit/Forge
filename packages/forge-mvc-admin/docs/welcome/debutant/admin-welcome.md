# Débutant 1 : Voir le tableau de bord

Objectif : ouvrir le back-office et comprendre ce qu'il affiche au départ.

## Accéder à `/admin`

Le branchement de l'installation a ajouté la route `GET /admin`.
Démarrez le projet, connectez-vous, puis ouvrez `/admin`.

La route n'est **pas publique** : un visiteur non authentifié est redirigé vers la page de connexion.
C'est la première garantie de sécurité du back-office.

## Ce que vous voyez

Le tableau de bord liste les **ressources administrables**.
Tant qu'aucune ressource n'est déclarée, il affiche un message d'invite :

```text
Aucune ressource déclarée.
Déclarez vos ressources dans mvc/admin/resources.py.
```

C'est normal : `forge admin:init` a créé un `resources.py` qui ne déclare encore rien.
Le prochain palier corrige cela.

## À retenir

- Le back-office vit sous `/admin`.
- Il n'est jamais public : l'authentification est exigée.
- Il n'affiche que ce que vous déclarez, jamais toutes les tables par surprise.

## Étape suivante

[Suivant : déclarer une ressource](admin-resource.md)
