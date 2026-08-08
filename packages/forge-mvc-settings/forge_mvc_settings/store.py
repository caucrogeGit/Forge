# pyright: strict
"""Paramètres applicatifs persistés dans MariaDB, sans logique métier.

`forge-mvc-settings` stocke des réglages d'application (nom d'établissement,
durée d'une session, mode maintenance, options pédagogiques) dans une table
`app_settings`, en paire clé/valeur typée. L'API est explicite : on lit avec
:func:`get_setting`, on écrit avec :func:`set_setting`. Le SQL reste visible
(constantes ci-dessous), aucune écriture cachée, aucune dépendance lourde.

La table n'est PAS créée automatiquement : la migration fournie par le paquet
doit avoir été appliquée (voir `forge settings:init` puis `forge
migration:apply`). Les fonctions acceptent un paramètre `db` injectable (par
défaut `core.database.db`) pour rester testables.
"""
from __future__ import annotations

import re
from typing import Any

from core.database.errors import UniqueViolationError
from forge_mvc_settings.errors import SettingsError

#: Nom de la table de paramètres.
TABLE_NAME = "app_settings"

#: Types de valeur supportés (sérialisés en texte, recoercés à la lecture).
SUPPORTED_TYPES = ("str", "int", "bool", "float")

#: Une valeur de paramètre, telle que rendue à la lecture.
SettingValue = str | int | bool | float

# Clé : commence par une lettre, puis lettres/chiffres/`_`/`.` ; 191 max
# (limite d'index utf8mb4). Le point autorise des clés hiérarchiques
# (`qcm.session_duration`), jamais d'espace ni de caractère arbitraire.
_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]{0,190}$")


_SELECT_ONE_SQL = f"SELECT setting_value, value_type FROM {TABLE_NAME} WHERE setting_key = ?"
_SELECT_ALL_SQL = f"SELECT setting_key, setting_value, value_type FROM {TABLE_NAME} ORDER BY setting_key"
_UPDATE_SQL = (
    f"UPDATE {TABLE_NAME} SET setting_value = ?, value_type = ? WHERE setting_key = ?"
)
_INSERT_SQL = (
    f"INSERT INTO {TABLE_NAME} (setting_key, setting_value, value_type) VALUES (?, ?, ?)"
)
_DELETE_SQL = f"DELETE FROM {TABLE_NAME} WHERE setting_key = ?"


def _db_module() -> Any:
    import core.database.db as db  # noqa: PLC0415

    return db


def _validate_key(key: object) -> None:
    if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
        raise SettingsError(
            f"Clé de paramètre invalide : {key!r}. Attendu : une lettre suivie de "
            "lettres, chiffres, '_' ou '.' (191 caractères au plus)."
        )


def _serialize(value: object) -> tuple[str, str]:
    # bool AVANT int : en Python, bool est un sous-type d'int.
    if isinstance(value, bool):
        return ("1" if value else "0", "bool")
    if isinstance(value, int):
        return (str(value), "int")
    if isinstance(value, float):
        return (repr(value), "float")
    if isinstance(value, str):
        return (value, "str")
    raise SettingsError(
        f"Type de valeur non supporté : {type(value).__name__}. "
        f"Types acceptés : {', '.join(SUPPORTED_TYPES)}."
    )


def _coerce(raw: Any, value_type: Any) -> SettingValue:
    text = "" if raw is None else str(raw)
    if value_type == "int":
        return int(text)
    if value_type == "float":
        return float(text)
    if value_type == "bool":
        return text == "1"
    return text


def set_setting(key: str, value: SettingValue, *, db: Any = None) -> None:
    """Crée ou met à jour le paramètre `key` avec `value` (upsert).

    Le type est déduit de `value` (`str`, `int`, `bool`, `float`). Lève
    :class:`SettingsError` si la clé est invalide ou le type non supporté.
    """
    _validate_key(key)
    serialized, value_type = _serialize(value)
    database = db if db is not None else _db_module()
    # Écrire puis insérer si rien n'a été touché (OPTIN-DML-DIALECT-001).
    # `ON DUPLICATE KEY UPDATE` était écrit en dur : mesuré, aucun des trois
    # autres backends ne l'accepte, et chacun a sa propre forme d'upsert
    # (`ON CONFLICT` ailleurs, `MERGE` en T-SQL). Ce motif en deux temps n'en
    # exige aucune et n'ajoute rien au contrat.
    #
    # La course est fermée par la contrainte d'unicité de la clé : deux
    # écrivains simultanés sur une clé absente ne peuvent pas insérer tous les
    # deux, et le perdant reprend par la mise à jour. Le doublon est reconnu
    # par le cœur (ADR-054), donc de la même façon sur les quatre backends.
    if database.execute(_UPDATE_SQL, (serialized, value_type, key)):
        return
    try:
        database.execute(_INSERT_SQL, (key, serialized, value_type))
    except UniqueViolationError:
        database.execute(_UPDATE_SQL, (serialized, value_type, key))


def get_setting(
    key: str, default: SettingValue | None = None, *, db: Any = None
) -> SettingValue | None:
    """Renvoie la valeur du paramètre `key`, recoercée selon son type stocké.

    Renvoie `default` si le paramètre n'existe pas. Lève
    :class:`SettingsError` si la clé est invalide.
    """
    _validate_key(key)
    row = (db if db is not None else _db_module()).fetch_one(_SELECT_ONE_SQL, (key,))
    if row is None:
        return default
    return _coerce(row["setting_value"], row["value_type"])


def get_all_settings(*, db: Any = None) -> dict[str, SettingValue]:
    """Renvoie tous les paramètres, recoercés, triés par clé."""
    rows = (db if db is not None else _db_module()).fetch_all(_SELECT_ALL_SQL)
    return {
        str(row["setting_key"]): _coerce(row["setting_value"], row["value_type"])
        for row in rows
    }


def delete_setting(key: str, *, db: Any = None) -> bool:
    """Supprime le paramètre `key`. Renvoie `True` s'il existait."""
    _validate_key(key)
    return (db if db is not None else _db_module()).execute(_DELETE_SQL, (key,)) > 0
