# Les codes de récupération dans Forge MFA

Ce document décrit la génération et la vérification des codes de récupération MFA.

Le fichier de code correspondant est `forge_mvc_mfa/recovery.py`.

## 1. À quoi sert ce module ?

Si l'utilisateur perd son téléphone, il doit pouvoir se connecter quand même.
Les **codes de récupération** sont un lot de codes à usage unique, générés à l'enrôlement, qui servent de second facteur de secours.

Ils sont stockés **uniquement sous forme de hash** : le code brut n'est jamais persisté.

## 2. Générer un lot

```python
from forge_mvc_mfa import create_recovery_codes

setup = create_recovery_codes(user_id=42, count=10)
setup.raw_codes      # à montrer UNE fois à l'utilisateur
setup.code_records   # AuthMfaRecoveryCode hashés, à stocker
```

`create_recovery_codes` ne écrit pas en base : il retourne les codes bruts (à afficher une seule fois) et les enregistrements hashés (à persister).

## 3. L'API

| Fonction | Comportement |
|---|---|
| `generate_recovery_code()` | génère un code lisible `XXXX-XXXX-XXXX-XXXX` |
| `normalize_recovery_code(code)` | retire les espaces et met en majuscules |
| `hash_recovery_code(code)` | le SHA-256 hexadécimal (64 caractères) du code normalisé |
| `verify_recovery_code(code, code_hash)` | vérifie un code brut contre son hash (temps constant) |
| `create_recovery_codes(user_id, count=10, now=None)` | génère un lot (`RecoveryCodesSetup`) |
| `consume_recovery_code(code, code_record, now=None)` | marque un code comme utilisé après vérification |
| `validate_recovery_code_contract(data)` | valide le contrat minimal |
| `normalize_recovery_code_record(data)` | normalise un dict brut en `AuthMfaRecoveryCode` |
| `is_valid_recovery_code_record(record)` | `True` si l'enregistrement est structurellement valide |

## 4. La sécurité

- les codes sont générés via `secrets.choice()` sur un alphabet sans ambiguïté ;
- ils sont hashés via `hash_recovery_code()` (SHA-256) avant stockage ;
- ils sont vérifiés via `secrets.compare_digest()` (résistant aux attaques temporelles) ;
- un code consommé est marqué utilisé et ne peut plus servir.

## 5. Contextes d'utilisation

- **Enrôlement** : `create_recovery_codes`, afficher `raw_codes` une fois, persister `code_records`.
- **Connexion de secours** : `verify_recovery_code` puis `consume_recovery_code`.

## 6. Voir aussi

- [Le cœur MFA](mfa.md) : le challenge qui accepte aussi un code de récupération.
- [Vue d'ensemble et politique de sécurité](../reference.md).
