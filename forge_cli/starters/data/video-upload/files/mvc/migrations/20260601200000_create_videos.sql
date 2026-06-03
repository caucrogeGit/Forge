-- Migration : create_videos
-- Ticket    : STARTER-VIDEO-UPLOAD-001
-- Palier 1 du niveau intermédiaire (welcome-video) : Téléverser une vidéo.
--
-- Crée la table `videos` du module Forge Vidéo pour que l'upload ait où
-- écrire. Schéma aligné sur VIDEO-CONFIG-001 : cycle de vie
-- uploaded → processing → ready → failed. `CREATE TABLE IF NOT EXISTS`
-- rend la migration idempotente.

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
