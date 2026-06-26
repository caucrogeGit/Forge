# Filtrer le journal

Objectif : retrouver des entrées précises dans le journal d'audit.

**Ce que vous allez apprendre :** restreindre `get_audit_log` avec des filtres
(`action`, `actor`, `target_type`, `target_id`) et borner le nombre de lignes
avec `limit`.
Les filtres fournis sont combinés en ET.

Deuxième palier du **niveau intermédiaire** de la progression Audit.

## Ce que ce starter montre

- filtrer le journal par `action`, `actor`, `target_type` ou `target_id` ;
- limiter le nombre de lignes lues avec `limit`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `get_audit_log(*, action=..., actor=..., target_type=..., target_id=..., limit=...)` | Renvoie les entrées filtrées, combinées en ET. | Opt-ins |

## 1. Filtrer par cible

```python
from forge_mvc_audit import get_audit_log

# Toutes les actions visant l'élève 42, au plus 20 lignes.
entrees = get_audit_log(target_type="eleve", target_id=42, limit=20)

# Toutes les modifications de note effectuées par un auteur précis.
notes = get_audit_log(action="note.modifiee", actor="prof.dupont")

for entree in notes:
    print(entree.created_at, entree.details)
```

### Comprendre ce code

- Chaque filtre passé (non `None`) restreint la recherche ; plusieurs filtres se combinent en ET.
- `target_id=42` accepte un entier ou une chaîne ; il est comparé sous forme de texte.
- `limit` borne le nombre de lignes renvoyées ; il est plafonné à `MAX_LIMIT` (1000).
- Un `limit` inférieur à 1 lève `AuditError`.
- Sans aucun filtre, on obtient simplement les entrées les plus récentes.

## À retenir

- `get_audit_log` accepte des filtres combinés en ET.
- `limit` borne la lecture, plafonnée à `MAX_LIMIT` (1000).
- Un `limit` inférieur à 1 lève `AuditError`.

## Après ce starter

Vous savez écrire, enrichir et filtrer des traces.
Place au bilan du niveau intermédiaire.

[Bilan intermédiaire](bilan.md)
