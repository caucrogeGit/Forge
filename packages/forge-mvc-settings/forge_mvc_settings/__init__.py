# pyright: strict
"""forge-mvc-settings — paramètres applicatifs opt-in (SETTINGS-OPTIN-SCAFFOLD-001).

Brique générique : persister des réglages d'application en paire clé/valeur
typée dans une table MariaDB (`app_settings`), avec une API explicite
`get_setting`/`set_setting`. Le cœur de Forge ignore tout des paramètres ; ce
paquet fournit l'API ; l'application décide de ce qu'elle stocke (nom
d'établissement, durée d'une session, mode maintenance, options pédagogiques).

La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
"""
from forge_mvc_settings.errors import SettingsError
from forge_mvc_settings.store import (
    CREATE_TABLE_SQL,
    SUPPORTED_TYPES,
    TABLE_NAME,
    delete_setting,
    get_all_settings,
    get_setting,
    set_setting,
)

__version__ = "1.0.0rc2"

__all__ = [
    "SettingsError",
    "TABLE_NAME",
    "SUPPORTED_TYPES",
    "CREATE_TABLE_SQL",
    "get_setting",
    "set_setting",
    "get_all_settings",
    "delete_setting",
]
