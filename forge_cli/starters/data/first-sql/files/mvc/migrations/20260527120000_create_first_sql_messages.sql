-- Migration : create_first_sql_messages
-- Ticket    : STARTER-FIRST-SQL-001
-- Palier 8 de la progression pédagogique : Première base SQL.
--
-- Crée une table minimale `first_sql_messages` et y insère le
-- message de démonstration « Bonjour SQL ». L'INSERT est idempotent
-- (ne ré-insère pas si la ligne existe déjà) — sûr à rejouer si la
-- table de tracking des migrations est réinitialisée.

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO first_sql_messages (content)
SELECT 'Bonjour SQL'
WHERE NOT EXISTS (
    SELECT 1 FROM first_sql_messages WHERE content = 'Bonjour SQL'
);
