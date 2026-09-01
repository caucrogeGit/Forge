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
from forge_mvc_audit.export import (
    AUDIT_EXPORT_COLUMNS,
    DEFAULT_BATCH_SIZE,
    entry_to_row,
    iter_audit_rows,
)
from forge_mvc_audit.store import (
    MAX_LIMIT,
    TABLE_NAME,
    AuditEntry,
    count_audit_before,
    cutoff_for_days,
    get_audit_log,
    purge_audit_before,
    record_audit,
    record_request_audit,
)

__version__ = "1.0.0rc7"

__all__ = [
    # Export du journal (AUDIT-CSV-EXPORT-001)
    "record_request_audit",
    "iter_audit_rows",
    "entry_to_row",
    "AUDIT_EXPORT_COLUMNS",
    "DEFAULT_BATCH_SIZE",
    "AuditError",
    "AuditEntry",
    "TABLE_NAME",
    "MAX_LIMIT",
    "record_audit",
    "get_audit_log",
    # Rétention (AUDIT-RETENTION-001)
    "cutoff_for_days",
    "count_audit_before",
    "purge_audit_before",
]
