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

from core.database.timestamps import utc_now
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
#: `updated_at` est écrit par Python, jamais laissé au moteur (ADR-081).
#:
#: Mesuré avant correctif, sur les trois serveurs : la colonne ne suivait la
#: modification que sur MariaDB, grâce à son `ON UPDATE` déclaratif, et restait
#: FIGÉE sur la date de création sur PostgreSQL et SQL Server, qui n'en ont pas
#: (`SETTINGS-UPDATED-AT-001`). Un paramètre modifié y annonçait donc, à jamais,
#: la date à laquelle il avait été créé.
#:
#: MariaDB refuse par ailleurs `ON UPDATE UTC_TIMESTAMP()` : le tenir aurait mis
#: le défaut en UTC et la mise à jour en heure locale, deux référentiels dans
#: une seule colonne. Python tranche les deux problèmes d'un coup.
_UPDATE_SQL = (
    f"UPDATE {TABLE_NAME} SET setting_value = ?, value_type = ?, updated_at = ? "
    "WHERE setting_key = ?"
)
_INSERT_SQL = (
    f"INSERT INTO {TABLE_NAME} (setting_key, setting_value, value_type, updated_at) "
    "VALUES (?, ?, ?, ?)"
)
_DELETE_SQL = f"DELETE FROM {TABLE_NAME} WHERE setting_key = ?"


def _db_module() -> Any:
    import core.database.db as db  # noqa: PLC0415

    return db


#: Préfixe réservé aux paramètres d'un utilisateur.
#:
#: Réservé, et non seulement conventionnel : sans cela, une clé globale
#: `user.42.theme` et le paramètre de l'utilisateur 42 désigneraient la même
#: ligne, et l'un écraserait l'autre en silence (`SETTINGS-PER-USER-001`).
USER_SCOPE_PREFIX = "user."


def _validate_key(key: object, *, allow_user_scope: bool = False) -> None:
    if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
        raise SettingsError(
            f"Clé de paramètre invalide : {key!r}. Attendu : une lettre suivie de "
            "lettres, chiffres, '_' ou '.' (191 caractères au plus)."
        )
    if not allow_user_scope and key.startswith(USER_SCOPE_PREFIX):
        raise SettingsError(
            f"Clé réservée : {key!r} commence par « {USER_SCOPE_PREFIX} », "
            "espace des paramètres par utilisateur. Employez "
            "set_user_setting(utilisateur, clé) pour ceux là."
        )


def user_setting_key(user_id: object, key: str) -> str:
    """Compose la clé d'un paramètre appartenant à un utilisateur.

    L'identifiant est rendu en texte et intercalé : `user.42.theme`. Il ne peut
    pas contenir de point, sans quoi deux utilisateurs pourraient viser la même
    clé, l'un se glissant dans l'espace de l'autre.

    Raises:
        SettingsError: identifiant vide, contenant un point, ou clé composée
            dépassant la longueur permise. Un identifiant long réduit l'espace
            restant, et une clé tronquée en silence viserait une autre ligne.
    """
    identifiant = "" if user_id is None else str(user_id).strip()
    if not identifiant:
        raise SettingsError("L'identifiant d'utilisateur ne peut pas être vide.")
    if "." in identifiant:
        raise SettingsError(
            f"Identifiant d'utilisateur invalide : {identifiant!r}. Le point est "
            "le séparateur d'espace de noms, il ne peut pas y figurer."
        )
    _validate_key(key)
    composee = f"{USER_SCOPE_PREFIX}{identifiant}.{key}"
    _validate_key(composee, allow_user_scope=True)
    return composee


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


def set_user_setting(
    user_id: object, key: str, value: SettingValue, *, db: Any = None
) -> None:
    """Écrit un paramètre appartenant à `user_id`."""
    _set_setting_raw(user_setting_key(user_id, key), value, db=db)


def get_user_setting(
    user_id: object, key: str, default: SettingValue | None = None, *, db: Any = None
) -> "SettingValue | None":
    """Lit un paramètre de `user_id`, ou `default`.

    Ne retombe **pas** sur le paramètre global de même nom : un réglage
    personnel absent et un réglage personnel identique au défaut de
    l'application ne se distinguent alors plus, et l'appelant ne peut plus dire
    lequel il lit. Le repli, s'il le veut, est une ligne de son code.
    """
    return get_setting(user_setting_key(user_id, key), default, db=db)


def delete_user_setting(user_id: object, key: str, *, db: Any = None) -> bool:
    """Supprime un paramètre de `user_id`. Vrai s'il existait."""
    return delete_setting(user_setting_key(user_id, key), db=db)


def get_user_settings(user_id: object, *, db: Any = None) -> "dict[str, SettingValue]":
    """Paramètres de `user_id`, clés **sans** le préfixe d'espace de noms.

    L'appelant a demandé les réglages d'un utilisateur : les lui rendre
    préfixés l'obligerait à retirer lui même ce qu'il vient de fournir.
    """
    prefixe = f"{USER_SCOPE_PREFIX}{str(user_id).strip()}."
    return {
        cle[len(prefixe):]: valeur
        for cle, valeur in _all_settings_raw(db=db).items()
        if cle.startswith(prefixe)
    }


