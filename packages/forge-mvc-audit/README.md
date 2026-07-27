# forge-mvc-audit

Journal d'audit applicatif opt-in pour Forge : tracer les actions importantes de
l'application (élève créé, note modifiée, QCM corrigé, connexion, rôle changé,
fichier supprimé) dans une table `audit_log`, avec une API explicite.

Périmètre volontairement borné : c'est un **audit applicatif**, pas un SIEM de
cybersécurité. Cohérent avec ADR-008 : Forge fournit la table et le helper, la
décision de tracer reste applicative.

## Installation

```bash
pip install --pre forge-mvc-audit
```

En développement : `pip install -e ./packages/forge-mvc-audit`.

## Mise en place de la table

```bash
forge audit:init        # copie la migration dans mvc/migrations/
forge migration:apply   # crée la table audit_log
```

## Utilisation

```python
from forge_mvc_audit import record_audit, get_audit_log

record_audit("eleve.cree", actor="prof.dupont", target_type="eleve", target_id=42)
record_audit("note.modifiee", actor="prof.dupont", target_type="note", target_id=7, details="12 -> 15")

for entree in get_audit_log(limit=20, actor="prof.dupont"):
    print(entree.created_at, entree.action, entree.target_type, entree.target_id)
```

L'API expose `record_audit`, `get_audit_log`, `AuditEntry`, plus `AuditError`,
`TABLE_NAME` et `MAX_LIMIT`.

## Périmètre

- `record_audit(action, *, actor, target_type, target_id, details, db)` écrit une
  trace et renvoie son identifiant.
- `get_audit_log(*, limit, actor, action, target_type, target_id, db)` relit les
  entrées récentes, filtrables (colonnes en liste blanche).
- Hors périmètre : corrélation d'événements, alerting, rétention automatique,
  détection d'intrusion (ce n'est pas un SIEM).

Documentation complète : <https://forgemvc.com/docs/forge/>.
