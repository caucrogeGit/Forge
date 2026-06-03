-- Migration : seed_delete_record_messages
-- Ticket    : STARTER-DELETE-RECORD-001
-- Palier 6 du niveau intermédiaire : Supprimer un enregistrement.
--
-- Réutilise la table neutre `first_sql_messages` et y insère quelques lignes
-- à supprimer. Idempotent (sûr à rejouer).

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT v.content FROM (
    SELECT 'À supprimer' AS content
    UNION ALL SELECT 'Message temporaire'
    UNION ALL SELECT 'Ligne de trop'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages m WHERE m.content = v.content
);
