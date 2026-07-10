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
