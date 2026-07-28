# Anti-rejeu TOTP

Objectif : empêcher qu'un même code TOTP soit **rejoué** dans sa fenêtre de validité.

**Ce que vous allez apprendre :** un code reste valide ~30 s.
`record_used` marque une *step* (fenêtre de temps) consommée pour un facteur ; `is_replay` refuse ensuite sa réutilisation.
`step_for_time` calcule la step d'un instant.

Deuxième palier du **niveau avancé** de la progression MFA.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-mfa` installé.
    État **en mémoire**, aucune base, aucune clé.

## Ce que ce starter montre

- `step_for_time(time.time())` → la step courante ;
- `record_used(factor_id, step)` puis `is_replay(factor_id, step)` → rejeu refusé ;
- un état **en mémoire** (comme le rate-limit).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_mfa.step_for_time` | Calculer la step TOTP d'un instant. | MFA |
| `forge_mvc_mfa.record_used` | Marquer une step consommée pour un facteur. | MFA |
| `forge_mvc_mfa.is_replay` | Refuser une step déjà consommée. | MFA |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/mfa-replay` et cliquez deux fois dans la même fenêtre (~30 s) : la seconde est refusée.

## Le contrôleur

```python
# mvc/controllers/mfa_replay_controller.py
import time

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import is_replay, record_used, step_for_time

_FACTOR_ID = 1


class MfaReplayController(BaseController):
    """Starter pédagogique : empêcher le rejeu d'un code TOTP."""

    @staticmethod
    def index(request: Request) -> Response:
        step = step_for_time(time.time())
        return BaseController.render(
            "mfa_replay/index.html",
            context={
                "csrf_token": BaseController.csrf_token(request),
                "step": step,
                "replayed": is_replay(_FACTOR_ID, step),
            },
            request=request,
        )

    @staticmethod
    def use(request: Request) -> Response:
        step = step_for_time(time.time())
        already = is_replay(_FACTOR_ID, step)
        if not already:
            record_used(_FACTOR_ID, step)
        return BaseController.render(
            "mfa_replay/index.html",
            context={
                "csrf_token": BaseController.csrf_token(request),
                "step": step,
                "accepted": not already,
                "replayed": is_replay(_FACTOR_ID, step),
            },
            request=request,
        )
```

## La vue

```html
<!-- mvc/views/mfa_replay/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Anti-rejeu TOTP - Forge</title>
</head>
<body>
  <h1>Anti-rejeu TOTP</h1>

  <p>Step TOTP courante : <code>{{ step }}</code></p>
  <p>Déjà consommée pour le facteur démo : <strong>{% if replayed %}oui{% else %}non{% endif %}</strong></p>

  {% if accepted is defined %}
    {% if accepted %}
    <p data-level="success">✓ Step consommée maintenant - toute réutilisation sera refusée.</p>
    {% else %}
    <p data-level="error">✗ Step déjà consommée : rejeu refusé.</p>
    {% endif %}
  {% endif %}

  <form method="post" action="/mfa-replay">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">Consommer la step courante</button>
  </form>

  <p>Cliquez deux fois dans la même fenêtre (~30 s) : la seconde est refusée.</p>
</body>
</html>
```

## La route

```python
# mvc/routes/__init__.py
from mvc.controllers.mfa_replay_controller import MfaReplayController

with router.group("", public=True) as public:
    public.add("GET", "/mfa-replay", MfaReplayController.index, name="mfa_replay_index")
    public.add("POST", "/mfa-replay", MfaReplayController.use, name="mfa_replay_use")
```

### Comprendre ce code

- Sans anti-rejeu, un attaquant interceptant un code valide pourrait le **rejouer** dans les ~30 s.
- On raisonne par **step** (numéro de fenêtre), pas par code : une step consommée est refusée pour ce facteur.
- L'état vit **en mémoire**, avec purge opportoniste des vieilles steps.

## À retenir

- Un code TOTP ne doit être accepté **qu'une fois** dans sa fenêtre.
- `record_used` + `is_replay` portent cette garde, par facteur et par step.
- `verify_totp_code` à lui seul ne protège pas du rejeu : d'où cette brique.

## Après ce starter

Dernier palier : protéger le secret lui-même, chiffré au repos.

[Secret chiffré au repos](mfa-crypto.md)
