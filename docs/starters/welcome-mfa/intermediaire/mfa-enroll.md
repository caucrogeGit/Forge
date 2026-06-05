# Enrôler un facteur TOTP

Objectif : créer un facteur TOTP **pending**, puis le **confirmer** — l'enrôlement
en deux temps.

**Ce que vous allez apprendre :** `create_totp_factor` crée un facteur pending dont
le secret est déjà **chiffré au repos** ; `confirm_totp_factor` l'active après
vérification d'un premier code (preuve que l'utilisateur a enregistré le secret).

Premier palier du **niveau intermédiaire** de la progression MFA.

!!! note "Module opt-in — clé requise"
    Ce starter suppose `forge-mvc-mfa` installé et `FORGE_MFA_SECRET_KEY` configurée
    (palier « Installation »). Sans clé, la page reste **pédagogique**.

## Ce que ce starter montre

- `create_totp_factor(user_id)` → un `TotpSetup` (secret, facteur pending, URI) ;
- le facteur pending gardé **en session** pour la démo ;
- `confirm_totp_factor(factor, code)` → facteur actif.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.create_totp_factor` | Créer un facteur TOTP pending (secret chiffré). | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.confirm_totp_factor` | Activer le facteur après vérification d'un code. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-enroll` : un secret/URI s'affiche, saisissez un
code valide pour confirmer le facteur.

## Le contrôleur (extrait)

```python
# mvc/controllers/mfa_enroll_controller.py
import dataclasses
from forge_mvc_mfa import AuthMfaFactor, confirm_totp_factor, create_totp_factor

# index : crée le facteur pending, garde ses champs en session
setup = create_totp_factor(_DEMO_USER_ID, account_name="demo@forge.example")
store.set(sid, {**session, "mfa_enroll_pending_factor": dataclasses.asdict(setup.factor)})

# confirm : reconstruit le facteur et le confirme
active = confirm_totp_factor(AuthMfaFactor(**data), code)
```

### Comprendre ce code

- `create_totp_factor` **ne touche pas la base** : il retourne des objets. La
  **persistance est le job de l'application** — ici on simule avec la session.
- Le secret du facteur (`factor.totp_secret`) est déjà **chiffré** (`enc:…`).
- La confirmation prouve que l'utilisateur a bien enregistré le secret avant de
  l'activer.

## À retenir

- Enrôlement = créer **pending** puis **confirmer** avec un code.
- Le package fournit les objets ; l'application les persiste (`auth_mfa_factors`).
- Le secret est chiffré au repos dès la création.

## Après ce starter

Le facteur est actif. La suite : le second facteur au moment de la connexion.

[Challenge de connexion](mfa-challenge.md)
