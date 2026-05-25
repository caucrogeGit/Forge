# Authentification Forge

Auth/User est la brique optionnelle de Forge pour representer une identite
utilisateur moderne sans transformer le framework en application metier. Elle
fournit des contrats Python, des helpers explicites et des SQL visibles que les
projets peuvent adopter progressivement.

Voir aussi : [ADR-001 — Stratégie d'authentification Forge 2.x](adr/001-auth-strategy.md) · [ADR-002 — Stratégie de session Forge 2.x](adr/002-session-strategy.md) · [RBAC — Contrôle d'accès](rbac.md) · [Sécurité en production](production-security.md) · [Référence CLI](reference.md)

Le contrôleur d'authentification par défaut (`mvc/controllers/auth_controller.py`) s'appuie sur `core.auth.password.verify_password` (Argon2id) pour la vérification des mots de passe. `core.security.hashing` reste disponible en repli pour les hashes PBKDF2 existants (voir ADR-001). Les nouveaux hashes PBKDF2 legacy utilisent désormais 600 000 itérations (format versionné `pbkdf2_sha256$…`) ; les anciens hashes restent vérifiables. Lorsqu'un utilisateur legacy PBKDF2 se connecte avec succès, Forge migre automatiquement son hash vers Argon2id (`auth_model.update_password_hash`). Cette migration est transparente et ne force pas de réinitialisation du mot de passe.

---

## API officielle et compatibilité legacy

Depuis Forge 2.x, et toujours dans les versions actuelles de Forge, l'API officielle pour les nouveaux projets est `core.auth`.

