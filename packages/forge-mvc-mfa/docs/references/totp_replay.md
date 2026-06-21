# La protection anti-rejeu TOTP dans Forge

Ce document décrit la protection contre la réutilisation d'un même code TOTP.

Le fichier de code correspondant est `forge_mvc_mfa/totp_replay.py`.

## 1. À quoi sert ce module ?

Un code TOTP reste valide pendant une fenêtre de quelques secondes.
Sans protection, un code intercepté pourrait être **rejoué** dans cette fenêtre.

Ce module mémorise les codes déjà acceptés (par facteur et par *step* temporelle) pour refuser un second usage.
Il fonctionne en mémoire, sur le même modèle que les autres compteurs du framework.

## 2. L'API

| Fonction | Comportement |
|---|---|
| `step_for_time(at_seconds)` | le numéro de *step* TOTP pour un timestamp Unix |
| `is_replay(factor_id, step)` | `True` si cette step a déjà été utilisée pour ce facteur |
| `record_used(factor_id, step)` | enregistre qu'un code de cette step a été accepté |
| `purge_old(now_seconds=None)` | supprime les entrées de plus de 24 h ; retourne le nombre purgé |
| `purge_all_totp_replay()` | vide le store complet (réservé aux tests) |

## 3. Le schéma d'usage

```python
from forge_mvc_mfa import step_for_time, is_replay, record_used

step = step_for_time(now_seconds)
if is_replay(factor_id, step):
    return False          # code déjà utilisé, refusé
# ... vérifier le code TOTP ...
record_used(factor_id, step)
```

On vérifie le rejeu **avant** d'accepter, puis on enregistre la step une fois le code validé.

## 4. Contextes d'utilisation

- **Vérification TOTP** : encadrer `verify_totp_code` par `is_replay` / `record_used`.
- **Entretien** : `purge_old()` périodiquement pour borner la mémoire.

## 5. Voir aussi

- [Le cœur MFA](mfa.md) : `verify_totp_code` à protéger du rejeu.
- [Vue d'ensemble et politique de sécurité](../reference.md).
