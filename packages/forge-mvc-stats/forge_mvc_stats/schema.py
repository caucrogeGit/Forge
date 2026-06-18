# pyright: strict
"""Définition SQL générique de la table d'événements statistiques Forge."""

from __future__ import annotations

STATS_EVENTS_TABLE = "forge_stats_events"

STATS_EVENTS_COLUMNS = (
    "id",
    "name",
    "label",
    "category",
    "metadata",
    "created_at",
)

_SQL = """\
CREATE TABLE IF NOT EXISTS forge_stats_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    label VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'general',
    metadata JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_forge_stats_events_name (name),
    INDEX idx_forge_stats_events_category (category),
    INDEX idx_forge_stats_events_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"""


def get_stats_events_schema_sql() -> str:
    """Return the SQL CREATE TABLE statement for forge_stats_events."""
    return _SQL