def set_setting(key: str, value: SettingValue, *, db: Any = None) -> None:
    """Crée ou met à jour le paramètre `key` avec `value` (upsert).

    Le type est déduit de `value` (`str`, `int`, `bool`, `float`). Lève
    :class:`SettingsError` si la clé est invalide ou le type non supporté.
    """
    _validate_key(key)
    _set_setting_raw(key, value, db=db)


def _set_setting_raw(key: str, value: SettingValue, *, db: Any = None) -> None:
    """Écriture sans contrôle d'espace de noms, partagée par les deux portes.

    `set_setting` refuse le préfixe réservé, `set_user_setting` le compose :
    revalider ici ferait refuser ce que la seconde vient d'écrire.
    """
    from forge_mvc_settings.cache import cache_invalidate

    cache_invalidate(key)
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
    maintenant = utc_now()
    if database.execute(_UPDATE_SQL, (serialized, value_type, maintenant, key)):
        return
    try:
        database.execute(_INSERT_SQL, (key, serialized, value_type, maintenant))
    except UniqueViolationError:
        database.execute(_UPDATE_SQL, (serialized, value_type, maintenant, key))


def get_setting(
    key: str, default: SettingValue | None = None, *, db: Any = None
) -> SettingValue | None:
    """Renvoie la valeur du paramètre `key`, recoercée selon son type stocké.

    Renvoie `default` si le paramètre n'existe pas. Lève
    :class:`SettingsError` si la clé est invalide.
    """
    _validate_key(key, allow_user_scope=True)
    from forge_mvc_settings.cache import cache_get, cache_put

    trouve, en_cache = cache_get(key)
    if trouve:
        return default if en_cache is None else en_cache

    row = (db if db is not None else _db_module()).fetch_one(_SELECT_ONE_SQL, (key,))
    valeur = None if row is None else _coerce(row["setting_value"], row["value_type"])
    cache_put(key, valeur)
    return default if valeur is None else valeur


def get_all_settings(*, db: Any = None) -> dict[str, SettingValue]:
    """Renvoie les paramètres **globaux**, recoercés, triés par clé.

    Les paramètres appartenant à un utilisateur en sont exclus : les mêler
    ferait grossir la configuration de l'application au rythme de ses comptes,
    et un écran de réglages afficherait les préférences de tout le monde.
    Employer `get_user_settings` pour ceux d'un utilisateur.
    """
    return {
        cle: valeur
        for cle, valeur in _all_settings_raw(db=db).items()
        if not cle.startswith(USER_SCOPE_PREFIX)
    }


def _all_settings_raw(*, db: Any = None) -> dict[str, SettingValue]:
    """Tous les paramètres, espace utilisateur compris."""
    rows = (db if db is not None else _db_module()).fetch_all(_SELECT_ALL_SQL)
    return {
        str(row["setting_key"]): _coerce(row["setting_value"], row["value_type"])
        for row in rows
    }


def get_settings_with_types(
    *, db: Any = None
) -> "list[tuple[str, SettingValue, str]]":
    """Paramètres **globaux**, avec leur valeur typée et leur type déclaré.

    `get_all_settings` perd le type, qu'un écran d'édition doit pourtant
    afficher et renvoyer : sans lui, une page réécrirait le paramètre en
    devinant, et changerait son type au passage (`ADMIN-SETTINGS-UI-001`).

    Comme `get_all_settings`, l'espace des paramètres par utilisateur en est
    exclu (`SETTINGS-ADMIN-USER-SCOPE-LEAK-001`). Il ne l'était pas, et cette
    fonction est celle que sert `describe_settings`, donc l'écran de réglages :
    la page affichait les préférences de tous les comptes, adresses comprises,
    et les offrait à l'édition. `get_all_settings` refusait déjà cela en
    nommant le danger ; la garde manquait sur la porte que l'écran emprunte.

    Le refus d'écriture, lui, tenait : `set_setting` rejette le préfixe
    réservé. Seule la lecture fuyait.

    Employer `get_user_settings` pour les paramètres d'un utilisateur.

    L'ordre est celui de la requête, trié par clé.
    """
    database = db if db is not None else _db_module()
    return [
        (
            str(ligne["setting_key"]),
            _coerce(ligne["setting_value"], ligne["value_type"]),
            str(ligne["value_type"]),
        )
        for ligne in database.fetch_all(_SELECT_ALL_SQL, ())
        if not str(ligne["setting_key"]).startswith(USER_SCOPE_PREFIX)
    ]


def delete_setting(key: str, *, db: Any = None) -> bool:
    """Supprime le paramètre `key`. Renvoie `True` s'il existait."""
    _validate_key(key, allow_user_scope=True)
    from forge_mvc_settings.cache import cache_invalidate

    cache_invalidate(key)
    return (db if db is not None else _db_module()).execute(_DELETE_SQL, (key,)) > 0
