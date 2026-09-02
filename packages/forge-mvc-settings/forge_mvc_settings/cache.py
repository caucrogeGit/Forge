# pyright: strict
"""Cache mémoire des paramètres, à invalidation explicite (SETTINGS-CACHE-001).

Un paramètre est lu à chaque requête, parfois plusieurs fois, et change une
fois par mois. Chaque lecture faisait pourtant un aller-retour vers la base.

## Pourquoi il n'est pas activé par défaut

Un cache change ce qu'une lecture garantit. Sans lui, `get_setting` rend
toujours la valeur en base ; avec lui, il rend la dernière valeur vue, et deux
processus peuvent diverger jusqu'à l'invalidation.

Le principe 3 refuse qu'un comportement change dans le dos de l'appelant :
l'application l'active, et sait donc ce qu'elle achète.

## Pourquoi l'invalidation est explicite

Un cache à expiration ferait cohabiter deux valeurs pendant un délai que
personne n'a choisi, et le temps de propagation dépendrait du moment de
l'écriture. Ici, écrire invalide : les écritures passant par ce paquet sont
suivies, et une écriture faite ailleurs, par une migration ou à la main,
demande un `clear_settings_cache()` que l'exploitant décide.

Ce que ce cache n'est pas : un cache partagé. Il vit dans le processus, et un
déploiement à plusieurs travailleurs en a un par travailleur.
"""
from __future__ import annotations

from forge_mvc_settings.store import SettingValue

__all__ = [
    "enable_settings_cache",
    "disable_settings_cache",
    "settings_cache_enabled",
    "clear_settings_cache",
    "cached_settings",
]

_enabled = False
_values: "dict[str, SettingValue | None]" = {}


def enable_settings_cache() -> None:
    """Active le cache. Sans effet s'il l'est déjà.

    L'activation vide le cache : ce qu'il contenait d'une activation
    précédente pourrait dater d'avant des écritures faites entre temps.
    """
    global _enabled
    _values.clear()
    _enabled = True


def disable_settings_cache() -> None:
    """Désactive le cache et le vide."""
    global _enabled
    _enabled = False
    _values.clear()


def settings_cache_enabled() -> bool:
    """Vrai si le cache est actif."""
    return _enabled


def clear_settings_cache(key: "str | None" = None) -> None:
    """Vide le cache, ou seulement l'entrée `key`.

    À appeler après une écriture faite hors de ce paquet, par une migration ou
    à la main : le cache ne peut pas la voir.
    """
    if key is None:
        _values.clear()
    else:
        _values.pop(key, None)


def cached_settings() -> "dict[str, SettingValue | None]":
    """Contenu courant du cache, pour un diagnostic."""
    return dict(_values)


def cache_get(key: str) -> "tuple[bool, SettingValue | None]":
    """Valeur en cache pour `key` : `(trouvée, valeur)`.

    Rend un couple et non la valeur seule : une absence et un `None` mis en
    cache se distinguent, sans quoi un paramètre absent serait relu à chaque
    fois, ce que le cache devait justement éviter.
    """
    if not _enabled or key not in _values:
        return (False, None)
    return (True, _values[key])


def cache_put(key: str, value: "SettingValue | None") -> None:
    """Range une valeur en cache. Sans effet si le cache est inactif."""
    if _enabled:
        _values[key] = value


def cache_invalidate(key: str) -> None:
    """Retire une entrée après une écriture. Toujours actif.

    Invalide même quand le cache est éteint : il peut être rallumé, et une
    entrée d'avant survivrait à l'écriture.
    """
    _values.pop(key, None)


