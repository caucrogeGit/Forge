# Auth (API cœur)

Le sujet **Auth (API cœur)** regroupe les starters qui s'appuient sur le
module d'authentification du cœur Forge — l'API [`core.auth`](../../features/auth.md) —
pour bâtir un flux de connexion applicatif minimal.

Contrairement aux opt-ins, `core.auth` est **toujours disponible** dans Forge :
hachage Argon2, vérification de mot de passe, session Auth/User et décorateur
`@login_required` sont fournis par le cœur. Le starter câble ces API dans une
petite application navigable (accueil public, login, dashboard protégé, profil,
logout) sans rien installer en plus.

## Parcours

| Niveau | Starter | Objectif |
|--------|---------|----------|
| Intermédiaire | [Auth minimal moderne — `users-core-auth`](users-core-auth.md) | Login, sessions, routes publiques/protégées et CSRF à partir de l'API cœur `core.auth` ; crée l'entité `Utilisateur` et injecte les routes explicites. |

Un seul niveau pour l'instant ; le parcours s'étoffera au fil des tickets Auth.

## Pour aller plus loin

- [Documentation de référence Auth](../../features/auth.md)
- [Reconstruction du starter](users-core-auth-rebuild.md)
