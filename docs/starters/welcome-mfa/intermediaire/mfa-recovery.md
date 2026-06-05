# Codes de récupération

Objectif : générer un lot de **codes de récupération** à usage unique, et en
consommer un quand le TOTP est indisponible.

**Ce que vous allez apprendre :** `create_recovery_codes` génère un lot (montré
**une fois**, stocké **haché**) ; `verify_recovery_code` confronte un code à son
hash ; `consume_recovery_code` le marque utilisé (usage **unique**).

Troisième palier du **niveau intermédiaire** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé. **Aucune clé de chiffrement requise**
    ici : les codes sont **hachés**, pas chiffrés. Démo en session.

## Ce que ce starter montre

- `create_recovery_codes(user_id)` → `RecoveryCodesSetup` (codes bruts + records) ;
- les codes affichés **une seule fois**, les records (hachés) gardés en session ;
- `verify_recovery_code` + `consume_recovery_code` pour utiliser un code.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.create_recovery_codes` | Générer un lot de codes (bruts + records hachés). | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.verify_recovery_code` | Confronter un code à son hash. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.consume_recovery_code` | Marquer un code utilisé (usage unique). | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-recovery` : un lot de codes s'affiche ; saisissez-en
un pour le consommer.

## Le contrôleur (extrait)

```python
# mvc/controllers/mfa_recovery_controller.py
from forge_mvc_mfa import AuthMfaRecoveryCode, consume_recovery_code, create_recovery_codes, verify_recovery_code

setup = create_recovery_codes(_DEMO_USER_ID)   # setup.raw_codes (affichés), setup.code_records (stockés)

for data in records:
    record = AuthMfaRecoveryCode(**data)
    if verify_recovery_code(code, record.code_hash):
        consume_recovery_code(code, record)
        break
```

### Comprendre ce code

- Les codes bruts sont montrés **une seule fois** ; seul leur **hash** est conservé
  (comme un mot de passe).
- `verify_recovery_code` utilise une comparaison à temps constant (anti-timing).
- `consume_recovery_code` garantit l'**usage unique** : un code consommé ne repasse pas.

## À retenir

- Les codes de récupération sauvent l'accès quand le TOTP est perdu.
- Stockés **hachés**, montrés une seule fois, **à usage unique**.
- En production, persistés dans `auth_mfa_recovery_codes`.

## Après ce starter

Vous maîtrisez le flux MFA. La suite (avancé) : le durcissement.

[Bilan du niveau intermédiaire](bilan.md)
