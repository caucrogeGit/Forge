-- Migration Forge Settings : table des paramètres applicatifs.
-- Source : forge-mvc-settings (SETTINGS-OPTIN-SCAFFOLD-001).
--
-- `CREATE TABLE IF NOT EXISTS` rend la migration idempotente : elle est sûre
-- même si la table existe déjà. Paire clé/valeur typée, SQL visible.
--
-- Appliquer avec : forge migration:apply

CREATE TABLE IF NOT EXISTS app_settings (
    setting_key   VARCHAR(191) NOT NULL,
    setting_value TEXT NOT NULL,
    value_type    VARCHAR(16) NOT NULL DEFAULT 'str',
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
