# forge-mvc-mfa

Brique MFA (TOTP + codes de récupération) pour le framework Forge.

## Statut : Pre-Alpha (Forge 3.0.x)

`forge-mvc-mfa` est marqué `Development Status :: 2 - Pre-Alpha`.

**Non recommandé en production sensible** sans protection additionnelle :
le secret TOTP est actuellement stocké en clair dans la table
`auth_mfa_factors`. Voir section "Limites connues" plus bas.

Le module **n'est pas inclus** dans `forge-mvc[all]` pour cette raison.

**Mode d'installation (Forge 3.0.x)** : `forge-mvc-mfa` n'est pas encore publié
sur PyPI. Installation depuis les sources (mode dev) :

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e .
pip install -r requirements-dev.txt
```

Les extras PyPI (`forge-mvc[mfa]`) seront disponibles en 3.1 après livraison
de `SEC-MFA-SECRET-ENCRYPTION-001` (chiffrement applicatif du secret TOTP) et
`OPTIN-PYPI-PUBLISH-001` (publication des modules opt-in).

Une version stable (Beta) est planifiée pour Forge 3.1.0.

## Installation (mode source)

```bash
# Depuis le dépôt Forge (mode développement)
pip install -r requirements-dev.txt  # installe forge-mvc-mfa depuis packages/
```

`forge-mvc-mfa` dépend de `pyotp>=2.9`.

## Utilisation

```python
from forge_mvc_mfa import (
    AuthMfaFactor,
    create_totp_factor,
    confirm_totp_factor,
    verify_mfa_challenge,
    is_mfa_enabled,
)
```

L'API complète est exposée directement depuis `forge_mvc_mfa`.
Les fonctions privées (`_persist_session_changes`, `_session_user_matches`)
doivent être importées depuis `forge_mvc_mfa.mfa`.

## SQL

Les tables nécessaires se trouvent dans `sql/` :

- `sql/auth_mfa_factors.sql` — facteurs TOTP
- `sql/auth_mfa_recovery_codes.sql` — codes de récupération

Appliquer via `db:apply` ou directement sur la base.

## Compatibilité

Disponible séparément depuis Forge 2.4.0 (ADR-004, MFA-EXTRACT-001).
Les anciens chemins `core.auth.mfa`, `core.auth.recovery` et
`core.auth.totp_replay` ont été retirés en Forge 3.0.

## Limites connues

- Le secret TOTP est stocké en clair dans la base (pas de chiffrement applicatif).
  Chiffrement prévu : `SEC-MFA-SECRET-ENCRYPTION-001` (Forge 3.1.0).
- Le store anti-replay et le rate-limit sont in-memory process-local.
  En multi-worker, utiliser des sticky sessions.
