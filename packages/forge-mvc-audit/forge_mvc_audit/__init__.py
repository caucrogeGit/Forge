# pyright: strict
"""forge-mvc-audit — journal d'audit applicatif opt-in (AUDIT-OPTIN-SCAFFOLD-001).

Brique générique : tracer les actions importantes d'une application (élève créé,
note modifiée, QCM corrigé, utilisateur connecté, rôle changé, fichier supprimé)
dans une table `audit_log`, avec une API explicite `record_audit`/`get_audit_log`.

Périmètre borné : audit applicatif, pas un SIEM de cybersécurité. Cohérent avec
ADR-008 (Forge fournit la table et le helper, la décision de tracer reste
applicative). La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
"""
from forge_mvc_audit.errors import AuditError
from forge_mvc_audit.store import (
    CREATE_TABLE_SQL,
    MAX_LIMIT,
    TABLE_NAME,
    AuditEntry,
    get_audit_log,
    record_audit,
)

__version__ = "1.0.0b17"

__all__ = [
    "AuditError",
    "AuditEntry",
    "TABLE_NAME",
    "MAX_LIMIT",
    "CREATE_TABLE_SQL",
    "record_audit",
    "get_audit_log",
]
