# Auth — Challenge MFA à la connexion

!!! info "Module en Alpha — non publié sur PyPI en {{forge_version}}"
    `forge-mvc-mfa` est marqué `Development Status :: 3 - Alpha` depuis `MFA-PYPI-READY-001`.

    Le secret TOTP est **chiffré au repos** via Fernet (`cryptography`) avec la clé
    `FORGE_MFA_SECRET_KEY`. Le chiffrement est obligatoire — démarrer sans cette
    variable d'environnement lève `MfaSecretKeyMissing`.

    **Non publié sur PyPI dans la vague `{{forge_version}}`.** Non inclus dans `forge-mvc[all]`.
    Installation depuis GitHub : voir [installation-github.md](../installation-github.md).

    Publication PyPI prévue lors d'une release dédiée.

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

---

## Politique de stockage des secrets MFA

### Statut actuel

`forge-mvc-mfa` est Alpha depuis `MFA-PYPI-READY-001`. Le secret TOTP est
**chiffré au repos** via Fernet (bibliothèque `cryptography`).

Le module est opt-in, non inclus dans `forge-mvc[all]`, et doit être configuré avec
`FORGE_MFA_SECRET_KEY` avant tout déploiement.

### Développement et tests

En développement et en environnement de test isolé :

- le secret TOTP est chiffré dans `auth_mfa_factors.totp_secret` (Fernet, préfixe `enc:`) ;
- la clé de chiffrement est lue depuis `FORGE_MFA_SECRET_KEY` — requis même en dev ;
- les codes de récupération sont stockés sous forme hashée (`hash_recovery_code()` — SHA-256 + `secrets.compare_digest`).

**Conditions requises même en développement :**

- `FORGE_MFA_SECRET_KEY` positionné dans l'environnement ;
- accès à la table `auth_mfa_factors` limité à l'utilisateur applicatif ;
- secrets jamais loggés (`totp_secret` et `recovery_code` sont dans les champs redactés de `sanitize_auth_audit_metadata()`) ;
- base de données non exposée publiquement.

### Production

Le module est Alpha. Le chiffrement Fernet est en place (depuis `SEC-MFA-SECRET-ENCRYPTION-001`).
Les exigences de production-ready complètes (rotation, sauvegarde/restauration,
revue sécurité) ne sont pas encore satisfaites.

**Protection additionnelle recommandée en production :**

- restreindre les droits d'accès à la table `auth_mfa_factors` au strict minimum applicatif ;
- stocker `FORGE_MFA_SECRET_KEY` dans un gestionnaire de secrets (Vault, AWS Secrets Manager…) ;
- chiffrement du disque de la base de données ;
- ne pas exporter `auth_mfa_factors` dans des dumps non chiffrés ;
- documenter la procédure de rotation et de sauvegarde/restauration de la clé.

### Secrets TOTP

Le secret TOTP est une clé partagée utilisée pour calculer les codes TOTP (RFC 6238).

**Pourquoi on ne peut pas simplement hasher le secret TOTP :**

Un hash est à sens unique. Pour vérifier un code TOTP, le serveur doit pouvoir recalculer `TOTP(secret, timestamp)`. Si le secret est hashé, cette opération est impossible.

Le stockage production-ready d'un secret TOTP nécessite :

- un **chiffrement applicatif réversible** (AES-256-GCM ou équivalent avec clé de chiffrement séparée), **ou**
- un **HSM** (*Hardware Security Module*), **ou**
- un **gestionnaire de secrets** (Vault, AWS Secrets Manager, ou équivalent).

Depuis `SEC-MFA-SECRET-ENCRYPTION-001`, `forge-mvc-mfa` implémente le chiffrement Fernet
(`cryptography.fernet.Fernet`, AES-128-CBC + HMAC-SHA256) via la clé `FORGE_MFA_SECRET_KEY`.
Les valeurs stockées en base sont préfixées `enc:` pour distinguer les secrets chiffrés
d'éventuelles valeurs legacy.

Pour renforcer davantage, coupler `FORGE_MFA_SECRET_KEY` à un gestionnaire de secrets externe.

### Codes de récupération

Les codes de récupération sont correctement protégés dans `forge-mvc-mfa` 3.0.x :

- générés via `secrets.choice()` sur un alphabet sans ambiguïté ;
- hashés avant stockage via `hash_recovery_code()` (SHA-256) ;
- vérifiés via `secrets.compare_digest()` (résistant aux timing attacks) ;
- stockés en base uniquement sous forme de hash — le code brut n'est jamais persisté.

**Cette conception est conforme pour la production**, à condition que la base elle-même soit protégée. Un hash de code de récupération exposé ne permet pas de retrouver le code brut.

### Exigences avant production-ready

`forge-mvc-mfa` ne sera pas déclaré Beta et publié sur PyPI tant que les exigences suivantes ne sont pas satisfaites :

1. ~~**Chiffrement applicatif des secrets TOTP**~~ ✓ livré (`SEC-MFA-SECRET-ENCRYPTION-001`) — Fernet + `FORGE_MFA_SECRET_KEY`.
2. **Politique de rotation documentée** — rotation ou invalidation maîtrisée des secrets compromis.
3. **Documentation de sauvegarde/restauration** — procédure en cas de perte de la clé de chiffrement.
4. ~~**Tests dédiés au stockage chiffré**~~ ✓ livré (`SEC-MFA-SECRET-ENCRYPTION-001`) — `tests/test_mfa_secret_crypto.py`.
5. **Revue sécurité explicite** — validation que le stockage chiffré est correct.
6. ~~**Décision explicite de changement de statut Pre-Alpha → Alpha**~~ ✓ livré (`MFA-PYPI-READY-001`).
7. **Décision de passage Alpha → Beta** et publication PyPI — ticket futur post-b7.

### Tickets liés

| Ticket | Description | État |
|---|---|---|
| `MFA-SECRET-STORAGE-POLICY-001` | Documenter la politique de stockage | livré |
| `SEC-MFA-SECRET-ENCRYPTION-001` | Chiffrement applicatif du secret TOTP (Fernet) | livré |
| `MFA-PYPI-READY-001` | Requalification Alpha (Pre-Alpha → Alpha) | livré |

