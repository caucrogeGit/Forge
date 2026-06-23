# La commande opt-in:disable dans Forge

Ce document décrit la commande `forge opt-in:disable <name>`.

Le fichier de code correspondant est `cli/optins/disable.py`.

## 1. À quoi sert cette commande ?

`opt-in:disable` est l'inverse exact d'`opt-in:enable` sur l'axe **activation** (ADR-016).
Elle retire la couche de câblage `optins/<name>/` et débranche `register_optins` de `mvc/routes.py`.

Elle laisse le **package installé** : pour désinstaller, voir [`opt-in:remove`](remove.md).

Le contrat reste strict : dry-run par défaut, `--apply` pour écrire.
Un fichier modifié à la main par l'utilisateur est **conservé**, jamais supprimé en silence (principe 9).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `disable_optin(name, *, apply, project_root)` | débranche l'opt-in du projet |
| `main(args=None)` | point d'entrée de la commande `forge opt-in:disable` |

## 3. Contextes d'utilisation

- **Débranchement** : retirer un opt-in routier sans toucher au package.
- **Prévisualisation** : voir les suppressions prévues avant `--apply`.

## 4. Voir aussi

- [La commande opt-in:enable](enable.md) : inverse exact.
- [La commande opt-in:remove](remove.md) : désinstallation du package.
