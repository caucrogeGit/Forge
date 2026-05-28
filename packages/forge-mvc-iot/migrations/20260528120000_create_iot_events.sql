-- Migration : create_iot_events
-- Ticket    : IOT-STORAGE-MIGRATION-001
-- Module    : forge-mvc-iot
--
-- Crée la table `iot_events` qui stocke les mesures reçues par le
-- subscriber MQTT Forge IoT. Le schéma est aligné sur le contrat figé
-- par IOT-STORAGE-EVENTS-001 (docs/iot/storage-events.md) :
--
-- - colonnes dans l'ordre canonique défini par
--   `forge_mvc_iot.storage.events.COLUMNS`
--   (site, device_id, kind, value, unit, timestamp, metadata_json,
--    received_at) ;
-- - `id` BIGINT UNSIGNED AUTO_INCREMENT, clé primaire ;
-- - `timestamp` conservé en VARCHAR(40) — chaîne ISO 8601 UTC du
--   payload, suffixe Z obligatoire ;
-- - `metadata_json` TEXT NULL — JSON sérialisé ou NULL si absent ;
-- - `received_at` DATETIME(6) NOT NULL — horodatage serveur, UTC.
--
-- Deux index minimaux : couple (site, device_id) pour filtrer par
-- capteur, received_at pour les fenêtres temporelles.
--
-- `CREATE TABLE IF NOT EXISTS` rend la migration idempotente :
-- rejouée, elle ne lève pas d'erreur si la table existe déjà.

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
