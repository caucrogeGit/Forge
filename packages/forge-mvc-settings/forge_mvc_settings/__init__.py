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
from forge_mvc_settings.admin_view import (
    FALSE_INPUTS,
    TRUE_INPUTS,
    SettingRow,
    describe_settings,
    parse_setting_value,
)
from forge_mvc_settings.store import (
    get_settings_with_types,
    SUPPORTED_TYPES,
    TABLE_NAME,
    delete_setting,
    get_all_settings,
    get_setting,
    set_setting,
)

__version__ = "1.0.0rc7"

__all__ = [
    # Édition depuis un écran (ADMIN-SETTINGS-UI-001)
    "parse_setting_value",
    "get_settings_with_types",
    "describe_settings",
    "SettingRow",
    "TRUE_INPUTS",
    "FALSE_INPUTS",
    "SettingsError",
    "TABLE_NAME",
    "SUPPORTED_TYPES",
    "get_setting",
    "set_setting",
    "get_all_settings",
    "delete_setting",
]
