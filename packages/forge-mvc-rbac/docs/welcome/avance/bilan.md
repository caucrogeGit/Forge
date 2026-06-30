# Bilan : niveau avancé (RBAC)

Récapitulatif du **niveau avancé** de la progression *Welcome RBAC*. Ce niveau
**relie** rôles et permissions aux utilisateurs réels.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Associer un rôle à un utilisateur](rbac-user-role.md) | Construire/valider une association user ↔ rôle (`create_auth_user_role`). |
| 2 : [Résoudre les permissions d'un utilisateur](rbac-resolve.md) | Calculer les permissions effectives via `fetch_all` injectable. |
| 3 : [Rôles de la requête](rbac-request-roles.md) | Inspecter rôles/permissions de la requête (`get_request_roles`). |

Vous maîtrisez le RBAC de bout en bout : déclarer, vérifier, appliquer, relier aux
utilisateurs.

## Et ensuite

La progression *Welcome RBAC* est terminée. En production : déclarez le contrat
`mvc/security/rbac.json`, persistez rôles et associations (`rbac`, `user_roles`),
gardez les routes (`require_*`) et adaptez l'UI (`can()`).

[Aide-mémoire de la progression RBAC](../recapitulatif.md)