| Domaine | API officielle — `core.auth` | Compatibilité / transversal — `core.security` |
|---|---|---|
| Hash mot de passe | `core.auth.password` — Argon2id | `core.security.hashing` — PBKDF2 **legacy** |
| Session Auth | `core.auth.session` (`login_user`, `login_required`…) | `core.security.session` — moteur HTTP (officiel) |
| Décorateur login | `core.auth.session.login_required` | `core.security.decorators.require_auth` — **legacy** |
| RBAC | `forge_mvc_rbac` (`pip install --pre forge-mvc-rbac` — publié sur PyPI) | — |
| CSRF | — | `core.security.middleware.CsrfMiddleware` + `require_csrf` — officiels |
| Middleware | — | `core.security.middleware` — officiel |
| MFA | `forge_mvc_mfa` (`pip install --pre forge-mvc-mfa` — publié sur PyPI depuis `1.0.0-beta.9`) — **Alpha**, secret TOTP chiffré au repos (voir [auth-mfa](reference/auth-mfa.md)) | — |
| Tokens à usage limité | `core.auth.tokens` | — |
| OIDC / SSO | ❌ non fourni nativement — voir [section OIDC](#oidc) | — |
| Contrat utilisateur | `core.auth.user` | — |
| Audit / rate limit | `core.auth.audit`, `core.auth.rate_limit` | — |

### Modules `core.security` encore officiels

Tous les modules `core.security` ne sont pas legacy. Les briques transversales suivantes restent officielles dans Forge actuel :

- `core.security.session` — moteur de session mémoire, utilisé en interne par `core.auth.session` ;
- `core.security.middleware.CsrfMiddleware` — protection CSRF active ;
- `core.security.middleware.AuthMiddleware` — middleware de redirection vers `/login`.

### Modules `core.security` dépréciés

Les éléments suivants sont dépréciés en faveur de `core.auth` et seront supprimés dans la trajectoire 1.x stable :

- `core.security.hashing` — PBKDF2 legacy. Reste utilisable pour vérifier d'anciens hashes et effectuer la migration transparente vers Argon2id. Les nouveaux projets doivent utiliser `core.auth.password` (Argon2id) ;
- `core.security.decorators.require_auth` — remplacé par `core.auth.session.login_required` ;
- `core.security.decorators.require_role` — remplacé par `forge_mvc_rbac.require_user_permission`.

Voir [ADR-001 — Stratégie d'authentification Forge 2.x](adr/001-auth-strategy.md) pour la décision d'architecture.

---

## Vue d'ensemble

Auth/User repond a la question : **qui est l'utilisateur ?** RBAC repond a la
question : **qu'a-t-il le droit de faire ?** Les deux briques peuvent etre
reliees par `user_roles`, mais restent separees.

Principes :

- pas d'ORM impose ;
- pas de modele utilisateur metier riche impose ;
- SQL optionnels visibles dans `mvc/models/sql/` ;
- aucune route login/reset/MFA/OIDC generee automatiquement ;
- aucune ecriture en base cachee dans les helpers de contrat ;
- aucune permission stockee dans `users` ;
- logique applicative et politique de securite finale cote projet.

Les modules Auth/User disponibles couvrent aujourd'hui :

- utilisateur local ;
- mot de passe Argon2id ;
- session utilisateur ;
- tokens a usage limite ;
- verification email ;
- reset password ;
- MFA TOTP, recovery codes, challenge et revalidation ;
- pont Auth/User vers RBAC ;
- administration CLI utilisateurs ;
- audit Auth ;
- rate limit Auth.

## Contrat utilisateur

`AuthUser` est le contrat minimal d'un utilisateur authentifiable.

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class AuthUser:
    id: int
    email: str
    password_hash: str
    is_active: bool = True
    created_at: Any | None = None
    updated_at: Any | None = None
```

API :

- `normalize_auth_user(data) -> AuthUser`
- `validate_auth_user_contract(data)`
- `is_valid_auth_user(user) -> bool`
- `InvalidAuthUserError`

`id` doit etre strictement positif, `email` non vide, `password_hash` non vide
et `is_active` booleen. Forge ne demande pas de nom, avatar, telephone, adresse,
profil proprietaire ou statut metier.

### `users.sql`

`forge auth:init` cree ou preserve :

```sql
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified_at DATETIME NULL,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

`email_verified_at` et `last_login_at` sont des colonnes utiles aux flux
applicatifs. Forge ne les met pas a jour automatiquement.

## Mot de passe

Forge fournit le hachage et la verification de mot de passe avec Argon2id. Le hachage repose sur la dépendance Python `argon2-cffi`.

```python
from core.auth import hash_password, verify_password, password_needs_rehash

password_hash = hash_password("mot-de-passe")
ok = verify_password("mot-de-passe", password_hash)
needs = password_needs_rehash(password_hash)
```

API :

- `hash_password(password)`
- `verify_password(password, password_hash) -> bool`
- `password_needs_rehash(password_hash) -> bool`
- `validate_new_password(password)`
- `InvalidNewPasswordError`

Le mot de passe clair n'est jamais stocke. Le reset password valide seulement
une regle minimale de nouveau mot de passe : chaine non vide et longueur
minimale. Les politiques plus complexes appartiennent aux applications.

## Session utilisateur

La session Auth/User stocke uniquement l'identifiant utilisateur local sous une
cle de session interne. Elle ne stocke ni `email`, ni `password_hash`, ni objet
`AuthUser` complet.

**Limite importante** : le backend de session par défaut (`MemorySessionStore`) est en mémoire processus — les sessions sont perdues au redémarrage. `FileSessionStore` offre une persistance locale ; `MariaDbSessionStore` offre un stockage partagé entre processus. Les deux sont disponibles dans `core.sessions` et doivent être configurés explicitement. Voir [ADR-002 — Stratégie de session](adr/002-session-strategy.md).

```python
from core.auth import authenticate_user, login_user, logout_user

user = authenticate_user(email, password, load_user_by_email)

if user is not None:
    login_user(request, user)

logout_user(request)
```

API :

- `authenticate_user(email, password, user_loader) -> AuthUser | None`
- `login_user(request, user) -> None`
- `logout_user(request) -> None`
- `get_authenticated_user_id(request) -> int | None`
- `current_user(request, user_loader) -> AuthUser | None`
- `is_authenticated(request) -> bool`
- `login_required`

`authenticate_user` appelle un loader fourni par l'application. Il refuse les
utilisateurs inactifs et retourne `None` pour les echecs normaux. Il ne fait pas
de requete SQL lui-meme.

`current_user` recharge l'utilisateur via un loader applicatif. Si la session
est absente, invalide, si le loader retourne `None`, ou si l'utilisateur est
inactif, le resultat est `None`.

`@login_required` protege une fonction controleur. Il retourne `401` par defaut
ou peut rediriger si `redirect_to` est fourni.

## Cookies de session

### Attributs de sécurité

Tous les cookies de session émis par Forge utilisent le préfixe `__Host-` et
portent les attributs suivants :

```
__Host-session_id=<token>; Path=/; HttpOnly; SameSite=Strict; Secure
```

| Attribut | Valeur | Rôle |
|---|---|---|
| `HttpOnly` | présent | Le cookie n'est pas accessible depuis JavaScript |
| `SameSite=Strict` | présent | Le cookie n'est pas envoyé sur requêtes cross-site |
| `Secure` | présent | Le cookie n'est envoyé que sur HTTPS |
| `Path=/` | présent | Le cookie s'applique à toutes les routes |

### Comportement dev / prod

Le flag `Secure` est **toujours activé**, quel que soit `app_env`. Forge suppose
que toute configuration de déploiement — y compris le développement local — passe
par HTTPS ou un reverse-proxy TLS. Il n'existe pas de mode "dev sans Secure".

Ce choix est cohérent avec le header `Strict-Transport-Security` qui est lui aussi
émis sur toutes les réponses, y compris en dev (voir docs/reference.md — section
"Headers HTTP de sécurité").

Si votre environnement local ne supporte pas HTTPS, configurez un proxy TLS local
(mkcert, Caddy, ngrok) ou utilisez les tests unitaires qui contournent HTTP.

### Contenu du cookie

Le cookie ne contient que l'identifiant de session : un token hexadécimal aléatoire
de 64 caractères généré par `secrets.token_hex(32)`. Aucune donnée utilisateur,
aucun token d'accès, aucune permission, aucun email ne transitent dans la valeur
du cookie.

Les données de session sont stockées côté serveur. Après authentification, la session
contient : `id`, `login`, `prenom`, `nom`, `email`, `roles`, `csrf_token`,
`expire_a`, `authentifie`. Elle ne contient jamais `password`, `password_hash`,
`token`, `secret` ni aucun code MFA.

### Suppression au logout

Le logout émet un cookie expiré avec `Max-Age=0` et les mêmes attributs de sécurité :

```
__Host-session_id=; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=0
```

La session est également supprimée côté serveur par `supprimer_session()` avant
que la réponse soit envoyée.

### Durée de session

Les sessions expirent après **3600 secondes** (1 heure) d'inactivité. Le délai
est repoussé à chaque requête authentifiée valide (`est_authentifie()`).

### Validation du format de l'identifiant de session

`get_session_id()` valide le format du cookie avant toute consultation du store.
Seul un identifiant composé de **64 caractères hexadécimaux minuscules** est accepté
(expression régulière `^[0-9a-f]{64}$`). Toute valeur trop courte, trop longue,
contenant des caractères non hexadécimaux ou une tentative d'injection (guillemets,
espaces, séparateurs) est rejetée — `get_session_id()` retourne `None` sans
consulter le store.

### Protection contre la fixation de session

Au login, `authentifier_session()` génère un nouvel identifiant de session et
supprime l'ancien. L'identifiant de session pré-authentification ne peut pas être
réutilisé après connexion.

### Cache-Control sur les pages auth

Les routes d'authentification (`/login`, `/login/mfa`, `/logout`) reçoivent
automatiquement le header :

```
Cache-Control: no-store
```

Ce header interdit au navigateur et aux caches intermédiaires de stocker la
réponse. Il est ajouté centralement dans `app.py` (`_send_response()`) pour
toutes les méthodes HTTP (GET et POST) sur ces chemins. Les fichiers statiques
ne sont pas affectés — ils conservent leur propre `Cache-Control: max-age=…`.

### Cookie CSRF

Forge n'émet pas de cookie CSRF séparé. Le token CSRF est stocké côté serveur
dans la session et transmis via un champ de formulaire ou l'en-tête
`X-CSRF-Token`. Aucune donnée CSRF ne transite dans un cookie.

### Préfixe `__Host-` et contraintes associées

Le préfixe `__Host-` impose les contraintes suivantes côté navigateur :

- `Secure` obligatoire (HTTPS imposé) ;
- `Path=/` obligatoire (portée globale) ;
- attribut `Domain` interdit (le cookie ne peut pas être partagé entre sous-domaines).

Forge respecte ces contraintes : `Secure`, `Path=/` et absence de `Domain` sont
garantis sur tous les cookies de session. La constante `SESSION_COOKIE_NAME` dans
`core/security/session.py` centralise le nom du cookie — toute modification doit
passer par cette constante.

### Limites restantes

- Un seul cookie de session est géré. Les applications multi-domaines ou multi-sous-domaines
  doivent gérer leur propre stratégie de cookie.
- Le flag `SameSite=Strict` peut empêcher le cookie d'être envoyé lors d'un accès
  direct depuis un lien externe (ex. lien dans un email). Adaptez à `SameSite=Lax`
  si nécessaire dans votre application.

## Tokens Auth

`AuthToken` represente un jeton securise a usage limite. Le token brut est donne
une seule fois a l'application ; seul son hash est stockable.

```python
from core.auth import generate_auth_token, hash_auth_token, verify_auth_token

raw_token = generate_auth_token()
token_hash = hash_auth_token(raw_token)
ok = verify_auth_token(raw_token, token_hash)
```

Structure :

```python
@dataclass(frozen=True)
class AuthToken:
    user_id: int
    purpose: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime | None = None
```

API :

- `generate_auth_token(nbytes=32)`
- `hash_auth_token(token)`
- `verify_auth_token(token, token_hash)`
- `token_expires_at(minutes=60, now=None)`
- `is_token_expired(expires_at, now=None)`
- `is_token_usable(token_record, purpose=None, now=None)`
- `normalize_auth_token(data)`
- `validate_auth_token_contract(data)`
- `is_valid_auth_token(token_record)`

### `auth_tokens.sql`

```sql
CREATE TABLE IF NOT EXISTS auth_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    purpose VARCHAR(80) NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auth_tokens_user_purpose (user_id, purpose),
    INDEX idx_auth_tokens_expires_at (expires_at),
    CONSTRAINT fk_auth_tokens_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

`used_at` permet a l'application de marquer un token comme consomme. Forge ne
met pas cette colonne a jour automatiquement.

## Verification email

La verification email s'appuie sur les tokens generiques.

```python
from core.auth import (
    EMAIL_VERIFICATION_PURPOSE,
    create_email_verification_token,
    verify_email_verification_token,
    email_verification_timestamp,
    is_email_verified,
)

raw_token, token_record = create_email_verification_token(user_id=1)
ok = verify_email_verification_token(raw_token, token_record)
```

Responsabilites de l'application :

- stocker `token_record.token_hash` dans `auth_tokens` ;
- envoyer le token brut dans un lien ;
- appeler `verify_email_verification_token` au retour ;
- renseigner `users.email_verified_at` ;
- renseigner `auth_tokens.used_at`.

Forge ne fournit pas d'envoi automatique d'email, route de confirmation,
controleur ou template.

## Mot de passe oublie

Le reset password se fait en deux etapes : creation/verifications du token, puis
production d'un nouveau hash.

```python
from core.auth import create_password_reset_token, reset_password_with_token

raw_token, token_record = create_password_reset_token(user_id=1)
result = reset_password_with_token(raw_token, token_record, "nouveau-mot-de-passe")

if result is not None:
    # users.password_hash = result.password_hash
    # auth_tokens.used_at = result.used_at
    pass
```

API :

- `PASSWORD_RESET_PURPOSE`
- `create_password_reset_token(user_id, minutes=30, now=None)`
- `verify_password_reset_token(token, token_record, now=None)`
- `password_reset_timestamp(now=None)`
- `create_password_reset_request(user, minutes=30, now=None)`
- `reset_password_with_token(token, token_record, new_password, now=None)`
- `PasswordResetRequest`
- `PasswordResetResult`

`PasswordResetResult` contient `user_id`, `password_hash` et `used_at`. Il ne
contient jamais le mot de passe clair ni le token brut. Forge ne fait aucune
ecriture DB automatique.

## MFA

!!! info "forge-mvc-mfa — opt-in officiel Alpha publié sur PyPI depuis 1.0.0-beta.9"
    Le module MFA est marqué `Development Status :: 3 - Alpha` depuis `MFA-PYPI-READY-001`.
    Le secret TOTP est **chiffré au repos** via Fernet (`FORGE_MFA_SECRET_KEY`).

    Installation :

    ```bash
    pip install --pre forge-mvc-mfa
    ```

    MFA est disponible comme module opt-in officiel `forge-mvc-mfa`, publié
    sur PyPI depuis `1.0.0-beta.9`. Il **n'est pas intégré au core** Forge
    — le core ne dépend pas de `forge-mvc-mfa`. Voir le
    [contrat d'installation](installation.md#contrat-dinstallation-des-opt-ins).

> **Depuis Forge 2.4.0**, le code MFA est extrait dans le module `forge-mvc-mfa` (ADR-004, MFA-EXTRACT-001).
> L'ancien chemin `core.auth.mfa` émettait un `DeprecationWarning` et a été retiré en Forge 3.0.

Forge fournit le socle MFA par briques :

- contrat et table des facteurs ;
- TOTP ;
- codes de recuperation ;
- challenge MFA a la connexion ;
- revalidation MFA pour actions sensibles.

### Facteurs MFA

```python
from forge_mvc_mfa import AuthMfaFactor, normalize_mfa_factor, is_mfa_enabled
```

`AuthMfaFactor` decrit `user_id`, `factor_type`, `totp_secret`, `status`,
`label`, `confirmed_at`, `last_used_at`, `created_at` et `updated_at`.

Statuts :

- `pending`
- `active`
- `disabled`

Types :

- `totp`
- `recovery`

### `auth_mfa_factors.sql`

```sql
CREATE TABLE IF NOT EXISTS auth_mfa_factors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    factor_type VARCHAR(40) NOT NULL,
    totp_secret VARCHAR(255) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    label VARCHAR(120) NULL,
    confirmed_at DATETIME NULL,
    last_used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_auth_mfa_factors_user_id (user_id),
    INDEX idx_auth_mfa_factors_user_status (user_id, status),
    CONSTRAINT fk_auth_mfa_factors_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Le champ `totp_secret` contient le secret TOTP **chiffré** dans la base
(Fernet, clé `FORGE_MFA_SECRET_KEY`). Forge ne l'affiche jamais ni ne l'inclut
dans un audit ou une tentative rate limit.

**Exigence :** `FORGE_MFA_SECRET_KEY` doit être positionné dans l'environnement.
Voir `SEC-MFA-SECRET-ENCRYPTION-001` pour les détails du chiffrement.

### TOTP

La prise en charge TOTP repose sur la dépendance Python `pyotp`.

API principale :

- `generate_totp_secret()`
- `totp_provisioning_uri(secret, account_name, issuer="Forge")`
- `create_totp_factor(user_id, secret, label=None)`
- `confirm_totp_factor(factor, code, secret, now=None)`
- `verify_totp_code(secret, code, now=None)`

Le secret brut est necessaire pour verifier les codes. Sa persistance securisee
reste une responsabilite applicative.

### Codes de recuperation

API :

- `create_recovery_codes(user_id, count=10)`
- `generate_recovery_code()`
- `hash_recovery_code(code)`
- `verify_recovery_code(code, code_hash)`
- `consume_recovery_code(code, code_record, now=None)`

`create_recovery_codes` retourne des codes bruts a afficher une seule fois et
des records hashables. Les codes bruts ne doivent jamais etre stockes.

### `auth_mfa_recovery_codes.sql`

```sql
CREATE TABLE IF NOT EXISTS auth_mfa_recovery_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    code_hash CHAR(64) NOT NULL UNIQUE,
    used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_auth_mfa_recovery_codes_user_id (user_id),
    INDEX idx_auth_mfa_recovery_codes_used_at (used_at),
    CONSTRAINT fk_auth_mfa_recovery_codes_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Challenge MFA

API :

- `start_mfa_challenge(request, user, now=None)`
- `has_pending_mfa_challenge(request, max_age_minutes=10, now=None)`
- `get_mfa_challenge_user_id(request)`
- `verify_mfa_challenge(request, code, factors, recovery_codes=(), now=None)`
- `clear_mfa_challenge(request)`
- `MfaChallengeResult`

Le challenge stocke seulement `user_id` et un timestamp en session. Il ne
connecte pas l'utilisateur automatiquement.

### Lockout MFA

Forge applique un rate-limit sur les verifications MFA pour prevenir le brute-force
sur les codes TOTP a 6 chiffres.

| Endpoint | Limite | Fenetre |
|---|---|---|
| Challenge MFA (login) | 5 tentatives | 5 minutes |
| Revalidation MFA (action sensible) | 3 tentatives | 5 minutes |

Le lockout est par utilisateur (`mfa_challenge:user:<id>` ou
`mfa_revalidation:user:<id>`). Un succes remet le compteur a zero.

En cas de lockout, la reponse renvoyee est identique a un echec de code :
le client n'apprend pas qu'il est bloque. L'evenement
`AUTH_EVENT_MFA_RATE_LIMITED` est journalise pour permettre a l'operateur
de detecter l'attaque.

Les parametres sont configurables via les constantes dans `forge_mvc_mfa.mfa` :

- `MFA_CHALLENGE_MAX_ATTEMPTS` (defaut : 5)
- `MFA_CHALLENGE_WINDOW_SECONDS` (defaut : 300)
- `MFA_REVALIDATION_MAX_ATTEMPTS` (defaut : 3)
- `MFA_REVALIDATION_WINDOW_SECONDS` (defaut : 300)

**Limite connue :** le store est in-memory process-local. En multi-worker
(gunicorn, uWSGI), chaque processus a son propre compteur — un attaquant
peut faire N_max x N_workers tentatives. Comportement identique au rate-limit
de login (`core.security.hashing`).

### Anti-replay TOTP

Forge applique RFC 6238 §5.2 : un code TOTP accepte ne peut pas etre rejoue
dans sa fenetre de validite (30 secondes).

Mecanisme : pour chaque facteur TOTP, Forge memorise la derniere step TOTP
acceptee (entier = timestamp_unix // 30). Tout code dont la step est inferieure
ou egale a la derniere step utilisee est refuse, meme si le code est
cryptographiquement valide.

Le check et l'enregistrement se font dans `verify_mfa_challenge` et
`verify_mfa_revalidation`. Un facteur `id=None` (non encore persiste) est
exempt du check anti-replay.

**Limites :**

- **Store in-memory process-local.** En multi-worker, chaque processus a son
  propre dict — replay theoriquement possible sur un autre worker dans la
  fenetre de 30 s. Mitigation : `SameSite=Strict` + sticky sessions.
- **Pas de persistance entre redemarrages.** Au redemarrage, le dict est vide.
  Fenetre de risque < 30 s.
- **Purge opportuniste.** Les entrees expirees (>24h) sont purgees toutes
  les 100 enregistrements. Aucun scheduler dedie.

## Challenge MFA à la connexion

Le challenge MFA s'intercale entre la validation du mot de passe et l'ouverture
de la session utilisateur complete.

Comportement :

- **MFA desactive** : le mot de passe correct ouvre immediatement la session.
- **MFA active** : le mot de passe correct ne suffit pas. Forge stocke un etat
  temporaire de challenge (`_auth_mfa_user_id`, `_auth_mfa_started_at`) et attend
  la validation du code MFA avant d'ouvrir la session.
- **Code invalide** : l'etat temporaire est conserve (non expire) ; aucune session
  n'est ouverte.
- **Challenge expire** (defaut 10 min) : l'etat est efface ; l'utilisateur doit
  se reconnecter.
- **Logout** : la suppression de session efface automatiquement l'etat temporaire.

Forge ne fournit pas encore : *remember device*, codes de recuperation dans le
flux de connexion principal, WebAuthn, SMS, email MFA.

### Integration dans le flux MVC

L'application MVC inclut un exemple complet :

- `mvc/controllers/auth_controller.py` — detecte `is_mfa_enabled` apres
  `verifier_mot_de_passe`, appelle `start_mfa_challenge` et redirige vers
  `/login/mfa` ;
- `mvc/controllers/mfa_challenge_controller.py` — `GET /login/mfa` verifie
  le challenge, `POST /login/mfa` valide le code ;
- `mvc/models/mfa_model.py` — `get_active_mfa_factors(user_id)` et
  `get_user_by_id(user_id)` pour la persistance ;
- `mvc/views/auth/mfa_challenge.html` — formulaire de code MFA minimal.

Le controleur accepte `_load_factors` et `_finalize_login` injectables pour
les tests sans base de donnees reelle.

### Revalidation MFA

API :

- `require_recent_mfa(request, max_age_minutes=15, now=None)`
- `verify_mfa_revalidation(request, code, factors, recovery_codes=(), now=None)`
- `mark_mfa_revalidated(request, user_id, now=None)`
- `has_recent_mfa_revalidation(request, max_age_minutes=15, now=None)`
- `clear_mfa_revalidation(request)`
- `MfaRevalidationResult`

La revalidation sert aux actions sensibles deja authentifiees : changement de
mot de passe, action admin, export sensible, etc.

### Verification d'identite

`verify_mfa_revalidation` et `mark_mfa_revalidated` exigent que :

1. La session courante soit authentifiee (`authentifie=True`).
2. L'utilisateur de la session corresponde au `user_id` passe en parametre
   (`session["user"]["id"] == user_id`).

Si l'une des conditions echoue, la fonction echoue silencieusement :
`verify_mfa_revalidation` retourne `None`, `mark_mfa_revalidated` est un
no-op. **Le compteur de rate-limit n'est pas incremente** — un echec
d'identite n'est pas une tentative de code MFA, c'est une erreur d'usage.

L'evenement audit `mfa.revalidation.identity_mismatch` est emis pour
permettre la detection d'anomalies en production. Sa presence signale soit
un bug applicatif (le controleur passe un mauvais `user_id`), soit une
tentative deliberee.

```python
from core.auth import AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH
from forge_mvc_mfa import verify_mfa_revalidation

# La session doit etre authentifiee pour user_id=42.
# verify_mfa_revalidation retourne None sinon, sans incrementer le rate-limit.
result = verify_mfa_revalidation(request, user_id=42, code=code, factors=factors)
```

### Persistence de session MFA sur tous les backends

Les fonctions `start_mfa_challenge`, `clear_mfa_challenge`, `mark_mfa_revalidated`
et `clear_mfa_revalidation` persistent les changements de session via un cycle
explicite read-modify-write garantissant la compatibilite avec tous les backends :

- **`MemorySessionStore`** : `store.get()` retourne une reference vivante —
  les mutations directes persistent naturellement.
- **`FileSessionStore` / `MariaDbSessionStore`** : `store.get()` retourne une
  copie deserialisee — les mutations directes sont silencieusement perdues.
  La correction passe par `store.replace(session_id, data)` apres modification.

Le helper interne `_persist_session_changes(request, *, set_keys, unset_keys)` :

1. Si `request.session` est un `dict` (FakeRequest ou session directe) : mutation en place.
2. Sinon : `store.get()` → modification → `store.replace()` pour ecriture complete.

La methode `replace()` a ete ajoutee au contrat `SessionStore` et implementee
dans les trois backends. Elle remplace integralement les donnees d'une session
(sans merge), contrairement a `set()` qui fusionne.

## OIDC

OIDC n'est pas fourni par Forge. La complexite d'une implementation
OIDC complete depasse ce qui peut etre livre dans une release publique stable.

Les elements d'un flux OIDC rigoureux incluent : generation de state, nonce
et PKCE S256 ; echange reseau du code contre les tokens au `token_endpoint` ;
validation du JWT / ID token (signature JWKS, claims `iss`, `aud`, `exp`,
`nonce`) ; decouverte du provider (`/.well-known/openid-configuration`) ;
liaison compte local / identite externe. Aucune de ces parties n'est fournie
par Forge.

**Pour integrer OIDC dans une application Forge**, utilisez une bibliotheque
tierce (`authlib`, `python-keycloak`, etc.) et appelez `login_user()` apres
validation complete de l'identite externe.

Le code OIDC experimente dans les versions 2.x reste accessible via l'historique
git (`git log -- core/auth/experimental/oidc.py`). Il ne sera pas reintegre
sans un ticket dedie `OIDC-IMPLEMENT-COMPLETE-001` partant d'une page blanche.

## Auth/User vers RBAC

`user_roles` est le pont optionnel entre les utilisateurs locaux et les roles
RBAC existants.

> ℹ️ Cette section utilise des symboles fournis par le module
> optionnel `forge-mvc-rbac` (`pip install --pre forge-mvc-rbac` — publié sur PyPI).

```python
from forge_mvc_rbac import (
    create_auth_user_role,
    get_user_permissions,
    get_user_role_ids,
    user_has_permission,
    require_user_permission,
)
```

Flux de resolution :

```text
session Auth/User -> user_id -> user_roles -> roles -> role_permissions -> permissions
```

### `user_roles.sql`

```sql
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    INDEX idx_user_roles_user_id (user_id),
    INDEX idx_user_roles_role_id (role_id),
    CONSTRAINT fk_user_roles_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role_id
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

`require_user_permission("article.edit")` lit l'utilisateur Auth/User connecte
et interroge le resolver `user_roles -> roles -> permissions`. Il retourne `401`
si aucun utilisateur Auth/User n'est connecte et `403` si la permission manque.

### Difference avec le RBAC historique

`@require_permission(...)`, fourni par `forge_mvc_rbac`, reste le decorateur
historique. Il lit les permissions deja presentes dans `request.permissions` ou
dans la session RBAC historique. Il ne lit pas automatiquement `user_roles`.

`require_user_permission(...)`, fourni par `core.auth`, est le decorateur serveur
pour Auth/User + RBAC.

`can(...)` dans Jinja est un helper d'affichage. Il peut utiliser le contexte
Auth/User injecte par `BaseController.render(..., request=request)` ou le mode
historique. Il ne remplace jamais une protection serveur.

Pour la documentation complète des rôles, permissions, decorateurs et helpers
Jinja, voir [RBAC — Contrôle d'accès](rbac.md).

## Administration CLI

Les commandes Auth/User disponibles dans cette copie de Forge sont :

Pour les signatures complètes et la description de chaque option, voir le
[guide de référence](reference.md).

```bash
forge auth:init
forge auth:doctor
forge auth:status
forge auth:list-sql
forge auth:user:create --email admin@example.com --password-prompt
forge auth:user:list
forge auth:user:show --email admin@example.com
forge auth:user:disable --email user@example.com
forge auth:user:enable --email user@example.com
forge auth:user:password --email user@example.com --password-prompt
forge auth:user:role:add --email user@example.com --role admin
forge auth:user:role:remove --email user@example.com --role admin
forge auth:user:roles --email user@example.com
```

`forge auth:init` cree ou preserve les SQL optionnels suivants :

- `users.sql`
- `auth_tokens.sql`
- `auth_mfa_factors.sql`
- `auth_mfa_recovery_codes.sql`
- `user_roles.sql`
- `auth_audit_log.sql`
- `auth_rate_limit_attempts.sql`

La commande ne cree aucun utilisateur, aucun token, aucun facteur MFA, aucun
role utilisateur, aucun audit et aucune tentative rate limit.
Elle n'applique pas non plus le SQL.

Les commandes d'administration utilisateur n'affichent aucun mot de passe,
hash, token ou secret MFA. Elles s'appuient sur la configuration projet
(`config.py`, `env/dev`, variables `DB_APP_*`) et sur la table optionnelle
`users`.

Les commandes de roles utilisateur manipulent uniquement la table optionnelle
`user_roles` :

- `auth:user:role:add` attribue a un utilisateur un role RBAC deja existant ;
- `auth:user:role:remove` retire cette association ;
- `auth:user:roles` liste les roles attribues.

Elles ne creent aucun utilisateur, aucun role et aucune permission. Les roles
et permissions restent definis par le RBAC (`roles`, `permissions`,
`role_permissions`). Le parametre `--role` accepte un id numerique, un slug ou
un nom de role existant.

### Erreurs et conseils CLI

Les erreurs Admin CLI suivent la convention :

```
Erreur : <message>
Conseil : <suggestion>
```

| Erreur | Conseil associe |
|---|---|
| Indiquez --id ou --email. | Exemple : forge auth:user:disable --email utilisateur@domaine.com |
| Utilisez --id ou --email, pas les deux. | Choisissez un seul identifiant : --id ou --email. |
| Utilisateur id=X introuvable. | Verifiez l'identifiant avec forge auth:user:list |
| Utilisateur 'email' introuvable. | Verifiez l'email avec forge auth:user:list |
| Email invalide. | Format attendu : utilisateur@domaine.com |
| Mot de passe obligatoire. | Utilisez --password-prompt pour saisir de maniere securisee. |
| Table users introuvable. | Lancez d'abord forge auth:init puis forge db:apply. |
| Base de donnees Auth/User indisponible. | Verifiez env/dev, DB_APP_* et DB_NAME. |

### Evenements d'audit admin

Les commandes d'etat et de role emettent des evenements d'audit via
`log_auth_event()` apres chaque operation reussie :

| Commande | Evenement |
|---|---|
| `auth:user:disable` | `user.disabled` |
| `auth:user:enable` | `user.enabled` |
| `auth:user:password` | `user.password_changed` |
| `auth:user:role:add` | `user_role.added` |
| `auth:user:role:remove` | `user_role.removed` |

L'evenement `user.not_found` est emis si un utilisateur cible est introuvable
lors d'une operation d'administration (sans bloquer l'erreur retournee).

Aucune de ces journalisations n'inclut de mot de passe, hash, token ou secret.

## Audit Auth

`AuthAuditEvent` represente un evenement d'audit Auth/User lisible et stockable.

```python
from core.auth import AUTH_EVENT_LOGIN_SUCCESS, create_auth_audit_event

event = create_auth_audit_event(
    event_type=AUTH_EVENT_LOGIN_SUCCESS,
    user_id=1,
    ip_address="192.0.2.10",
    user_agent="Mozilla/5.0",
    metadata={"method": "password"},
)
```

API :

- `AuthAuditEvent`
- `normalize_auth_audit_event(data)`
- `validate_auth_audit_event_contract(data)`
- `is_valid_auth_audit_event(event)`
- `create_auth_audit_event(...)`
- `sanitize_auth_audit_metadata(metadata)`
- `log_auth_event(event_type, *, user_id, ip_address, user_agent, metadata)`
- `safe_log_auth_event(...)` — version resiliente, recommandee pour la plupart des usages
- `get_audit_failure_count()` — compteur d'echecs de `safe_log_auth_event` (monitoring)
- `reset_audit_failure_count()` — reinitialise le compteur (tests)

### Resilience des appels d'audit

L'audit auth est **best-effort** par defaut : un echec du logger ne doit jamais
bloquer un flux utilisateur critique (login, MFA, reset).

Forge fournit deux fonctions pour emettre un evenement d'audit :

- **`log_auth_event(...)`** : appel **strict**. Propage `InvalidAuthAuditEventError`
  si les parametres sont invalides (event_type vide, user_id negatif, metadata non-dict),
  ou toute exception emise par le logger en cas de defaillance interne.
  Reserve aux cas ou l'appelant doit savoir precisement si l'audit a reussi.

- **`safe_log_auth_event(...)`** : appel **resilient**, **recommande pour la
  quasi-totalite des cas**. Tente l'enregistrement, attrape les exceptions, et
  retourne `True`/`False`. Ne propage jamais d'exception.

Une verification de securite (rate-limit, code TOTP, identite de session)
ne doit jamais etre bloquee par un echec d'audit.
`safe_log_auth_event` garantit ce comportement par defaut.

Les echecs de `safe_log_auth_event` sont :

1. **Logges** via le logger Python `forge.auth.audit` au niveau `WARNING`
   avec le traceback complet (`exc_info=True`). Configurer ce logger pour
   que les warnings remontent vers la sortie souhaitee (stderr, fichier,
   agregateur).

2. **Comptes** dans un compteur accessible via `get_audit_failure_count()`.
   Utile pour un endpoint de healthcheck ou un monitoring externe.

```python
from core.auth import safe_log_auth_event, AUTH_EVENT_MFA_RATE_LIMITED

# Le code continue qu'il y ait succes ou echec d'audit
safe_log_auth_event(
    AUTH_EVENT_MFA_RATE_LIMITED,
    user_id=user_id,
    ip_address=request.ip,
    metadata={"endpoint": "challenge"},
)
```

`log_auth_event()` journalise un evenement via le logger Python `forge.auth.audit`.
Les evenements d'echec (`login.failed`, `mfa.challenge.failed`, etc.) sont emis
au niveau `WARNING` ; les autres au niveau `INFO`.
Les mots de passe, tokens et codes MFA ne sont jamais inclus dans les logs.

```python
from core.auth.audit import log_auth_event, AUTH_EVENT_LOGIN_SUCCESS

# Appel direct — leve si les parametres sont invalides
log_auth_event(
    AUTH_EVENT_LOGIN_SUCCESS,
    user_id=utilisateur["UtilisateurId"],
    ip_address=request.ip,
)
```

Configurez le logger dans votre application :

```python
import logging
logging.getLogger("forge.auth.audit").setLevel(logging.INFO)
```

Evenements standards :

- `login.success`
- `login.failed`
- `logout`
- `password_reset.requested`
- `password_reset.completed`
- `email.verified`
- `mfa.challenge.required`
- `mfa.challenge.success`
- `mfa.challenge.failed`
- `mfa.revalidation.success`
- `mfa.revalidation.failed`
- `mfa.revalidation.identity_mismatch` — session non authentifiee ou user_id different du user courant
- `user.disabled`
- `user.enabled`
- `user.password_changed`
- `user_role.added`
- `user_role.removed`
- `oidc.account_linked`

`metadata` est nettoye avant stockage applicatif. Les cles sensibles retirees
incluent `password`, `password_hash`, `token`, `raw_token`, `access_token`,
`refresh_token`, `id_token`, `secret`, `secret_hash`, `totp_secret`,
`recovery_code` et `code_verifier`.

### `auth_audit_log.sql`

```sql
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(120) NOT NULL,
    user_id INT NULL,
    actor_user_id INT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    metadata_json TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auth_audit_log_event_type (event_type),
    INDEX idx_auth_audit_log_user_id (user_id),
    INDEX idx_auth_audit_log_actor_user_id (actor_user_id),
    INDEX idx_auth_audit_log_created_at (created_at),
    CONSTRAINT fk_auth_audit_log_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_auth_audit_log_actor_user_id
        FOREIGN KEY (actor_user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Forge ne branche pas automatiquement l'audit dans login/reset/MFA/OIDC/admin.

### Architecture audit — trois briques distinctes

Forge fournit trois briques indépendantes, sans les assembler automatiquement.
La décision de persistance appartient à l'application (ADR-008).

**Brique 1 — Contrat d'événement** : `AuthAuditEvent`, validation, 20+ types
normalisés. Format garanti pour tout consommateur.

**Brique 2 — Émission Python** : `safe_log_auth_event()` émet vers le logger
`forge.auth.audit`. Le handler (et donc le destinataire final) est configuré
par l'application. Par défaut, aucun handler n'est ajouté — les événements
remontent au logging Python standard.

**Brique 3 — Table SQL latente** : `auth_audit_log.sql` fournit un schéma prêt.
**Forge n'écrit pas dans cette table.** C'est une infrastructure optionnelle.

### Brancher la persistance SQL (exemple applicatif)

Si l'application veut persister les audits en base, elle peut configurer un
handler Python logging ou un wrapper explicite. Exemple avec un handler :

```python
import logging
import json


class AuditSqlHandler(logging.Handler):
    """Persiste les événements d'audit forge.auth.audit en base."""

    def emit(self, record):
        try:
            event = record.msg  # AuthAuditEvent
            _insert_audit(event)
        except Exception:
            self.handleError(record)


def _insert_audit(event):
    # Adapter à votre couche d'accès DB
    from mvc.db import execute
    execute(
        "INSERT INTO auth_audit_log "
        "(event_type, user_id, ip_address, user_agent, metadata_json) "
        "VALUES (%s, %s, %s, %s, %s)",
        (
            event.event_type,
            event.user_id,
            event.ip_address,
            event.user_agent,
            json.dumps(event.metadata or {}),
        ),
    )


# Dans l'initialisation de l'application (ex. app.py ou config.py)
logging.getLogger("forge.auth.audit").addHandler(AuditSqlHandler())
```

Ce snippet est documentaire — à adapter au modèle d'accès DB de l'application.
Voir [ADR-008](adr/008-auth-audit-architecture.md) pour les approches
alternatives (wrapper applicatif, stream externe).

## Rate limit Auth

Le rate limit Auth/User represente des tentatives d'actions sensibles et calcule
une decision anti-bruteforce a partir des tentatives chargees par l'application.

```python
from core.auth import (
    AUTH_RATE_LIMIT_LOGIN,
    AuthRateLimitRule,
    check_auth_rate_limit,
    create_auth_rate_limit_attempt,
)

rule = AuthRateLimitRule(
    action=AUTH_RATE_LIMIT_LOGIN,
    max_attempts=5,
    window_seconds=900,
)

decision = check_auth_rate_limit(
    action=AUTH_RATE_LIMIT_LOGIN,
    key=email,
    attempts=load_attempts(email),
    rule=rule,
)
```

API :

- `AuthRateLimitAttempt`
- `AuthRateLimitRule`
- `AuthRateLimitDecision`
- `normalize_rate_limit_key(value)`
- `normalize_auth_rate_limit_attempt(data)`
- `validate_auth_rate_limit_attempt_contract(data)`
- `is_valid_auth_rate_limit_attempt(attempt)`
- `normalize_auth_rate_limit_rule(data)`
- `validate_auth_rate_limit_rule_contract(data)`
- `is_valid_auth_rate_limit_rule(rule)`
- `create_auth_rate_limit_attempt(...)`
- `check_auth_rate_limit(...)`

Actions standards :

- `login`
- `password_reset`
- `mfa_challenge`
- `mfa_revalidation`
- `oidc_callback`

`check_auth_rate_limit` compte uniquement les echecs `success=False` pour le
couple `action + key` dans la fenetre `window_seconds`. Les succes, les autres
actions, les autres cles et les tentatives hors fenetre sont ignores. Si la
limite est atteinte, la decision contient `retry_after_seconds`.

### `auth_rate_limit_attempts.sql`

```sql
CREATE TABLE IF NOT EXISTS auth_rate_limit_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(120) NOT NULL,
    rate_key VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_id INT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auth_rate_limit_action_key (action, rate_key),
    INDEX idx_auth_rate_limit_created_at (created_at),
    INDEX idx_auth_rate_limit_user_id (user_id),
    CONSTRAINT fk_auth_rate_limit_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

La colonne SQL s'appelle `rate_key`, car `key` peut etre ambigu. Forge ne stocke
aucun mot de passe, token ou secret dans les tentatives et ne branche pas
automatiquement cette protection dans les flux Auth.

## Flux recommandes

### Login classique sans MFA

```python
from core.auth import authenticate_user, login_user

user = authenticate_user(email, password, load_user_by_email)

if user is None:
    return invalid_credentials_response()

login_user(request, user)
return redirect("/dashboard")
```

L'application peut ensuite mettre a jour `users.last_login_at`, stocker un audit
`login.success`, ou enregistrer une tentative rate limit reussie si elle le
souhaite.

### Login avec MFA

> ℹ️ Cette section utilise des symboles fournis par le module
> optionnel `forge-mvc-mfa` (`pip install --pre forge-mvc-mfa` — publié sur
> PyPI depuis `1.0.0-beta.9`, statut Alpha).

```python
from core.auth import authenticate_user, login_user
from forge_mvc_mfa import is_mfa_enabled, start_mfa_challenge

user = authenticate_user(email, password, load_user_by_email)

if user is None:
    return invalid_credentials_response()

factors = load_mfa_factors(user.id)

if is_mfa_enabled(factors):
    start_mfa_challenge(request, user)
    return show_mfa_form()

login_user(request, user)
```

Puis, dans l'etape MFA :

```python
from core.auth import login_user
from forge_mvc_mfa import verify_mfa_challenge

result = verify_mfa_challenge(
    request,
    code,
    factors=load_mfa_factors(user_id),
    recovery_codes=load_recovery_codes(user_id),
)

if result is None:
    return invalid_mfa_response()

user = load_user_by_id(result.user_id)
login_user(request, user)
```

Forge ne persiste pas `last_used_at` ou `used_at` automatiquement.

### Reset password

```python
raw_token, token_record = create_password_reset_token(user_id=1)
# stocker token_record.token_hash, envoyer raw_token

result = reset_password_with_token(raw_token, token_record, new_password)

if result is not None:
    # users.password_hash = result.password_hash
    # auth_tokens.used_at = result.used_at
    pass
```

### Verification email

```python
raw_token, token_record = create_email_verification_token(user_id=1)
# stocker token_record.token_hash, envoyer raw_token

if verify_email_verification_token(raw_token, token_record):
    verified_at = email_verification_timestamp()
    # users.email_verified_at = verified_at
    # auth_tokens.used_at = verified_at
```

### Protection route avec `require_user_permission`

> ℹ️ Cette section utilise des symboles fournis par le module
> optionnel `forge-mvc-rbac` (`pip install --pre forge-mvc-rbac` — publié sur PyPI).

```python
from forge_mvc_rbac import require_user_permission

@require_user_permission("articles.edit")
def edit_article(request, article_id):
    ...
```

Pour l'affichage :

```jinja2
{% if can("articles.edit") %}
  <a href="/articles/{{ article.id }}/edit">Modifier</a>
{% endif %}
```

Le helper Jinja masque l'action ; le decorateur serveur protege la route.

### Action sensible avec revalidation MFA

> ℹ️ Cette section utilise des symboles fournis par le module
> optionnel `forge-mvc-mfa` (`pip install --pre forge-mvc-mfa` — publié sur
> PyPI depuis `1.0.0-beta.9`, statut Alpha).

```python
from forge_mvc_mfa import require_recent_mfa

def change_password(request):
    if not require_recent_mfa(request):
        return redirect("/mfa/revalidate")
    ...
```

Puis :

```python
result = verify_mfa_revalidation(
    request,
    code,
    factors=load_mfa_factors(user_id),
    recovery_codes=load_recovery_codes(user_id),
)

if result is None:
    return invalid_mfa_response()
```

### Rate limit autour d'un login applicatif

```python
from core.auth import (
    AUTH_RATE_LIMIT_LOGIN,
    AuthRateLimitRule,
    check_auth_rate_limit,
    create_auth_rate_limit_attempt,
)

rule = AuthRateLimitRule(
    action=AUTH_RATE_LIMIT_LOGIN,
    max_attempts=5,
    window_seconds=900,
)

decision = check_auth_rate_limit(
    action=AUTH_RATE_LIMIT_LOGIN,
    key=email,
    attempts=load_login_attempts(email),
    rule=rule,
)

if not decision.allowed:
    return too_many_attempts(decision.retry_after_seconds)

user = authenticate_user(email, password, load_user_by_email)
attempt = create_auth_rate_limit_attempt(
    action=AUTH_RATE_LIMIT_LOGIN,
    key=email,
    ip_address=request.ip,
    success=user is not None,
)
# stocker attempt dans auth_rate_limit_attempts
```

## Limites restantes

Forge ne fournit pas encore :

- interface HTML admin utilisateurs ;
- routes Auth generees automatiquement ;
- middleware global Auth/User ;
- envoi automatique d'emails ;
- echange reseau OIDC code -> token ;
- validation cryptographique JWT ;
- WebAuthn / passkeys ;
- SAML ;
- OAuth multi-provider avance ;
- multi-tenant Auth/User ;
- consultation CLI ou HTML du journal d'audit ;
- consultation CLI ou HTML des tentatives rate limit ;
- politiques complexes d'organisation ou de delegation admin.

Ces limites sont volontaires. Forge fournit des briques explicites ; les
applications choisissent leurs flux, leurs routes, leur persistance et leurs
politiques metier.

## Voir aussi

- [RBAC — Contrôle d'accès](rbac.md) — rôles, permissions, décorateurs serveur, helper Jinja
- [Sécurité en production](production-security.md) — checklist déploiement, headers, CSRF, secrets
- [Référence CLI](reference.md) — toutes les commandes `forge` avec signatures complètes
- [ADR-001 — Stratégie d'authentification Forge 2.x](adr/001-auth-strategy.md)
- [ADR-002 — Stratégie de session Forge 2.x](adr/002-session-strategy.md)
