# forge-mvc-mfa

Brique MFA (TOTP + codes de récupération) pour le framework Forge.

## Statut : Alpha — opt-in officiel publié sur PyPI depuis 1.0.0-beta.9

`forge-mvc-mfa` est marqué `Development Status :: 3 - Alpha` depuis
`MFA-PYPI-READY-001`.

Depuis `SEC-MFA-SECRET-ENCRYPTION-001`, **le secret TOTP est chiffré au repos**
via Fernet (`cryptography`). La clé est lue depuis `FORGE_MFA_SECRET_KEY` —
obligatoire au démarrage.

Le module est **publié sur PyPI** depuis `1.0.0-beta.9` (forme PEP 440 :
`1.0.0b9`). Il reste **hors** de `forge-mvc[all]` (statut Alpha) — installer
le paquet directement. Le passage Alpha → Beta reste un ticket futur,
indépendant de la publication PyPI déjà effectuée.

Installation :

```bash
pip install --pre forge-mvc-mfa
```

Pour développer le paquet en mode éditable depuis les sources du dépôt Forge :

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
pip install -e .
pip install -r requirements-dev.txt
```

### Configuration requise — `FORGE_MFA_SECRET_KEY`

`forge-mvc-mfa` chiffre les secrets TOTP au repos via Fernet et exige une
clé valide dans l'environnement. Forge refuse explicitement les valeurs
absentes, vides, ou placeholder (`change-me`, `default`, `dev`, `secret`,
`test`, …) — voir `MFA-SECRET-KEY-BOOT-VALIDATION-001`.

```bash
# Générer une clé Fernet (à stocker dans .env ou un gestionnaire de secrets).
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Ajouter dans `.env` :

```
FORGE_MFA_SECRET_KEY=<clé générée ci-dessus>
```

**Ne JAMAIS commiter cette clé dans le dépôt.** Utiliser `.env`,
un gestionnaire de secrets (Vault, AWS Secrets Manager, etc.) ou les
variables d'environnement du runtime de production.

### Validation au démarrage

Pour échouer **tôt** en production plutôt qu'à la première opération
MFA, appeler la validation explicite au boot de l'application :

```python
from forge_mvc_mfa import validate_mfa_secret_key_config

# Au démarrage de l'application — par exemple dans app.py ou wsgi.py.
# Lève MfaSecretKeyMissing / MfaSecretKeyPlaceholder / MfaSecretInvalidKey
# avec un message d'erreur exploitable. Aucune valeur de clé n'est loguée.
validate_mfa_secret_key_config()
```

MFA reste **opt-in** : Forge ne force pas cette validation au niveau du
core. C'est l'application qui choisit de l'appeler quand elle active MFA.
Une application qui installe `forge-mvc-mfa` mais ne l'utilise pas n'est
jamais bloquée.

### Exceptions levées

| Exception | Cause |
|---|---|
| `MfaSecretKeyMissing` | `FORGE_MFA_SECRET_KEY` absent ou vide |
| `MfaSecretKeyPlaceholder` | valeur reconnue comme placeholder (`change-me`, etc.) |
| `MfaSecretInvalidKey` | format Fernet invalide (longueur ou base64) |

Aucune de ces exceptions ne contient la valeur de la clé tentée — pour
éviter de fuir un secret dans un log applicatif. Le message indique
toujours la commande de génération d'une clé valide.

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

Les tables MFA (`auth_mfa_factors`, `auth_mfa_recovery_codes`) sont générées
dans votre projet par la commande du core `forge auth:init`, puis appliquées
avec `forge db:apply`. Les fichiers `sql/` du dépôt source en sont la référence
(ils ne sont pas livrés dans le wheel : la DDL est embarquée par `auth:init`).

## Compatibilité

Disponible comme paquet séparé (ADR-004, MFA-EXTRACT-001). Les anciens chemins
`core.auth.mfa`, `core.auth.recovery` et `core.auth.totp_replay` ont été retirés
du core lors de l'extraction.

## Limites connues

- Le store anti-replay et le rate-limit sont in-memory process-local.
  En multi-worker, utiliser des sticky sessions.
- La politique de rotation et la procédure de sauvegarde/restauration de la
  clé Fernet ne sont pas encore formalisées (exigences Beta restantes).
