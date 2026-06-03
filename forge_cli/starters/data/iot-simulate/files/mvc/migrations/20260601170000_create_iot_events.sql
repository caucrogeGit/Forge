-- Migration : create_iot_events
-- Ticket    : STARTER-IOT-SIMULATE-001
-- Palier 1 du niveau intermédiaire (welcome-iot) : Simuler une mesure IoT.
--
-- Crée la table `iot_events` du module Forge IoT pour que la simulation
-- ait où écrire. Le schéma est aligné sur le contrat figé par
-- IOT-STORAGE-EVENTS-001 (colonnes site, device_id, kind, value, unit,
-- timestamp, metadata_json, received_at). `CREATE TABLE IF NOT EXISTS`
-- rend la migration idempotente.

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
