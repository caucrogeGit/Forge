-- Migration : create_videos
-- Ticket    : STARTER-VIDEO-PROBE-001
-- Palier 1 du niveau avancé (welcome-video) : Sonder une vidéo.
--
-- Garantit la table `videos` (schéma VIDEO-CONFIG-001) : la sonde lit le
-- chemin du fichier d'origine depuis cette table. `CREATE TABLE IF NOT
-- EXISTS` : idempotent.

CREATE TABLE IF NOT EXISTS videos (
    id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    uuid             CHAR(36)        NOT NULL,
    title            VARCHAR(255)    NULL,
    original_path    VARCHAR(500)    NOT NULL,
    mp4_path         VARCHAR(500)    NULL,
    poster_path      VARCHAR(500)    NULL,
    mime_type        VARCHAR(120)    NULL,
    size_bytes       BIGINT UNSIGNED NOT NULL,
    duration_seconds INT UNSIGNED    NULL,
    width            INT UNSIGNED    NULL,
    height           INT UNSIGNED    NULL,
    status           VARCHAR(30)     NOT NULL,
    error_message    TEXT            NULL,
    created_at       DATETIME(6)     NOT NULL,
    updated_at       DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_videos_uuid (uuid),
    INDEX idx_videos_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
