-- Migration Forge Notifications : table des notifications in-app.
-- Source : forge-mvc-notifications (NOTIFICATIONS-OPTIN-SCAFFOLD-001).
--
-- `CREATE TABLE IF NOT EXISTS` rend la migration idempotente. SQL visible.
-- Index (recipient, read_at) pour le décompte des non lues et le filtrage.
--
-- Appliquer avec : forge migration:apply

CREATE TABLE IF NOT EXISTS notifications (
    id          INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    recipient   VARCHAR(191) NOT NULL,
    type        VARCHAR(64) NOT NULL DEFAULT 'info',
    message     TEXT NOT NULL,
    data        TEXT NOT NULL,
    read_at     DATETIME NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_notif_recipient (recipient, read_at),
    KEY idx_notif_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
