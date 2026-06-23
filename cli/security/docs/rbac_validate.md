# La commande rbac:validate dans Forge

Ce document décrit la commande `forge rbac:validate`.

Le fichier de code correspondant est `cli/security/rbac_validate.py`.

## 1. À quoi sert cette commande ?

`forge rbac:validate` valide le contrat RBAC du projet, `mvc/security/rbac.json`, contre `schemas/rbac.schema.json`.
Le fichier est optionnel : son absence n'est pas une erreur.

C'est une validation de **structure** : conformité au schéma JSON.
La cohérence fonctionnelle (rôles vides, permissions inutilisées…) relève de [`rbac:audit`](rbac_audit.md).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `rbac_validate_main(args)` | point d'entrée de la commande `forge rbac:validate` |

L'option `--json` produit une sortie machine stable sur `stdout`, sans ligne lisible par un humain.

Codes de retour :

- `0` : fichier absent (RBAC optionnel) ou fichier valide.
- `1` : fichier présent mais invalide, ou erreur de chargement du schéma.

## 3. Contextes d'utilisation

- **Garde-fou** : vérifier la conformité du contrat RBAC avant déploiement.
- **CI** : faire échouer un pipeline sur un `rbac.json` malformé.

## 4. Voir aussi

- [La commande rbac:audit](rbac_audit.md) : cohérence fonctionnelle du contrat.
- [Les commandes auth:*](auth.md) : socle d'authentification et comptes.
