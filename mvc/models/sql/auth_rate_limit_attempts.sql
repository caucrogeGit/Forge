CREATE TABLE IF NOT EXISTS auth_rate_limit_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(120) NOT NULL,
    rate_key VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_id INT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auth_rate_limit_action_key (action, rate_key),
    INDEX idx_auth_rate_limit_created_at (created_at),
    INDEX idx_auth_rate_limit_user_id (user_id),
    CONSTRAINT fk_auth_rate_limit_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
