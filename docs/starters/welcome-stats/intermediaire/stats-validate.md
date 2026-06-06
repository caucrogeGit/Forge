# Valider un événement

Objectif : refuser un événement mal formé **avant** de l'écrire en base.

**Ce que vous allez apprendre :** `make_event` valide à la construction et
`validate_event` re-vérifie un événement existant. Un nom invalide lève
`StatsEventError` — on refuse avant toute écriture.

Troisième palier du **niveau intermédiaire** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- `make_event(name, ...)` qui valide à la construction ;
- `validate_event(event)` qui re-vérifie ;
- la capture de `StatsEventError`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.make_event` | Construire (et valider) un événement. | [Stats](../../../reference/api.md) |
| `forge_mvc_stats.validate_event` | Re-vérifier un événement existant. | [Stats](../../../reference/api.md) |
| `forge_mvc_stats.StatsEventError` | Erreur si l'événement est invalide. | [Stats](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-validate?name=page_view` (valide) puis
`?name=page.view` (refusé).

## Le contrôleur

```python
# mvc/controllers/stats_validate_controller.py
from forge_mvc_stats import StatsEventError, make_event, validate_event


def _validate_view(name: str) -> dict:
    try:
        event = make_event(name, "Démo", "general", {})
        validate_event(event)
        return {"input": name, "valid": True, "name": event.name, "error": None}
    except StatsEventError as exc:
        return {"input": name, "valid": False, "name": None, "error": str(exc)}
```

### Comprendre ce code

- La validation se fait **à la construction** : un `make_event` invalide lève
  immédiatement, avant tout SQL.
- `validate_event` permet de re-vérifier un événement reçu d'ailleurs (désérialisé,
  par exemple).
- Refuser tôt = pas de données invalides en base.

## À retenir

- Un événement est validé **avant** d'être écrit.
- `make_event` lève à la construction ; `validate_event` re-vérifie.
- `StatsEventError` porte la cause du refus.

## Après ce starter

Vous savez écrire des événements valides. La suite (avancé) : les **consulter**.

[Bilan du niveau intermédiaire](bilan.md)
