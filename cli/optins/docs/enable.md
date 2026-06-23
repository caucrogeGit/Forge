# La commande opt-in:enable dans Forge

Ce document décrit la commande `forge opt-in:enable <name>`.

Le fichier de code correspondant est `cli/optins/enable.py`.

## 1. À quoi sert cette commande ?

`opt-in:enable` agit sur l'axe **activation** (ADR-016).
Pour un opt-in de *kind* `route`, elle branche la brique dans le projet en créant la couche `optins/<name>/` et en enregistrant `register_optins` dans `mvc/routes.py`.

Le contrat est strict :

- **dry-run par défaut** : sans `--apply`, rien n'est écrit ;
- **idempotence** : fichier absent créé, présent identique signalé `[OK]`, présent différent signalé `[WARN]` sans écriture ;
- **jamais d'écrasement silencieux** (principe 9) ;
- **pas de discovery magique** : le branchement reste explicite.

Pour les opt-ins non routiers, la commande informe au lieu d'écrire (voir [conseils](guidance.md)).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `register_optins(router)` | enregistre les routes des opt-ins branchés |
| `main(args=None)` | point d'entrée de la commande `forge opt-in:enable` |

## 3. Contextes d'utilisation

- **Branchement d'un opt-in routier** : intégrer `iot` au projet.
- **Prévisualisation** : voir les écritures prévues avant `--apply`.

## 4. Voir aussi

- [La commande opt-in:disable](disable.md) : inverse exact.
- [La commande opt-in:list](list.md) : état local des opt-ins.
