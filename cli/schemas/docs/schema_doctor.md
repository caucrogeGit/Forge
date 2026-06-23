# La commande schema:doctor dans Forge

Ce document décrit la commande `forge schema:doctor`.

Le fichier de code correspondant est `cli/schemas/schema_doctor.py`.

## 1. À quoi sert cette commande ?

`forge schema:doctor` diagnostique les schémas JSON Forge référencés dans `forge.schema.index.json`.
Pour chaque schéma, elle vérifie cinq points :

1. le fichier existe ;
2. le fichier est du JSON valide ;
3. la clé `$schema` est présente et pointe vers le Draft 2020-12 ;
4. la clé `$id` est présente ;
5. les `$ref` locaux (hors `#` interne et `http` distant) pointent vers des fichiers existants.

Elle ne valide pas les entités utilisateur (`mvc/entities/*.json`).
Cette validation-là relève de `forge entity:validate`.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `schema_doctor_main(args)` | point d'entrée de la commande `forge schema:doctor` |

L'option `--json` produit une sortie machine stable sur `stdout`, sans ligne lisible par un humain.

Codes de retour :

- `0` : aucune erreur.
- `1` : au moins une erreur (registre illisible, schéma absent ou invalide, `$ref` mort).

## 3. Contextes d'utilisation

- **Intégrité** : vérifier que les schémas embarqués sont valides et cohérents.
- **CI** : le code de retour non nul fait échouer un pipeline en cas de schéma cassé.
- **Maintenance** : détecter un `$ref` mort après un renommage de schéma.

## 4. Voir aussi

- [La commande schema:list](schema_list.md) : inventaire des schémas et de leur présence.
