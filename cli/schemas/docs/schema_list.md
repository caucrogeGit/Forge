# La commande schema:list dans Forge

Ce document décrit la commande `forge schema:list`.

Le fichier de code correspondant est `cli/schemas/schema_list.py`.

## 1. À quoi sert cette commande ?

`forge schema:list` liste les schémas JSON Forge disponibles localement.
Elle lit le registre `schemas/forge.schema.index.json`.
Pour chaque schéma référencé, elle affiche son chemin relatif et son statut (`OK` / `MANQUANT`).

C'est une commande en lecture seule : elle n'écrit ni ne modifie aucun fichier.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `schema_list_main(args)` | point d'entrée de la commande `forge schema:list` |

L'option `--json` produit une sortie machine stable sur `stdout`, sans ligne lisible par un humain.

Codes de retour :

- `0` : registre lisible et tous les schémas présents.
- `1` : registre illisible ou au moins un schéma manquant.

## 3. Contextes d'utilisation

- **Inventaire** : savoir quels schémas JSON Forge sont embarqués dans le projet.
- **Pré-diagnostic** : repérer un schéma manquant avant un `schema:doctor`.
- **Outillage** : la sortie `--json` alimente un script ou un pipeline.

## 4. Voir aussi

- [La commande schema:doctor](schema_doctor.md) : diagnostic approfondi des schémas (validité, `$ref`).
