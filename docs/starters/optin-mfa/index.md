# MFA (opt-in)

Le sujet **MFA (opt-in)** regroupe les starters d'entrée dans
l'authentification multi-facteurs de Forge, portée par le module
opt-in [`forge-mvc-mfa`](../../reference/auth-mfa.md).

Comme tout opt-in Forge, MFA n'est **jamais** activé automatiquement :
le projet installe `forge-mvc-mfa` explicitement (hors `forge-mvc[all]`)
et applique le starter pour câbler le challenge TOTP au flux de
connexion.

## Parcours

| Niveau | Starter | Objectif |
|--------|---------|----------|
| Premier contact | [Auth MFA (TOTP) — `welcome-optin-mfa`](welcome-optin-mfa.md) | Challenge TOTP intercalé entre le mot de passe et l'ouverture de session ; remplace deux contrôleurs sans toucher aux entités ni à `mvc/routes.py`. |

Un seul niveau pour l'instant ; le parcours s'étoffera au fil des
tickets MFA.

## Pour aller plus loin

- [Documentation de référence MFA](../../reference/auth-mfa.md)
- [Reconstruction du starter](welcome-optin-mfa-rebuild.md)
