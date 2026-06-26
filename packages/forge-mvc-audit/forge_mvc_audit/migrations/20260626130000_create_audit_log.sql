-- Migration Forge Audit : table du journal d'audit applicatif.
-- Source : forge-mvc-audit (AUDIT-OPTIN-SCAFFOLD-001).
--
-- `CREATE TABLE IF NOT EXISTS` rend la migration idempotente. Audit applicatif
-- borné (pas un SIEM), SQL visible. Index sur action, cible et date pour des
-- lectures filtrées efficaces.
--
-- Appliquer avec : forge migration:apply

CREATE TABLE IF NOT EXISTS audit_log (
    id          INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    actor       VARCHAR(191) NULL,
    action      VARCHAR(191) NOT NULL,
    target_type VARCHAR(191) NULL,
    target_id   VARCHAR(191) NULL,
    details     TEXT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_audit_action (action),
    KEY idx_audit_target (target_type, target_id),
    KEY idx_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
