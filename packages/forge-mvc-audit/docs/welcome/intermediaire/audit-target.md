# Enrichir une trace

Objectif : décrire précisément l'objet visé par une action.

**Ce que vous allez apprendre :** enrichir une trace avec `target_type`, `target_id` et `details`, en plus de l'`actor`.
Ces champs permettent de savoir non seulement qui a agi, mais sur quoi.

Premier palier du **niveau intermédiaire** de la progression Audit.

!!! note "Module opt-in"
    Si `forge-mvc-audit` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- nommer l'objet visé avec `target_type` et `target_id` ;
- ajouter un complément libre avec `details`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `record_audit(action, *, actor, target_type, target_id, details)` | Enregistre une trace enrichie de sa cible et de détails. | Opt-ins |

## 1. Tracer une action ciblée

```python
from forge_mvc_audit import record_audit

record_audit(
    "note.modifiee",
    actor="prof.dupont",
    target_type="eleve",
    target_id=42,
    details="note de 12 à 14 en mathématiques",
)
```

### Comprendre ce code

- `target_type` nomme la nature de l'objet visé, par exemple `"eleve"`.
- `target_id` identifie cet objet ; on peut passer un entier (ici `42`), il est converti en chaîne au stockage.
- `details` est un texte libre qui complète la trace, sans format imposé.
- Tous ces champs sont facultatifs : on ne renseigne que ce qui a du sens pour l'action.

## À retenir

- `target_type` et `target_id` désignent l'objet concerné par l'action.
- `details` ajoute un complément libre, lisible.
- Ces champs sont optionnels : à vous de choisir ce qui mérite d'être tracé.

## Après ce starter

Vous savez enrichir une trace.
Voyons comment retrouver des entrées précises dans le journal.

[Filtrer le journal](audit-filter.md)
