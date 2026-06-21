# Le cœur MFA dans Forge

Ce document décrit l'API centrale de `forge_mvc_mfa` : facteurs, configuration TOTP, challenge à la connexion et revalidation des actions sensibles.

Le fichier de code correspondant est `forge_mvc_mfa/mfa.py`.

## 1. À quoi sert ce module ?

C'est le cœur du MFA : il modélise un **facteur** d'authentification, sait créer et vérifier un facteur **TOTP**, intercale un **challenge** entre le mot de passe et la session, et permet de **revalider** une action sensible.

Le module est sans écriture en base : il calcule et valide, c'est l'application qui persiste.

## 2. Les facteurs

`AuthMfaFactor` est la représentation Python d'un facteur stockable.

| Fonction | Comportement |
|---|---|
| `validate_mfa_factor_contract(data)` | valide le contrat minimal d'un facteur ; lève sinon |
| `normalize_mfa_factor(data)` | valide et normalise un dict brut en `AuthMfaFactor` |
| `is_valid_mfa_factor(factor)` | `True` si le facteur est structurellement valide |
| `is_mfa_factor_active(factor)` | `True` si le facteur a le statut `active` |
| `is_mfa_enabled(factors)` | `True` si au moins un facteur de la liste est actif |

## 3. La configuration TOTP

```python
from forge_mvc_mfa import create_totp_factor, confirm_totp_factor, verify_totp_code

setup = create_totp_factor(user_id=42, label="Mon téléphone")
# setup.secret, setup.factor, setup.provisioning_uri (QR code)

confirmed = confirm_totp_factor(setup.factor, code="123456")   # AuthMfaFactor ou None
```

| Fonction | Comportement |
|---|---|
| `create_totp_factor(user_id, label=None, issuer_name="Forge", ...)` | crée un facteur TOTP `pending` (un `TotpSetup`), sans écrire en base |
| `confirm_totp_factor(factor, code, now=None)` | confirme un facteur `pending` après vérification du code |
| `verify_totp_code(secret, code, valid_window=1, now=None)` | vérifie un code TOTP |
| `totp_provisioning_uri(secret, account_name, issuer_name="Forge")` | construit l'URI `otpauth://totp/` (QR code) |
| `generate_totp_secret()` | génère un secret TOTP base32 cryptographiquement sûr |

Le secret produit doit être **chiffré au repos** avant stockage : voir [le chiffrement des secrets](secret_crypto.md).

## 4. Le challenge à la connexion

Le challenge s'intercale entre la validation du mot de passe et l'ouverture de la session.

```python
from forge_mvc_mfa import is_mfa_enabled, start_mfa_challenge, verify_mfa_challenge

if is_mfa_enabled(factors):
    start_mfa_challenge(request, auth_user)   # ne connecte pas
    return redirect("/login/mfa")
```

| Fonction | Comportement |
|---|---|
| `start_mfa_challenge(request, user, now=None)` | démarre un challenge temporaire en session après l'auth primaire |
| `has_pending_mfa_challenge(request, max_age_minutes=10, now=None)` | `True` si un challenge est en attente et non expiré |
| `get_mfa_challenge_user_id(request)` | l'id en attente, ou `None` |
| `verify_mfa_challenge(request, code, factors, recovery_codes=None, ...)` | vérifie un code TOTP ou de récupération ; retourne `MfaChallengeResult` ou `None` ; supprime le challenge en cas de succès |
| `clear_mfa_challenge(request)` | supprime les clés de challenge (idempotent) |

L'état temporaire n'est **pas** une session authentifiée : aucun accès aux routes protégées tant que le code n'est pas validé.

## 5. La revalidation d'action sensible

Pour réexiger un code MFA avant une action critique, même session déjà ouverte :

| Fonction | Comportement |
|---|---|
| `verify_mfa_revalidation(request, user_id, code, factors, ...)` | vérifie un code et marque la revalidation ; retourne `MfaRevalidationResult` ou `None` |
| `mark_mfa_revalidated(request, user_id, now=None)` | stocke en session une preuve de revalidation récente |
| `has_recent_mfa_revalidation(request, user_id, max_age_minutes=10, now=None)` | `True` si une revalidation récente et valide existe |
| `get_mfa_revalidated_user_id(request)` | l'id revalidé en session, ou `None` |
| `clear_mfa_revalidation(request)` | supprime les clés de revalidation (idempotent) |
| `require_recent_mfa(func=None, *, max_age_minutes=10)` | décorateur protégeant une action sensible |

## 6. Les constantes

Types de facteur (`MFA_FACTOR_TOTP`, `MFA_FACTOR_RECOVERY`), statuts (`MFA_STATUS_PENDING`, `MFA_STATUS_ACTIVE`, `MFA_STATUS_DISABLED`), et clés/bornes de session pour le challenge et la revalidation (`MFA_CHALLENGE_*`, `MFA_REVALIDATION_*`).

## 7. Contextes d'utilisation

- **Enrôlement** : `create_totp_factor` puis `confirm_totp_factor`.
- **Connexion** : `start_mfa_challenge` puis `verify_mfa_challenge`.
- **Action sensible** : `@require_recent_mfa` ou `verify_mfa_revalidation`.

## 8. Voir aussi

- [Le chiffrement des secrets](secret_crypto.md) : protéger le secret TOTP au repos.
- [Les codes de récupération](recovery.md) : le second facteur de secours.
- [La protection anti-rejeu](totp_replay.md) : empêcher la réutilisation d'un code.
- [Vue d'ensemble et politique de sécurité](../reference.md).
