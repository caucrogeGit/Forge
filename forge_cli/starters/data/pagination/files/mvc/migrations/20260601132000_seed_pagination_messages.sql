-- Migration : seed_pagination_messages
-- Ticket    : STARTER-PAGINATION-001
-- Palier 3 du niveau intermédiaire : Paginer une liste.
--
-- Réutilise la table neutre `first_sql_messages` et y insère assez de lignes
-- (7) pour que la pagination (PAGE_SIZE = 3) montre plusieurs pages.
-- Idempotent (sûr à rejouer).

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT v.content FROM (
    SELECT 'Message 1' AS content
    UNION ALL SELECT 'Message 2'
    UNION ALL SELECT 'Message 3'
    UNION ALL SELECT 'Message 4'
    UNION ALL SELECT 'Message 5'
    UNION ALL SELECT 'Message 6'
    UNION ALL SELECT 'Message 7'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages m WHERE m.content = v.content
);
