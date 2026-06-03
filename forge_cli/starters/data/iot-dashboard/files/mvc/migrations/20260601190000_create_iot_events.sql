-- Migration : create_iot_events
-- Ticket    : STARTER-IOT-DASHBOARD-001
-- Palier 3 du niveau intermédiaire (welcome-iot) : Tableau de bord IoT.
--
-- Garantit la table `iot_events` (schéma aligné sur IOT-STORAGE-EVENTS-001)
-- pour que le tableau de bord ait des données à lire. `CREATE TABLE IF NOT
-- EXISTS` : idempotent, sûr même si un autre palier l'a déjà créée.

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
