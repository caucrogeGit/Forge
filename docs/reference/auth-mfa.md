# Auth — Challenge MFA à la connexion

!!! warning "Module en Pre-Alpha"
    `forge-mvc-mfa` est marqué `Development Status :: 2 - Pre-Alpha`.

    Le secret TOTP est actuellement **stocké en clair** dans la colonne
    `TotpSecret` de la table `auth_mfa_factors`. **Non recommandé en
    production sensible** sans protection additionnelle (restriction
    d'accès à la table au minimum).

    Le module **n'est pas inclus** dans `forge-mvc[all]` (cf. T3).
    Installation depuis GitHub : voir [installation-github.md](../installation-github.md).

    Le chiffrement applicatif est planifié dans
    `SEC-MFA-SECRET-ENCRYPTION-001` — ticket post-1.0, tant que MFA reste Pre-Alpha.
    À cette livraison, le module passera en Beta.

> **Module extrait** : depuis Forge 2.5.0, le code MFA vit dans
> `forge-mvc-mfa`. Voir `packages/forge-mvc-mfa/README.md` pour
> l'installation et l'API utilisateur. Cette page documente le flux
> de challenge MFA pour mémoire et référence rapide.


Le challenge MFA s'intercale entre la validation du mot de passe et l'ouverture de la session.

Flux général :

```
mot de passe correct + MFA désactivé  → session ouverte (comportement inchangé)
mot de passe correct + MFA activé     → état temporaire créé → /login/mfa
code MFA valide                        → état temporaire supprimé → session ouverte
code MFA invalide                      → état temporaire conservé → retour formulaire
```

### État temporaire de challenge

| Clé de session | Rôle |
|---|---|
| `_auth_mfa_user_id` | Identifiant de l'utilisateur en attente de MFA |
| `_auth_mfa_started_at` | Timestamp ISO de début (expiration 10 min par défaut) |

L'état temporaire n'est **pas** une session authentifiée. L'utilisateur n'a aucun accès aux routes protégées tant que le code MFA n'est pas validé.

### API `forge_mvc_mfa`

| Fonction | Comportement |
|---|---|
| `start_mfa_challenge(request, user)` | Stocke `user.id` et timestamp en session. Ne connecte pas l'utilisateur. Lève `InvalidAuthUserError` si utilisateur inactif. |
| `has_pending_mfa_challenge(request, max_age_minutes=10)` | Retourne `True` si challenge en cours et non expiré. |
| `get_mfa_challenge_user_id(request)` | Retourne l'identifiant en attente ou `None`. |
| `verify_mfa_challenge(request, code, factors, recovery_codes=None)` | Vérifie code TOTP ou de récupération. Retourne `MfaChallengeResult` ou `None`. Supprime le challenge en cas de succès. |
| `clear_mfa_challenge(request)` | Supprime les clés de challenge. Idempotent. |

### Exemple d'intégration MVC

```python
# Dans le contrôleur de login, après vérification du mot de passe :
from forge_mvc_mfa import is_mfa_enabled, start_mfa_challenge
from core.auth.user import AuthUser

mfa_factors = get_active_mfa_factors(user_id)
if is_mfa_enabled(mfa_factors):
    auth_user = AuthUser(id=user_id, email=email, password_hash=hash, is_active=True)
    start_mfa_challenge(request, auth_user)
    return redirect("/login/mfa")

# Sinon : ouvrir la session directement
```

### Limites actuelles (AUTH-MFA-004)

Forge ne fournit pas encore dans ce flux : *remember device*, WebAuthn, SMS, email MFA, gestion des codes de récupération dans le formulaire de connexion.

