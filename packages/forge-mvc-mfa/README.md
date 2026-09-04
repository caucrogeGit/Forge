# forge-mvc-mfa

Brique MFA (TOTP + codes de récupération) pour le framework Forge.

## Un opt-in officiel

Cet opt-in **suit la version du cœur** de Forge et n'a pas de cycle de maturité
propre : sa version est celle du `pyproject.toml` racine (`OPTINS-MATURITY-FOLLOWS-CORE-001`).

Depuis `SEC-MFA-SECRET-ENCRYPTION-001`, **le secret TOTP est chiffré au repos**
via Fernet (`cryptography`). La clé est lue depuis `FORGE_MFA_SECRET_KEY`,
obligatoire au démarrage, et `MFA-KEY-ROTATION-001` en livre la rotation.

Le module est **publié sur PyPI** (`MFA-PYPI-READY-001`). Il reste **hors** de
`forge-mvc[all]` : l'installer directement, car l'activation de la MFA est un
choix de sécurité explicite de l'application.

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

### Rotation de la clé — `FORGE_MFA_SECRET_KEY_PREVIOUS`

Changer la clé sans précaution rend tous les secrets TOTP illisibles au même
instant, et chaque porteur d'un facteur perd son second facteur.

`FORGE_MFA_SECRET_KEY_PREVIOUS` déclare les clés retirées, séparées par des
virgules. Elles servent uniquement au déchiffrement, le chiffrement utilisant
toujours la clé courante.

```
FORGE_MFA_SECRET_KEY=<nouvelle clé>
FORGE_MFA_SECRET_KEY_PREVIOUS=<ancienne clé>
```

Les secrets existants se rechiffrent ensuite au rythme voulu, puis la variable
se retire :

```python
from forge_mvc_mfa import rotate_totp_secret, uses_current_key

for facteur in mes_facteurs_totp():
    if not uses_current_key(facteur.totp_secret):
        enregistrer(facteur.id, rotate_totp_secret(facteur.totp_secret))
```

Forge ne balaie pas la base lui-même : la table des facteurs appartient à
l'application, dont Forge ne connaît ni le nom ni les colonnes. Une clé retirée
reste un secret tant qu'elle est déclarée. Voir `MFA-KEY-ROTATION-001` et la
procédure complète dans la référence de l'opt-in.

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

Extrait du cœur par l'ADR-004 (`MFA-EXTRACT-001`). Les anciens chemins
`core.auth.mfa`, `core.auth.recovery` et `core.auth.totp_replay` ont été
retirés depuis, sous une numérotation antérieure au renumérotage vers 1.0.

## Limites connues

- Le registre anti-rejeu vit en mémoire du processus **par défaut**. Forge
  livre `DbTotpReplayStore`, adossé au backend BDD, donc commun à tous les
  workers ; l'application le pose au démarrage en une ligne visible. Les
  sticky sessions ne sont pas la réponse recommandée : elles déplacent le
  problème sans le résoudre.
- Le rate-limit du challenge vit lui aussi en mémoire du processus, et les cinq
  essais deviennent donc `5 × N` workers. La parade se pose au proxy, et la
  configuration Nginx engendrée par `forge deploy:init` la porte sur `/login`
  depuis `DEPLOY-NGINX-RATE-LIMIT-001`. **Le challenge MFA vit sur une autre
  route, que Forge ne connaît pas** : ajoutez un `location` de même forme.
- La rotation de la clé Fernet est livrée (`MFA-KEY-ROTATION-001`) :
  `FORGE_MFA_SECRET_KEY_PREVIOUS`, `rotate_totp_secret`, `uses_current_key`.
  La procédure de sauvegarde de la clé relève de l'exploitant.
