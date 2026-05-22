# forge-mvc-mfa

Brique MFA (TOTP + codes de récupération) pour le framework Forge.

## Statut : Pre-Alpha (Forge 3.0.x) — chiffrement Fernet livré

`forge-mvc-mfa` est marqué `Development Status :: 2 - Pre-Alpha`.

Depuis `SEC-MFA-SECRET-ENCRYPTION-001`, **le secret TOTP est chiffré au repos**
via Fernet (`cryptography`). La clé est lue depuis `FORGE_MFA_SECRET_KEY` —
obligatoire au démarrage.

Le module **n'est pas inclus** dans `forge-mvc[all]`. La requalification Beta
est prévue dans `MFA-PYPI-READY-001`.

**Mode d'installation (Forge 3.0.x)** : `forge-mvc-mfa` n'est pas encore publié
sur PyPI. Installation depuis les sources (mode dev) :

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e .
pip install -r requirements-dev.txt
```

### Configuration requise

```bash
# Générer une clé Fernet (à stocker dans .env ou un gestionnaire de secrets)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Ajouter dans `.env` :

```
FORGE_MFA_SECRET_KEY=<clé générée ci-dessus>
```

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

- Le store anti-replay et le rate-limit sont in-memory process-local.
  En multi-worker, utiliser des sticky sessions.
- La politique de rotation et la procédure de sauvegarde/restauration de la
  clé Fernet ne sont pas encore formalisées (exigences Beta restantes).
