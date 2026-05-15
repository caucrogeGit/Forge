CREATE TABLE IF NOT EXISTS mail_log (
    id             INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    message_type   VARCHAR(100) NOT NULL DEFAULT '',
    to_email       VARCHAR(255) NOT NULL DEFAULT '',
    subject        VARCHAR(500) NOT NULL DEFAULT '',
    transport      VARCHAR(50)  NOT NULL DEFAULT '',
    status         ENUM('sent', 'failed', 'skipped') NOT NULL,
    error_message  TEXT,
    related_entity VARCHAR(100),
    related_id     INT,
    created_at     DATETIME     NOT NULL,
    sent_at        DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
