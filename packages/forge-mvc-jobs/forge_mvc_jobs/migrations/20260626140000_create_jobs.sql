-- Migration Forge Jobs : table de file de tâches de fond.
-- Source : forge-mvc-jobs (JOBS-OPTIN-SCAFFOLD-001).
--
-- `CREATE TABLE IF NOT EXISTS` rend la migration idempotente. La file est une
-- simple table (SQL visible), réservée atomiquement par UPDATE ... LIMIT 1.
-- Index (queue, status, available_at) pour une réservation efficace.
--
-- Appliquer avec : forge migration:apply

CREATE TABLE IF NOT EXISTS jobs (
    id           INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    queue        VARCHAR(191) NOT NULL DEFAULT 'default',
    task         VARCHAR(191) NOT NULL,
    payload      TEXT NOT NULL,
    status       VARCHAR(16) NOT NULL DEFAULT 'pending',
    attempts     INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 1,
    available_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_error   TEXT NULL,
    claim_token  VARCHAR(64) NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at   DATETIME NULL,
    finished_at  DATETIME NULL,
    KEY idx_jobs_claim (queue, status, available_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
