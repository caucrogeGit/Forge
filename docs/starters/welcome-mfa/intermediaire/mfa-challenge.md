# Challenge de connexion

Objectif : le **second facteur** à la connexion — ouvrir un challenge après le mot
de passe, puis le valider.

**Ce que vous allez apprendre :** `start_mfa_challenge` ouvre un challenge
**temporaire en session** (sans connecter l'utilisateur) ; `verify_mfa_challenge`
confronte le code (TOTP ou récupération) au challenge, avec tentatives limitées.

Deuxième palier du **niveau intermédiaire** de la progression MFA.

!!! note "Module opt-in — clé requise"
    Ce starter suppose `forge-mvc-mfa` installé et `FORGE_MFA_SECRET_KEY` configurée.
    La démo travaille **en session** avec un utilisateur démo.

## Ce que ce starter montre

- `start_mfa_challenge(request, user)` → challenge ouvert en session ;
- `verify_mfa_challenge(request, code, factors)` → succès / échec ;
- un facteur démo gardé en session.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.start_mfa_challenge` | Ouvrir un challenge MFA temporaire en session. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.verify_mfa_challenge` | Vérifier un code contre le challenge. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-challenge` : un secret démo s'affiche ; saisissez
un code pour valider le challenge.

## Le contrôleur (extrait)

```python
# mvc/controllers/mfa_challenge_controller.py
from core.auth.user import AuthUser
from forge_mvc_mfa import AuthMfaFactor, start_mfa_challenge, verify_mfa_challenge

_DEMO_USER = AuthUser(id=1, email="demo@forge.example", password_hash="(démo)", is_active=True)

# index : ouvre le challenge après l'auth primaire
start_mfa_challenge(request, _DEMO_USER)

# verify : confronte le code aux facteurs de l'utilisateur
result = verify_mfa_challenge(request, code, [AuthMfaFactor(**data)])
```

### Comprendre ce code

- Le challenge **ne connecte pas** : il mémorise « cet utilisateur a passé le 1er
  facteur, en attente du 2e ». La connexion réelle suit la validation.
- `verify_mfa_challenge` accepte un code **TOTP ou de récupération**, et limite les
  tentatives (anti-bruteforce).
- Dans une vraie application, le challenge suit le login et les facteurs viennent de
  la base ; ici on simule en session.

## À retenir

- Le challenge est l'étape **entre** mot de passe et connexion effective.
- Il vit **en session**, temporaire, à tentatives limitées.
- TOTP ou code de récupération valident indifféremment le challenge.

## Après ce starter

Le 2e facteur fonctionne. La suite : les codes de récupération en secours.

[Codes de récupération](mfa-recovery.md)
