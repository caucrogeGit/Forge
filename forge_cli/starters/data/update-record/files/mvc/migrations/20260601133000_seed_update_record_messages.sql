-- Migration : seed_update_record_messages
-- Ticket    : STARTER-UPDATE-RECORD-001
-- Palier 5 du niveau intermédiaire : Modifier un enregistrement.
--
-- Réutilise la table neutre `first_sql_messages` et y insère quelques lignes
-- à éditer. Idempotent (sûr à rejouer).

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT v.content FROM (
    SELECT 'À modifier' AS content
    UNION ALL SELECT 'Encore un message'
    UNION ALL SELECT 'Troisième ligne'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages m WHERE m.content = v.content
);
