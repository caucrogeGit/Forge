# Première action d'audit

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-audit` avant de commencer : voir sa [référence](../../reference.md).

Objectif : premier contact avec le module **opt-in** `forge-mvc-audit`.

**Ce que vous allez apprendre :** enregistrer une action importante de l'application dans le journal d'audit.
On écrit une trace avec la fonction `record_audit`, qui renvoie l'identifiant de la ligne créée.
Le module ne décide jamais quoi tracer : l'application le décide.

Premier palier du **niveau débutant** de la progression Audit.

!!! note "Module opt-in"
    Si `forge-mvc-audit` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- enregistrer une action avec `record_audit` ;
- récupérer l'identifiant de la ligne d'audit créée.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `record_audit(action, *, actor=...)` | Enregistre une action et renvoie l'id de la ligne. | Opt-ins |

## 1. Enregistrer une action

```python
from forge_mvc_audit import record_audit

ligne_id = record_audit("eleve.cree", actor="prof.dupont")
print("Trace enregistrée, id :", ligne_id)
```

### Comprendre ce code

- `record_audit("eleve.cree", ...)` insère une ligne dans la table `audit_log`.
- `action` est obligatoire : c'est un libellé court qui nomme l'événement, par exemple `"eleve.cree"` ou `"note.modifiee"`.
- `actor` indique qui a déclenché l'action (un login, un identifiant).
- La fonction renvoie l'identifiant entier de la ligne créée.
- La table doit déjà exister : voir `forge audit:init` puis `forge migration:apply`.

## À retenir

- Une trace s'enregistre avec `record_audit(action, ...)`.
- `action` est obligatoire ; une action vide lève `AuditError`.
- `record_audit` renvoie l'id de la ligne d'audit.

## Après ce starter

Vous avez écrit une première trace.
Voyons comment relire le journal.

[Relire le journal](audit-read.md)
