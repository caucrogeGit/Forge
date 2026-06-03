-- Migration : seed_json_api_messages
-- Ticket    : STARTER-JSON-API-001
-- Palier 4 du niveau avancé : API JSON protégée.
--
-- Réutilise la table neutre `first_sql_messages` et garantit quelques lignes
-- pour que l'API renvoie des données. CREATE TABLE IF NOT EXISTS + INSERT
-- idempotents : sûrs à rejouer.

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT v.content FROM (
    SELECT 'Message exposé via l''API' AS content
    UNION ALL SELECT 'Deuxième message'
    UNION ALL SELECT 'Troisième message'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages m WHERE m.content = v.content
);
