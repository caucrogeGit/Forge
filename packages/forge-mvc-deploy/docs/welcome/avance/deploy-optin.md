# Opt-in CLI-only

Objectif : comprendre pourquoi Deploy est un opt-in à CLI seule.

**Ce que vous allez apprendre :** `forge-mvc-deploy` n'expose aucune API
runtime.
Il ajoute seulement deux commandes à la CLI `forge` ; une application ne
l'importe jamais à l'exécution.
S'il n'est pas installé, les commandes `deploy:*` sont simplement absentes.

Premier palier du **niveau avancé** de la progression Deploy.

!!! note "Module opt-in"
    Si `forge-mvc-deploy` n'est pas installé, les commandes `deploy:*` n'apparaissent pas.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- la forme particulière d'un opt-in à CLI seule ;
- le repli « module non installé » ;
- le rattachement à la charte (principe 8, ADR-004, ADR-053).

## 1. Aucune API runtime

```text
forge-mvc-deploy ajoute deploy:init et deploy:check à la CLI forge.
Aucun module applicatif n'importe forge_mvc_deploy à l'exécution.
Le paquet ne sert qu'à l'outillage de déploiement.
```

- L'opt-in n'expose pas de fonctions à appeler depuis vos contrôleurs ou vos modèles.
- Son seul point d'entrée est la ligne de commande : `forge deploy:init`, `forge deploy:check`.
- C'est la même forme que `forge-mvc-testing`, lui aussi réservé à l'outillage (dev-only).

## 2. Le repli « module non installé »

```bash
forge deploy:init
# si le paquet n'est pas installé : la commande est inconnue de forge
```

### Comprendre ce code

- Sans le paquet, les commandes `deploy:*` n'existent pas, sans erreur cachée.
- Installer l'opt-in les fait apparaître ; le désinstaller les retire.
- Le cœur fonctionne identiquement, que Deploy soit présent ou non.

## 3. Le rattachement à la charte

- **Principe 8, noyau minimal, briques opt-in** : l'outillage de déploiement n'alourdit pas le cœur.
- **ADR-004, périmètre du core** : le déploiement n'est pas dans le cœur minimal strict.
- **ADR-053** : décision qui fonde l'opt-in `forge-mvc-deploy` et sa forme à CLI seule.

## À retenir

- `forge-mvc-deploy` n'expose aucune API runtime : il n'ajoute que des commandes CLI.
- Sans le paquet, les commandes `deploy:*` sont absentes, sans rien casser dans le cœur.
- La forme CLI-only découle du principe 8, d'ADR-004 et d'ADR-053.

## Après ce starter

Vous comprenez la forme de l'opt-in.
Voyons l'indépendance du cœur et les déploiements alternatifs.

[Indépendance du cœur](deploy-independance.md)
