-- Migration Forge Images : table de la couche médias applicative.
-- Source : forge-mvc-images (OPTIN-IMAGES-INIT-001).
--
-- `CREATE TABLE IF NOT EXISTS` rend la migration idempotente : elle est sûre
-- même si la table existe déjà. Elle sert la couche médias applicative
-- (attach_media_to_entity, get_media_gallery, get_cover_media) ; la couche
-- traitement (save_image_upload, verify_image_content, variantes) n'en dépend pas.
--
-- Appliquer avec : forge migration:apply

CREATE TABLE IF NOT EXISTS media (
    Id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    EntityName   VARCHAR(100)    NOT NULL,
    EntityId     INT             NOT NULL,
    Path         VARCHAR(500)    NOT NULL,
    OriginalName VARCHAR(255)    NOT NULL,
    MimeType     VARCHAR(120)    NOT NULL,
    Size         INT             NOT NULL,
    Role         VARCHAR(50)     NOT NULL DEFAULT 'default',
    Position     INT             NOT NULL DEFAULT 0,
    AltText      VARCHAR(255)    NULL,
    CreatedAt    DATETIME        NOT NULL,
    PRIMARY KEY (Id),
    INDEX idx_media_entity (EntityName, EntityId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
