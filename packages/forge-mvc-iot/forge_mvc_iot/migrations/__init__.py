"""Migrations SQL Forge IoT — ressources du package.

Ce sous-package héberge les fichiers de migration SQL versionnés du
module ``forge-mvc-iot``. Ce sont des **ressources** (fichiers ``.sql``),
embarquées dans la distribution PyPI via
``[tool.setuptools.package-data]`` dans ``pyproject.toml``.

Pour les lire depuis du code Python (par exemple pour une future
commande ``forge iot:init``) :

    from importlib import resources

    migration = (
        resources.files("forge_mvc_iot")
        / "migrations"
        / "20260528120000_create_iot_events.sql"
    )
    content = migration.read_text(encoding="utf-8")
"""

from __future__ import annotations

__all__: list[str] = []
