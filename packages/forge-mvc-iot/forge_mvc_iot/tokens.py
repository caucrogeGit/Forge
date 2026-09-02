# pyright: strict
"""Jetons d'accès par site ou par équipement (`IOT-DEVICE-AUTH-001`).

L'API de lecture était protégée par **un** jeton, `FORGE_IOT_API_TOKEN`, qui
donnait accès à toutes les mesures de tous les sites.

C'est le défaut que ce module corrige. Un prestataire chargé des capteurs d'un
bâtiment recevait ce jeton, et lisait par là les mesures des autres bâtiments,
sans qu'aucun mécanisme ne l'en empêche ni ne le signale.

## Trois portées, de la plus large à la plus étroite

| Portée | Ce qu'elle ouvre |
|---|---|
| globale | toutes les mesures, tous les sites |
| site | toutes les mesures d'un site |
| équipement | les mesures d'un seul équipement d'un site |

Le jeton d'environnement garde la portée globale : le retirer casserait les
déploiements existants, et la charte demande de ne pas rompre une API publique
hors release majeure. La documentation dit ce qu'il ouvre, et pourquoi un jeton
de site vaut mieux.

## Pourquoi un simple SHA-256, sans sel ni étirement

Un jeton est **engendré par Forge** avec 256 bits d'entropie, contrairement à
un mot de passe choisi par un humain. Il n'existe donc ni dictionnaire ni table
arc-en-ciel à opposer, et l'étirement de clé, qui sert à ralentir une attaque
par force brute sur un secret faible, ne protégerait de rien ici tout en
coûtant un calcul à chaque requête.

C'est la pratique établie pour les jetons d'API, et elle est différente de
celle des mots de passe pour cette raison précise.

Le jeton n'est **jamais** stocké en clair, et n'est affiché qu'une fois, à sa
création.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

__all__ = [
    "IotTokenError",
    "IotScope",
    "GLOBAL_SCOPE",
    "TOKEN_BYTES",
    "TOKEN_PREFIX",
    "generate_token",
    "hash_token",
    "looks_like_token",
    "IotTokenRepository",
]

#: Entropie d'un jeton engendré. 32 octets, rendus en 64 caractères hexadécimaux.
TOKEN_BYTES = 32

#: Préfixe reconnaissable, pour qu'un jeton trouvé dans un journal ou un fichier
#: de configuration se laisse identifier et révoquer sans deviner ce qu'il est.
TOKEN_PREFIX = "forge_iot_"

_TOKEN_RE = re.compile(rf"^{re.escape(TOKEN_PREFIX)}[0-9a-f]{{{TOKEN_BYTES * 2}}}$")

#: Un identifiant de site ou d'équipement tel que la table les accepte.
_NAME_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


class IotTokenError(ValueError):
    """Jeton ou portée invalides."""


@dataclass(frozen=True)
class IotScope:
    """Ce qu'un porteur de jeton a le droit de lire.

    `site` à `None` désigne la portée globale ; `device_id` à `None` désigne
    tout un site. Les deux ne peuvent pas être renversés : un équipement sans
    site ne désigne rien, puisque deux sites peuvent nommer leur capteur
    pareillement.
    """

    site: "str | None" = None
    device_id: "str | None" = None
    label: "str | None" = None

    def __post_init__(self) -> None:
        if self.site is None and self.device_id is not None:
            raise IotTokenError(
                "un équipement sans site ne désigne rien : deux sites peuvent "
                "nommer leur capteur de la même façon."
            )

    @property
    def is_global(self) -> bool:
        return self.site is None

    @property
    def is_device(self) -> bool:
        return self.device_id is not None

    def allows(self, site: "str | None", device_id: "str | None" = None) -> bool:
        """Vrai si cette portée autorise la lecture visée.

        Une portée d'équipement refuse une requête qui ne nomme pas
        d'équipement : « toutes les mesures du site » n'est pas une réponse
        acceptable à qui n'a droit qu'à un capteur.
        """
        if self.is_global:
            return True
        if site is None or site != self.site:
            return False
        if self.device_id is None:
            return True
        return device_id == self.device_id

    def describe(self) -> str:
        """Portée en clair, pour un journal ou un message d'erreur."""
        if self.is_global:
            return "globale (tous les sites)"
        if self.device_id is None:
            return f"site {self.site!r}"
        return f"équipement {self.device_id!r} du site {self.site!r}"


#: Portée du jeton d'environnement historique.
GLOBAL_SCOPE = IotScope()


def generate_token() -> str:
    """Engendre un jeton. À afficher une fois, jamais à stocker en clair."""
    return TOKEN_PREFIX + secrets.token_hex(TOKEN_BYTES)


def hash_token(raw: str) -> str:
    """Empreinte SHA-256 hexadécimale du jeton.

    C'est cette empreinte qui est stockée et recherchée. Le jeton étant
    engendré avec 256 bits d'entropie, ni sel ni étirement n'apportent ici de
    protection, et le module explique pourquoi en tête.
    """
    valeur = (raw or "").strip()
    if not valeur:
        raise IotTokenError("jeton vide")
    return hashlib.sha256(valeur.encode("utf-8")).hexdigest()


