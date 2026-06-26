# Relire le journal

Objectif : lire les dernières actions enregistrées dans le journal d'audit.

**Ce que vous allez apprendre :** relire le journal avec `get_audit_log`, qui
renvoie une liste d'objets `AuditEntry`.
Les entrées arrivent des plus récentes aux plus anciennes.
Chaque `AuditEntry` expose les champs d'une trace.

Deuxième palier du **niveau débutant** de la progression Audit.

## Ce que ce starter montre

- récupérer les entrées récentes avec `get_audit_log` ;
- parcourir les `AuditEntry` et lire leurs champs.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `get_audit_log(*, limit=...)` | Renvoie les entrées récentes (id décroissant). | Opt-ins |
| `AuditEntry` | Dataclass figée décrivant une entrée du journal. | Opt-ins |

## 1. Lire les dernières entrées

```python
from forge_mvc_audit import get_audit_log

entrees = get_audit_log(limit=10)
for entree in entrees:
    print(entree.id, entree.created_at, entree.actor, entree.action)
```

### Comprendre ce code

- `get_audit_log(limit=10)` renvoie au plus dix entrées, des plus récentes aux plus anciennes (ordre décroissant par id).
- Le résultat est une `list[AuditEntry]`, vide si le journal ne contient rien.
- Chaque `AuditEntry` est une dataclass figée : ses champs sont `id`, `actor`, `action`, `target_type`, `target_id`, `details`, `created_at`.
- `created_at` est renvoyé sous forme de chaîne (date et heure).

## À retenir

- On relit le journal avec `get_audit_log(...)`.
- Les entrées sont triées de la plus récente à la plus ancienne.
- Une entrée est un `AuditEntry` aux champs explicites.

## Après ce starter

Vous savez écrire et relire une trace.
Place au bilan du niveau débutant.

[Bilan débutant](bilan.md)
