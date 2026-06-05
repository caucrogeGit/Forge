# Revalidation (step-up)

Objectif : exiger une **MFA récente** avant une action sensible, même déjà connecté
— le *step-up*.

**Ce que vous allez apprendre :** `mark_mfa_revalidated` enregistre une revalidation
en session ; `has_recent_mfa_revalidation` dit si elle est encore fraîche. Le
décorateur `require_recent_mfa` s'appuie sur ces briques pour protéger une route.

Premier palier du **niveau avancé** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé. Démo **en session** (utilisateur
    démo), aucune clé requise.

## Ce que ce starter montre

- `has_recent_mfa_revalidation(request, user_id)` → l'état courant ;
- `mark_mfa_revalidated(request, user_id)` → enregistre une revalidation ;
- le principe du décorateur `require_recent_mfa`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.mark_mfa_revalidated` | Enregistrer une revalidation MFA en session. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.has_recent_mfa_revalidation` | Dire si la revalidation est encore récente. | [MFA](../../../reference/api.md) |
| `forge_mvc_mfa.require_recent_mfa` | Décorateur protégeant une action sensible. | [MFA](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-revalidation` : l'état « MFA récente » passe à oui
après avoir cliqué « Revalider ».

## Le contrôleur (extrait)

```python
# mvc/controllers/mfa_revalidation_controller.py
from forge_mvc_mfa import has_recent_mfa_revalidation, mark_mfa_revalidated

# revalidate : enregistre une revalidation maintenant
mark_mfa_revalidated(request, _DEMO_USER_ID)

# une action sensible vérifie la fraîcheur
recent = has_recent_mfa_revalidation(request, _DEMO_USER_ID)
```

### Comprendre ce code

- Le *step-up* protège les actions à risque (changer le mot de passe, supprimer le
  compte) même au sein d'une session déjà authentifiée.
- La fraîcheur expire (`max_age_minutes`) : passé le délai, on redemande une MFA.
- `require_recent_mfa` est le **décorateur** qui applique cette règle à une route.

## À retenir

- Le step-up exige une MFA **récente** avant une action sensible.
- `mark_mfa_revalidated` / `has_recent_mfa_revalidation` sont les briques.
- `require_recent_mfa` les applique de façon déclarative à une route.

## Après ce starter

La suite : empêcher le rejeu d'un même code TOTP.

[Anti-rejeu TOTP](mfa-replay.md)
