# Bilan : niveau avancé (MFA)

Récapitulatif du **niveau avancé** de la progression *Bonjour Forge MFA*. Ce niveau
couvre le **durcissement** : revalidation, anti-rejeu, chiffrement au repos.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Revalidation (step-up)](mfa-revalidation.md) | Exiger une MFA récente avant une action sensible. |
| 2 : [Anti-rejeu TOTP](mfa-replay.md) | Refuser le rejeu d'un même code (`record_used`, `is_replay`). |
| 3 : [Secret chiffré au repos](mfa-crypto.md) | Chiffrer/déchiffrer les secrets (`encrypt_totp_secret`). |

Vous maîtrisez les briques MFA, de la génération du secret au durcissement.

## Et ensuite

La progression *Bonjour Forge MFA* est terminée. Chaque brique a été vue isolément ;
à vous de les **câbler dans votre flux Auth** en suivant l'ordre des paliers.
En production, persistez facteurs et codes (`auth_mfa_factors`,
`auth_mfa_recovery_codes`) et appelez `validate_mfa_secret_key_config` au démarrage.

[Aide-mémoire de la progression MFA](../recapitulatif.md)
