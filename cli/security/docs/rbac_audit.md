# La commande rbac:audit dans Forge

Ce document décrit la commande `forge rbac:audit`.

Le fichier de code correspondant est `cli/security/rbac_audit.py`.

## 1. À quoi sert cette commande ?

`forge rbac:audit` vérifie la **cohérence fonctionnelle** du contrat RBAC `mvc/security/rbac.json`.
Elle signale par exemple les rôles sans permissions, les entités sans actions CRUD, les permissions non déclarées dans les entités ou inutilisées par les rôles.
Le fichier est optionnel : son absence n'est pas une erreur.

Contrairement à [`rbac:validate`](rbac_validate.md) qui contrôle la structure, cette commande contrôle le sens.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `rbac_audit_main(args)` | point d'entrée de la commande `forge rbac:audit` |

L'option `--json` produit une sortie machine stable sur `stdout`, sans ligne lisible par un humain.

Codes de retour :

- `0` : fichier absent, ou fichier valide (avec ou sans avertissements).
- `1` : fichier présent mais invalide (JSON ou schéma), ou option inconnue.

## 3. Contextes d'utilisation

- **Revue de droits** : repérer les incohérences avant une montée en charge des rôles.
- **Hygiène** : détecter les permissions orphelines ou les rôles inertes.

## 4. Voir aussi

- [La commande rbac:validate](rbac_validate.md) : validation structurelle du contrat.
- [Les commandes auth:*](auth.md) : socle d'authentification et comptes.
