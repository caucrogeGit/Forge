# Bilan : niveau intermédiaire (RBAC)

Récapitulatif du **niveau intermédiaire** de la progression *Welcome RBAC*.
Ce niveau **applique** le contrat : vérifier, protéger, adapter l'UI.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Vérifier une permission](rbac-check.md) | Répondre « ces rôles ont-ils ce droit ? » (`has_contract_permission`). |
| 2 : [Protéger une route](rbac-guard.md) | Garde de route `403`/passage (`require_contract_permission`). |
| 3 : [Permission dans un template](rbac-template.md) | Adapter l'UI avec `can()` (`make_can`). |

Vous savez vérifier et appliquer une permission, côté route **et** interface.

## Et ensuite

Place au niveau **avancé** : relier rôles et permissions aux **utilisateurs** réels.

[Niveau avancé : Associer un rôle à un utilisateur](../avance/rbac-user-role.md)
