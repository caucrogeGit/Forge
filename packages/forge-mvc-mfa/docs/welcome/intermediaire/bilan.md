# Bilan : niveau intermédiaire (MFA)

Récapitulatif du **niveau intermédiaire** de la progression *Welcome MFA*. Ce
niveau couvre le **flux** : enrôler, challenger à la connexion, récupérer.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Enrôler un facteur TOTP](mfa-enroll.md) | Créer un facteur pending puis le confirmer (`create_totp_factor`, `confirm_totp_factor`). |
| 2 : [Challenge de connexion](mfa-challenge.md) | Ouvrir et vérifier le 2e facteur en session (`start_mfa_challenge`, `verify_mfa_challenge`). |
| 3 : [Codes de récupération](mfa-recovery.md) | Générer et consommer des codes à usage unique (`create_recovery_codes`, `consume_recovery_code`). |

Vous savez dérouler le flux MFA complet, du facteur au secours.

## Et ensuite

Place au niveau **avancé** : le durcissement, avec revalidation (step-up), anti-rejeu, et
chiffrement des secrets au repos.

[Niveau avancé : Revalidation (step-up)](../avance/mfa-revalidation.md)
