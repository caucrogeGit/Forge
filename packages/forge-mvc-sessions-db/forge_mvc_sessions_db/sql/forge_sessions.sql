-- DDL Forge Sessions : table du store de session persistant.
-- Source : forge-mvc-sessions-db (retour terrain 016, F34/F36/F37).
--
-- `forge sessions:init` écrit ce fichier dans mvc/models/sql/ ; `forge db:apply`
-- l'applique. `CREATE TABLE IF NOT EXISTS` rend l'opération idempotente.
--
-- Horodatages : Python est l'unique autorité (UTC). Pas de DEFAULT
-- CURRENT_TIMESTAMP ni ON UPDATE (pas de double horloge SGBD/Python, F37).
-- La colonne `version` sert la concurrence optimiste du store (garde
-- WHERE version = ?, F36).
--
-- DDL MariaDB. Adaptez les types au backend actif si nécessaire (par exemple
-- TEXT au lieu de LONGTEXT, et un CREATE INDEX séparé sur SQLite ou PostgreSQL).

CREATE TABLE IF NOT EXISTS forge_sessions (
    session_id CHAR(64)  NOT NULL,
    data       LONGTEXT  NOT NULL,
    expire_at  DATETIME  NOT NULL,
    version    INT       NOT NULL DEFAULT 0,
    created_at DATETIME  NOT NULL,
    updated_at DATETIME  NOT NULL,
    PRIMARY KEY (session_id),
    INDEX idx_forge_sessions_expire_at (expire_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
