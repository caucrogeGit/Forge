-- Migration : create_relations_tables
-- Ticket    : STARTER-RELATIONS-001
-- Palier 1 du niveau avancé : Relations entre tables.
--
-- Deux tables liées par une CLÉ ÉTRANGÈRE :
--   * `categories` (id, name)
--   * `articles`   (id, title, category_id → categories.id)
-- La table parente est créée AVANT la table enfant (la contrainte FK exige
-- que `categories` existe). CREATE TABLE IF NOT EXISTS + INSERT idempotents :
-- sûrs à rejouer.

CREATE TABLE IF NOT EXISTS categories (
    id   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100)    NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS articles (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title       VARCHAR(255)    NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_articles_category
        FOREIGN KEY (category_id) REFERENCES categories (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO categories (name)
SELECT v.name FROM (
    SELECT 'Général'   AS name
    UNION ALL SELECT 'Technique'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM categories c WHERE c.name = v.name
);

INSERT INTO articles (title, category_id)
SELECT v.title, c.id FROM (
    SELECT 'Premier article'   AS title, 'Général'   AS category
    UNION ALL SELECT 'Notes techniques',        'Technique'
    UNION ALL SELECT 'Bienvenue',               'Général'
) AS v
JOIN categories c ON c.name = v.category
WHERE NOT EXISTS (
    SELECT 1 FROM articles a WHERE a.title = v.title
);
