-- Migration : seed_list_records_messages
-- Ticket    : STARTER-LIST-RECORDS-001
-- Palier 1 du niveau intermédiaire : Lister des enregistrements.
--
-- Réutilise la table neutre `first_sql_messages` (palier débutant Première
-- base SQL) et y insère PLUSIEURS lignes pour que la liste soit parlante.
-- CREATE TABLE IF NOT EXISTS + INSERT idempotents : sûrs à rejouer.

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT v.content FROM (
    SELECT 'Bonjour SQL'        AS content
    UNION ALL SELECT 'Deuxième message'
    UNION ALL SELECT 'Troisième message'
    UNION ALL SELECT 'Quatrième message'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages m WHERE m.content = v.content
);
