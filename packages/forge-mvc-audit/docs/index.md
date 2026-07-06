# Forge Audit

`forge-mvc-audit` est l'opt-in de journal d'audit applicatif de Forge.

Il enregistre les actions importantes de l'application (élève créé, note modifiée, QCM corrigé, connexion, rôle changé, fichier supprimé) dans une table `audit_log`, avec une API explicite.

## Périmètre borné

C'est un audit applicatif, pas un SIEM de cybersécurité.
Cohérent avec ADR-008 : Forge fournit la table et le helper, la décision de tracer reste applicative.
Le cœur de Forge ignore tout des traces ; la dépendance va de l'opt-in vers le cœur, jamais l'inverse.

## Mise en route

```bash
pip install --pre forge-mvc-audit
forge audit:init        # copie la migration dans mvc/migrations/
forge migration:apply   # crée la table audit_log
```

## Premier usage

```python
from forge_mvc_audit import record_audit, get_audit_log

record_audit("eleve.cree", actor="prof.dupont", target_type="eleve", target_id=42)

for entree in get_audit_log(limit=20):
    print(entree.created_at, entree.action, entree.actor)
```

## Pour aller plus loin

- [Le journal d'audit](references/store.md) : `record_audit`, `get_audit_log`, `AuditEntry`.
- [L'initialisation](references/cli.md) : `forge audit:init`.
- [Les erreurs](references/errors.md) : `AuditError`.
