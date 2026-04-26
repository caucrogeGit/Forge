"""Suppression ciblée des clés étrangères déclarées par un starter applicatif."""

from __future__ import annotations

import json
from pathlib import Path

import forge_cli.output as out
from forge_cli.starters.file_ops import relations_data_path, to_snake


def drop_foreign_keys(meta: dict, root: Path) -> None:
    """
    Supprime uniquement les FK nommées dans le relations.json du starter.
    Vérifie l'existence dans information_schema avant chaque DROP.
    Ne touche pas aux autres FK du projet.
    """
    data_path = relations_data_path(meta)
    if not data_path:
        return

    from forge_cli.entities.db_apply import load_db_apply_config

    try:
        import mariadb

        relations = json.loads(data_path.read_text(encoding="utf-8")).get("relations", [])
        cfg = load_db_apply_config()
        conn = mariadb.connect(
            host=cfg.host, port=cfg.port,
            user=cfg.login, password=cfg.password,
            database=cfg.database,
        )
    except Exception:
        return

    try:
        cur = conn.cursor()
        try:
            for rel in relations:
                table = rel.get("from_entity", "")
                fk = rel.get("foreign_key_name", "")
                if not table or not fk:
                    continue
                table_name = to_snake(table)
                cur.execute(
                    """
                    SELECT CONSTRAINT_NAME
                    FROM information_schema.TABLE_CONSTRAINTS
                    WHERE CONSTRAINT_SCHEMA = ?
                      AND TABLE_NAME        = ?
                      AND CONSTRAINT_NAME   = ?
                      AND CONSTRAINT_TYPE   = 'FOREIGN KEY'
                    """,
                    (cfg.database, table_name, fk),
                )
                if cur.fetchone():
                    cur.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {fk}")
                    print(out.ok(f"Contrainte {fk} supprimée avant reconstruction."))
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
