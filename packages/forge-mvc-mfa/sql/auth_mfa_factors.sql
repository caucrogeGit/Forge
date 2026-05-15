CREATE TABLE IF NOT EXISTS auth_mfa_factors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    factor_type VARCHAR(40) NOT NULL,
    totp_secret VARCHAR(255) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    label VARCHAR(120) NULL,
    confirmed_at DATETIME NULL,
    last_used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_auth_mfa_factors_user_id (user_id),
    INDEX idx_auth_mfa_factors_user_status (user_id, status),
    CONSTRAINT fk_auth_mfa_factors_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
