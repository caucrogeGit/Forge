# Aide-mémoire de la progression MFA

Récapitulatif des paliers de la progression *Bonjour Forge MFA* et des API du module
opt-in `forge-mvc-mfa` introduites à chaque étape.

!!! note "Module opt-in"
    `forge-mvc-mfa` est **publié sur PyPI** (Alpha) : `pip install --pre forge-mvc-mfa`.
    Il exige `FORGE_MFA_SECRET_KEY` (Fernet) pour chiffrer les secrets. Ce parcours
    montre chaque brique **isolée** ; le flux câblé vit dans `welcome-optin-mfa`.

## Niveau débutant — mécaniques TOTP (sans état)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Bonjour Forge MFA](debutant/mfa-welcome.md) | Inspecter facteurs, statuts, clé | `validate_mfa_secret_key_config` |
| 2 | [Secret TOTP et QR](debutant/mfa-secret.md) | Générer secret + URI `otpauth://` | `generate_totp_secret`, `totp_provisioning_uri` |
| 3 | [Vérifier un code TOTP](debutant/mfa-verify.md) | Confronter code et secret | `verify_totp_code` |

## Niveau intermédiaire — enrôlement & flux de connexion (session)

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Enrôler un facteur TOTP](intermediaire/mfa-enroll.md) | Créer pending puis confirmer | `create_totp_factor`, `confirm_totp_factor` |
| 2 | [Challenge de connexion](intermediaire/mfa-challenge.md) | Second facteur au login | `start_mfa_challenge`, `verify_mfa_challenge` |
| 3 | [Codes de récupération](intermediaire/mfa-recovery.md) | Codes de secours à usage unique | `create_recovery_codes`, `consume_recovery_code` |

## Niveau avancé — durcissement

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Revalidation (step-up)](avance/mfa-revalidation.md) | Exiger une MFA récente | `mark_mfa_revalidated`, `require_recent_mfa` |
| 2 | [Anti-rejeu TOTP](avance/mfa-replay.md) | Empêcher le rejeu d'un code | `record_used`, `is_replay` |
| 3 | [Secret chiffré au repos](avance/mfa-crypto.md) | Chiffrer les secrets (Fernet) | `encrypt_totp_secret`, `decrypt_totp_secret` |
