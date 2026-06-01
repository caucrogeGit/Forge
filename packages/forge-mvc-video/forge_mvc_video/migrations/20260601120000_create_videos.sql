-- Migration : create_videos
-- Ticket    : VIDEO-CONFIG-001
-- Module    : forge-mvc-video
--
-- Crée la table `videos` qui suit le cycle de vie d'une vidéo gérée par
-- l'opt-in Forge Video : upload → traitement (transcodage MP4) → lecture.
--
-- - `id` BIGINT UNSIGNED AUTO_INCREMENT, clé primaire ;
-- - `uuid` CHAR(36) NOT NULL UNIQUE — identifiant stable, sert aussi de
--   répertoire de stockage (jamais le nom de fichier utilisateur) ;
-- - chemins (`original_path`, `mp4_path`, `poster_path`) relatifs à la
--   racine de stockage `FORGE_VIDEO_STORAGE_ROOT` ;
-- - métadonnées extraites par ffprobe : `duration_seconds`, `width`,
--   `height`, `mime_type`, `size_bytes` ;
-- - `status` : uploaded | processing | ready | failed (le worker CLI
--   `video:process` fait avancer le statut, jamais une requête HTTP) ;
-- - `error_message` : raison d'un `failed`, lisible.
--
-- Le SQL reste visible et appliqué explicitement (`forge migration:apply`).
-- `CREATE TABLE IF NOT EXISTS` rend la migration idempotente.

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
