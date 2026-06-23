# La commande opt-in:list dans Forge

Ce document décrit la commande `forge opt-in:list`.

Le fichier de code correspondant est `cli/optins/list.py`.

## 1. À quoi sert cette commande ?

`opt-in:list` affiche l'**état local** des opt-ins connus dans un projet Forge.
Elle est **strictement en lecture seule** : elle ne crée, ne modifie et n'installe rien.

Elle inspecte seulement le **texte** de quelques fichiers connus (`optins/` et `mvc/routes.py`).
Elle n'importe aucun paquet `forge_mvc_*` : elle ne lit que le catalogue statique.
Pas de discovery magique : seuls les opt-ins de *kind* `route` (`iot`, `video`, `audio`) reçoivent une couche `optins/<name>/`.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `list_optins(*, project_root)` | affiche l'état local de tous les opt-ins |
| `detect_optin_state(project_root, name)` | analyse l'état d'un opt-in routier |
| `main(argv=None)` | point d'entrée de la commande `forge opt-in:list` |

## 3. Contextes d'utilisation

- **État des lieux** : savoir quels opt-ins sont branchés dans le projet.
- **Diagnostic** : repérer un câblage incomplet sans rien modifier.

## 4. Voir aussi

- [Le catalogue des opt-ins](catalog.md) : source des opt-ins connus.
- [La commande opt-in:enable](enable.md) : branchement local.
