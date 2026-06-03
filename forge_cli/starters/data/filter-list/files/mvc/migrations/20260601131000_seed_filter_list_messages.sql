-- Migration : seed_filter_list_messages
-- Ticket    : STARTER-FILTER-LIST-001
-- Palier 2 du niveau intermédiaire : Rechercher / filtrer une liste.
--
-- Réutilise la table neutre `first_sql_messages` et y insère quelques lignes
-- variées pour que la recherche soit parlante. Idempotent (sûr à rejouer).

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT v.content FROM (
    SELECT 'Bonjour SQL'         AS content
    UNION ALL SELECT 'Bonjour Forge'
    UNION ALL SELECT 'Message de test'
    UNION ALL SELECT 'Autre message'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages m WHERE m.content = v.content
);
