# Les exceptions Auth dans Forge

Ce document décrit la hiérarchie d'exceptions du module d'authentification.

Le fichier de code correspondant est `core/auth/exceptions.py`.

## 1. À quoi sert ce module ?

Le module auth distingue ses erreurs pour que l'application réagisse précisément (utilisateur invalide, mot de passe refusé, contrat d'audit ou de rate-limit non respecté…).
Toutes héritent de `AuthError`.

## 2. La hiérarchie

| Exception | Cas |
|---|---|
| `AuthError` | erreur de base du module auth |
| `InvalidAuthUserError` | données utilisateur incomplètes ou invalides |
| `InvalidNewPasswordError` | nouveau mot de passe invalide |
| `InvalidAuthAuditEventError` | événement d'audit invalide |
| `InvalidAuthRateLimitAttemptError` | tentative de rate-limit invalide |
| `InvalidAuthRateLimitRuleError` | règle de rate-limit invalide |
| `InvalidMfaFactorError` | données de facteur MFA invalides |
| `InvalidMfaRecoveryCodeError` | données de code de récupération MFA invalides |

## 3. Contextes d'utilisation

- **Validation de contrat** : levées par les `validate_*` des modules auth.

## 4. Voir aussi

- [Le contrat utilisateur](user.md), [l'audit](audit.md), [le rate-limit](rate_limit.md).
