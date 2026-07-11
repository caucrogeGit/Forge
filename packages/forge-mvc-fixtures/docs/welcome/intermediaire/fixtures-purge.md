# Repartir d'un état propre

Objectif : vider les tables peuplées par les fixtures avec `forge fixtures:purge`.

**Ce que vous allez apprendre :** la purge dérive les tables cibles de vos fixtures et affiche les `DELETE` avant de les exécuter.

## Pourquoi purger

En développement, vous voulez souvent repartir d'une base propre : effacer les données d'essai avant de recharger un jeu à jour.
`fixtures:purge` fait exactement cela, sans toucher au schéma.

## Voir avant de vider

Lancez la commande **sans option** :

```bash
forge fixtures:purge
```

Elle lit vos fixtures, en **déduit** les tables ciblées (les `INSERT INTO`), et **affiche** les `DELETE FROM` qu'elle exécuterait.
Rien n'est caché : vous voyez les tables qui seront vidées avant que ce soit fait.

## Vider

```bash
forge fixtures:purge --run
```

Les `DELETE` sont exécutés dans l'**ordre inverse** du chargement : les tables qui en référencent d'autres sont vidées en premier, pour respecter les clés étrangères.

## Le cycle de travail

1. `forge fixtures:load --run` pour charger.
2. Travailler, tester, casser des choses.
3. `forge fixtures:purge --run` pour vider.
4. Recharger, et ainsi de suite.

C'est la boucle rejouable qui distingue une fixture d'une migration.

## Ce que la purge ne fait pas

Elle ne supprime pas les tables (pas de `DROP`), ne touche pas au schéma, et ne vide que les tables que vos fixtures peuplent.

## Commandes utilisées

| Commande | Rôle |
|---|---|
| `forge fixtures:purge` | Affiche les `DELETE` dérivés des fixtures (aucun effet). |
| `forge fixtures:purge --run` | Vide les tables ciblées dans l'environnement actif. |

## La suite

Voyons comment tout cela se cadre par environnement, et pourquoi la production est protégée.

[Continuer : cadrer par environnement](fixtures-env.md)
