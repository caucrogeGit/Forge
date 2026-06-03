-- Migration : create_iot_events
-- Ticket    : STARTER-IOT-API-001
-- Palier 2 du niveau intermédiaire (welcome-iot) : Exposer l'API IoT.
--
-- L'API HTTP JSON officielle lit la table `iot_events`. On garantit donc sa
-- présence (schéma aligné sur IOT-STORAGE-EVENTS-001). `CREATE TABLE IF NOT
-- EXISTS` rend la migration idempotente — sûre même si le palier de
-- simulation a déjà créé la table.

CREATE TABLE IF NOT EXISTS iot_events (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site          VARCHAR(64)     NOT NULL,
    device_id     VARCHAR(64)     NOT NULL,
    kind          VARCHAR(64)     NOT NULL,
    value         DOUBLE          NOT NULL,
    unit          VARCHAR(32)     NOT NULL,
    timestamp     VARCHAR(40)     NOT NULL,
    metadata_json TEXT            NULL,
    received_at   DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_iot_events_site_device (site, device_id),
    INDEX idx_iot_events_received_at (received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
