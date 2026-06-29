# Les commandes auth:* dans Forge

Ce document décrit la famille de commandes `forge auth:*` (socle d'authentification et gestion des utilisateurs).

Le fichier de code correspondant est `cli/security/auth.py`.

## 1. À quoi servent ces commandes ?

Ces commandes installent le socle d'authentification et administrent les comptes utilisateurs locaux.
L'authentification est optionnelle dans Forge : ces commandes ne s'imposent qu'aux projets qui en ont besoin.

Les écritures de fichiers SQL suivent le mode write-if-new : un fichier existant n'est jamais écrasé (principe 9).
Les opérations base de données utilisent les identifiants d'administration (`DB_ADMIN_*`).

## 2. L'API

| Commande | Rôle |
|---|---|
| `auth:init` | crée le SQL optionnel des tables d'authentification |
| `auth:list-sql` | liste les fichiers SQL d'authentification connus |
| `auth:status` | affiche l'état fonctionnel du socle |
| `auth:doctor` | diagnostique le socle sans accès base |
| `auth:user:create` | crée un compte utilisateur local |
| `auth:user:list` | liste les comptes (sans secret) |
| `auth:user:show` | affiche un compte (sans secret) |
| `auth:user:disable` / `auth:user:enable` | désactive ou réactive un compte |
| `auth:user:password` | change le mot de passe d'un compte |
| `auth:user:role:add` / `auth:user:role:remove` | attribue ou retire un rôle RBAC |
| `auth:user:roles` | liste les rôles attribués à un compte |

Les tables couvertes incluent `users`, `auth_tokens`, `auth_mfa_factors`, `auth_mfa_recovery_codes`, `user_roles`, `auth_audit_log` et `auth_rate_limit_attempts`.

## 3. Contextes d'utilisation

- **Mise en place** : `auth:init` puis `auth:doctor` pour vérifier l'installation.
- **Administration** : créer, lister, désactiver des comptes en ligne de commande.
- **Rôles** : associer des rôles RBAC existants à un utilisateur.

## 4. Voir aussi

- Les commandes `rbac:validate` et `rbac:audit` sont fournies par l'opt-in `forge-mvc-rbac` (ADR-056) : voir la documentation du paquet.
