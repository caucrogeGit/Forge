# Avancé 4 : Voir les sessions ouvertes

Objectif : savoir combien de personnes sont connectées, sans ouvrir un client SQL.

## Un panneau, pas une ressource

Le tableau de bord mène à `/admin/_sessions`.
Ce n'est pas une ressource déclarée : rien à inscrire au registre, la page existe dès que le back-office est branché.

| Ce qu'il montre | Ce que cela dit |
|---|---|
| Actives | combien de personnes sont connectées, ou ont un panier en cours |
| Expirées, en attente de purge | ce que `forge sessions:gc` n'a pas encore balayé |
| Lignes en table | ce que la table coûte à chaque balayage |
| Répartition par nature | ce qui distingue une session authentifiée d'une session anonyme |

## Il demande un magasin persistant

Le panneau lit la table de `forge-mvc-sessions-db`.
Sans cet opt-in, il ne devine rien et le dit : la page s'affiche en annonçant qu'elle n'a pas de magasin à interroger.

```bash
pip install --pre forge-mvc-sqlite forge-mvc-entities forge-mvc-sessions-db
forge db:config
forge db:init
forge sessions:init
forge migration:apply
```

Cinq commandes, et aucune n'est de trop.
Le magasin est une table : il lui faut un backend, le moteur qui porte les migrations, une configuration d'environnement, une base, puis la table elle même.
Un projet qui a déjà une base saute les trois premières.

Un magasin en mémoire n'a rien à montrer : chaque travailleur a le sien, et le compte n'aurait pas de sens.

!!! danger "Aucun identifiant de session n'est affiché"
    Un identifiant de session **est** le moyen de se faire passer pour son titulaire.

    Le panneau compte, il n'expose pas : une capture d'écran d'un back-office ne doit jamais permettre d'ouvrir la session de quelqu'un.

!!! info "Une part d'expirées trop haute est signalée"
    Au delà de la moitié des lignes en attente de purge, le panneau le dit.

    C'est le signe d'un `sessions:gc` qui ne tourne pas : la table grossit, chaque lecture coûte plus cher, et rien d'autre ne l'aurait montré.

## Le geste qui va avec

Le panneau constate ; il ne purge pas.
La purge se planifie, en minuterie systemd par exemple, et le guide de déploiement en donne la paire `.service` et `.timer`.

```bash
forge sessions:gc
```

## À retenir

- Le panneau vit sur `/admin/_sessions`, sans déclaration de ressource.
- Il demande `forge-mvc-sessions-db`, et annonce son absence au lieu de se taire.
- Il ne montre aucun identifiant, et signale une purge en retard.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
