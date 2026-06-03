-- Migration : create_db_transaction_table
-- Ticket    : STARTER-DB-TRANSACTION-001
-- Dernier palier du niveau avancé : Écritures transactionnelles.
--
-- Garantit la table neutre `first_sql_messages`. Pas de seed : la liste se
-- remplit au fur et à mesure des insertions transactionnelles.
-- CREATE TABLE IF NOT EXISTS : sûr à rejouer.

CREATE TABLE IF NOT EXISTS first_sql_messages (
    id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    content VARCHAR(255)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