def looks_like_token(raw: str) -> bool:
    """Vrai si la chaîne a la forme d'un jeton engendré par Forge.

    Sert à écarter tôt une valeur qui n'en est manifestement pas un, sans
    interroger la base. Ne dit **rien** de sa validité : un jeton révoqué ou
    inventé de la bonne forme passe ce contrôle.
    """
    return bool(_TOKEN_RE.fullmatch((raw or "").strip()))


def _nom(valeur: object, quoi: str) -> str:
    texte = str(valeur or "").strip()
    if not _NAME_RE.fullmatch(texte):
        raise IotTokenError(
            f"{quoi} invalide : {texte!r}. Attendu 1 à 64 caractères parmi "
            "lettres, chiffres, point, deux-points, tiret et souligné."
        )
    return texte


class _DbAdapter(Protocol):
    def insert(self, sql: str, params: "tuple[Any, ...]") -> int: ...
    def execute(self, sql: str, params: "tuple[Any, ...]") -> Any: ...
    def fetch_one(
        self, sql: str, params: "tuple[Any, ...]"
    ) -> "dict[str, Any] | None": ...
    def fetch_all(
        self, sql: str, params: "tuple[Any, ...]"
    ) -> "list[dict[str, Any]]": ...


_TABLE = "iot_api_tokens"

_INSERT_SQL = (
    f"INSERT INTO {_TABLE} (token_hash, site, device_id, label, created_at) "
    "VALUES (?, ?, ?, ?, ?)"
)
_SELECT_BY_HASH_SQL = (
    f"SELECT id, token_hash, site, device_id, label, created_at, revoked_at "
    f"FROM {_TABLE} WHERE token_hash = ?"
)
_SELECT_ALL_SQL = (
    f"SELECT id, site, device_id, label, created_at, revoked_at "
    f"FROM {_TABLE} ORDER BY id"
)
_REVOKE_SQL = f"UPDATE {_TABLE} SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL"


class IotTokenRepository:
    """Accès à la table des jetons. Le SQL reste visible (principe 5)."""

    def __init__(self, db_adapter: "_DbAdapter | None" = None) -> None:
        self._db = db_adapter if db_adapter is not None else _default_adapter()

    def create(
        self,
        *,
        site: "str | None" = None,
        device_id: "str | None" = None,
        label: "str | None" = None,
        now: "datetime | None" = None,
    ) -> "tuple[str, int]":
        """Crée un jeton. Rend le jeton **en clair** et son identifiant.

        C'est la seule fois où le jeton en clair existe : il n'est pas stocké,
        et ne pourra pas être retrouvé. Le perdre oblige à en créer un autre.
        """
        portee = IotScope(
            site=_nom(site, "site") if site is not None else None,
            device_id=_nom(device_id, "équipement") if device_id is not None else None,
            label=(label or "").strip() or None,
        )
        brut = generate_token()
        identifiant = self._db.insert(
            _INSERT_SQL,
            (
                hash_token(brut),
                portee.site,
                portee.device_id,
                portee.label,
                now or datetime.now(UTC).replace(tzinfo=None),
            ),
        )
        return brut, identifiant

    def resolve(self, raw: str) -> "IotScope | None":
        """Portée du jeton présenté, ou `None` s'il n'ouvre rien.

        Rend `None` aussi bien pour un jeton inconnu que pour un jeton révoqué :
        l'appelant n'a pas à distinguer les deux, et un message qui le ferait
        renseignerait un attaquant sur l'existence d'un jeton.
        """
        if not looks_like_token(raw):
            return None
        ligne = self._db.fetch_one(_SELECT_BY_HASH_SQL, (hash_token(raw),))
        if ligne is None or ligne.get("revoked_at") is not None:
            return None
        # Comparaison en temps constant par acquit de conscience : la recherche
        # a déjà porté sur des empreintes, non sur le secret, mais rien
        # n'oblige un adaptateur à comparer proprement.
        if not secrets.compare_digest(
            str(ligne.get("token_hash") or ""), hash_token(raw)
        ):
            return None
        site = ligne.get("site")
        return IotScope(
            site=str(site) if site else None,
            device_id=str(ligne["device_id"]) if ligne.get("device_id") else None,
            label=str(ligne["label"]) if ligne.get("label") else None,
        )

    def list_all(self) -> "list[dict[str, Any]]":
        """Jetons connus, sans leur empreinte.

        L'empreinte n'est pas rendue : elle ne sert qu'à la recherche, et
        l'afficher dans une liste n'aiderait personne tout en donnant prise à
        une comparaison hors ligne.
        """
        return self._db.fetch_all(_SELECT_ALL_SQL, ())

    def revoke(self, token_id: int, *, now: "datetime | None" = None) -> bool:
        """Révoque un jeton. Vrai s'il était actif.

        La ligne est **conservée**, avec sa date de révocation : savoir qu'un
        jeton a existé et quand il a cessé de valoir fait partie de ce qu'un
        exploitant doit pouvoir retrouver.
        """
        touche = self._db.execute(
            _REVOKE_SQL, (now or datetime.now(UTC).replace(tzinfo=None), token_id)
        )
        return bool(touche)


def _default_adapter() -> "_DbAdapter":
    from core.database import db

    return db  # pyright: ignore[reportReturnType]
