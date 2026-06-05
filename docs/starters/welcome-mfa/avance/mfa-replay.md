# Anti-rejeu TOTP

Objectif : empêcher qu'un même code TOTP soit **rejoué** dans sa fenêtre de validité.

**Ce que vous allez apprendre :** un code reste valide ~30 s. `record_used` marque une
*step* (fenêtre de temps) consommée pour un facteur ; `is_replay` refuse ensuite sa
réutilisation. `step_for_time` calcule la step d'un instant.

Deuxième palier du **niveau avancé** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé. État **en mémoire**, aucune base,
    aucune clé.

## Ce que ce starter montre

- `step_for_time(time.time())` → la step courante ;
- `record_used(factor_id, step)` puis `is_replay(factor_id, step)` → rejeu refusé ;
- un état **en mémoire** (comme le rate-limit).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.step_for_time` | Calculer la step TOTP d'un instant. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.record_used` | Marquer une step consommée pour un facteur. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.is_replay` | Refuser une step déjà consommée. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-replay` et cliquez deux fois dans la même fenêtre
(~30 s) : la seconde est refusée.

## Le contrôleur (extrait)

```python
# mvc/controllers/mfa_replay_controller.py
import time
from forge_mvc_mfa import is_replay, record_used, step_for_time

step = step_for_time(time.time())
if not is_replay(_FACTOR_ID, step):
    record_used(_FACTOR_ID, step)   # première utilisation acceptée
# is_replay(_FACTOR_ID, step) renvoie désormais True
```

### Comprendre ce code

- Sans anti-rejeu, un attaquant interceptant un code valide pourrait le **rejouer**
  dans les ~30 s.
- On raisonne par **step** (numéro de fenêtre), pas par code : une step consommée est
  refusée pour ce facteur.
- L'état vit **en mémoire**, avec purge opportoniste des vieilles steps.

## À retenir

- Un code TOTP ne doit être accepté **qu'une fois** dans sa fenêtre.
- `record_used` + `is_replay` portent cette garde, par facteur et par step.
- `verify_totp_code` à lui seul ne protège pas du rejeu — d'où cette brique.

## Après ce starter

Dernier palier : protéger le secret lui-même, chiffré au repos.

[Secret chiffré au repos](mfa-crypto.md)
