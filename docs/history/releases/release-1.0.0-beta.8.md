# Release — Forge 1.0.0-beta.8

## Statut

Version bêta publique.

Cette version n'est pas encore une version stable.

## Résumé

Forge 1.0.0-beta.8 consolide les modules opt-in `media` et `mfa` après la release beta.7.

## Changements principaux

- `forge-mvc-media` requalifié Alpha et préparé pour une publication future ;
- suppression des shims legacy media dans `core/uploads` ;
- documentation media complétée ;
- `forge-mvc-mfa` : secrets TOTP chiffrés au repos avec Fernet ;
- clé MFA obligatoire : `FORGE_MFA_SECRET_KEY` ;
- `forge-mvc-mfa` requalifié Alpha et préparé pour une publication future ;
- documentation opt-ins alignée ;
- tests MFA et packaging opt-ins renforcés.

## Installation

Après publication PyPI du core :

```bash
pip install --pre forge-mvc==1.0.0b8
```

Les publications opt-ins seront traitées dans des tickets PyPI séparés.

## Limites

- version encore bêta ;
- media et mfa Alpha, non stables ;
- publication PyPI de media et mfa à traiter séparément ;
- rotation de clé MFA non couverte ;
- réorganisation complète de la documentation reportée après stabilisation.
