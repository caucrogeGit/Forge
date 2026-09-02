# pyright: strict
"""Adresses IP et compte de visiteurs (`STATS-IP-ANONYMISATION-001`).

`forge-mvc-stats` ne stocke **aucune** adresse : sa table porte un nom, un
libellé, une catégorie et des métadonnées libres. Ce n'est pas un oubli, c'est
son périmètre : il compte des événements, il n'enquête pas.

Le champ `metadata` est pourtant libre, et rien n'empêchait d'y écrire
`{"ip": request.remote_addr}`. C'est le geste naturel de qui veut compter des
visiteurs uniques, et il transforme une table de statistiques en fichier de
données personnelles, soumis à conservation limitée et à droit d'accès, sans
que personne ne l'ait décidé.

## Ce que le module fournit

Deux façons de compter des visiteurs, et un refus.

**L'empreinte tournante** est la bonne réponse au besoin réel. Elle ne stocke
aucune adresse : elle en dérive un identifiant salé, valable une journée. Deux
visites du même visiteur le même jour donnent la même empreinte, deux jours de
suite non, et l'empreinte ne permet pas de remonter à l'adresse.

**La troncature** garde une adresse, amputée de sa partie identifiante. Elle
sert quand une granularité géographique approximative est vraiment nécessaire.
Elle reste une donnée à caractère personnel atténuée, pas une donnée anonyme,
et le module le dit plutôt que de laisser croire l'inverse.

**Le refus** ferme la porte du milieu : une adresse brute rangée sous une clé
qui la nomme est refusée à l'écriture. La ligne ne doit pas exister, plutôt
qu'être filtrée à chaque lecture.
"""
from __future__ import annotations

import hashlib
import ipaddress
from datetime import UTC, date, datetime
from typing import Any

__all__ = [
    "StatsPrivacyError",
    "IPV4_KEEP_BITS",
    "IPV6_KEEP_BITS",
    "ADDRESS_KEYS",
    "anonymize_ip",
    "visitor_hash",
    "looks_like_address_key",
    "assert_no_raw_address",
]

#: Bits conservés d'une adresse IPv4. Le dernier octet est mis à zéro, ce que
#: les autorités de protection des données admettent comme atténuation.
IPV4_KEEP_BITS = 24

#: Bits conservés d'une adresse IPv6. Un /48 désigne un site, pas une machine.
IPV6_KEEP_BITS = 48

#: Clés de métadonnées qui nomment une adresse. Une valeur d'adresse rangée
#: sous l'une d'elles est refusée.
ADDRESS_KEYS = frozenset({
    "ip", "ip_address", "ipaddress", "client_ip", "remote_addr", "remote_ip",
    "addr", "address", "adresse", "adresse_ip", "user_ip", "visitor_ip",
    "x_forwarded_for", "forwarded_for",
})


class StatsPrivacyError(ValueError):
    """Une adresse brute a été trouvée là où elle n'a pas sa place."""


def anonymize_ip(value: str) -> str:
    """Adresse tronquée de sa partie identifiante.

    IPv4 perd son dernier octet, IPv6 tout ce qui suit son /48.

    !!! warning
        Le résultat n'est **pas** une donnée anonyme. Il reste rattachable à un
        petit ensemble d'abonnés, et sur un réseau peu peuplé il désigne
        parfois une seule personne. Pour compter des visiteurs, préférez
        `visitor_hash`, qui ne garde rien.

    Raises:
        StatsPrivacyError: la valeur n'est pas une adresse IP.
    """
    brut = (value or "").strip()
    try:
        adresse = ipaddress.ip_address(brut)
    except ValueError as exc:
        raise StatsPrivacyError(f"adresse IP invalide : {value!r}.") from exc

    bits = IPV4_KEEP_BITS if adresse.version == 4 else IPV6_KEEP_BITS
    reseau = ipaddress.ip_network(f"{adresse}/{bits}", strict=False)
    return str(reseau.network_address)


def visitor_hash(
    value: str,
    secret: str,
    *,
    day: "date | datetime | None" = None,
) -> str:
    """Empreinte de visiteur, salée et valable une journée.

    Deux visites du même visiteur le même jour donnent la même empreinte ; le
    lendemain, une autre. Aucune adresse n'est conservée, et l'empreinte ne
    permet pas de remonter à l'adresse tant que le secret reste secret.

    `secret` doit être un vrai secret d'application, pas une constante écrite
    dans le code : sans lui, l'espace des adresses IPv4 se parcourt en entier
    en quelques secondes, et l'empreinte ne protège plus rien.

    Raises:
        StatsPrivacyError: adresse invalide, ou secret vide.
    """
    brut = (value or "").strip()
    try:
        ipaddress.ip_address(brut)
    except ValueError as exc:
        raise StatsPrivacyError(f"adresse IP invalide : {value!r}.") from exc

    sel = (secret or "").strip()
    if not sel:
        raise StatsPrivacyError(
            "un secret est requis : sans lui, l'espace des adresses IPv4 se "
            "parcourt en entier en quelques secondes et l'empreinte ne protège "
            "plus rien."
        )

    # `replace(tzinfo=None)` avant `.date()` : la valeur ne touche jamais la
    # base, mais le garde-fou de l'ADR-081 lit la forme et non la
    # destination, et s'y conformer vaut mieux qu'une exemption de plus.
    jour = day or datetime.now(UTC).replace(tzinfo=None).date()
    if isinstance(jour, datetime):
        jour = jour.date()
    empreinte = hashlib.sha256(f"{sel}|{jour.isoformat()}|{brut}".encode()).hexdigest()
    # Tronquée : seize caractères hexadécimaux suffisent à distinguer des
    # visiteurs sur une journée, et une empreinte plus courte est moins tentante
    # à conserver ou à rapprocher d'un autre jeu.
    return empreinte[:16]


def looks_like_address_key(key: str) -> bool:
    """Vrai si le nom de clé désigne une adresse.

    Le contrôle porte sur la **clé** et non sur la valeur : une chaîne comme
    « 1.2.3.4 » est une adresse IPv4 valide et un numéro de version tout aussi
    valable, et refuser toutes les valeurs de cette forme casserait des
    métadonnées légitimes.
    """
    normalisee = (key or "").strip().lower().replace("-", "_")
    return normalisee in ADDRESS_KEYS


def assert_no_raw_address(metadata: "dict[str, Any]") -> None:
    """Refuse une adresse brute rangée sous une clé qui la nomme.

    Le refus a lieu **à l'écriture** : la ligne ne doit pas exister, plutôt
    qu'être filtrée à chaque lecture. Une valeur déjà tronquée ou déjà réduite
    en empreinte passe, puisqu'elle n'est plus une adresse.

    Raises:
        StatsPrivacyError: une clé d'adresse porte une adresse IP complète.
    """
    for cle, valeur in metadata.items():
        if not looks_like_address_key(str(cle)) or not isinstance(valeur, str):
            continue
        brut = valeur.strip()
        try:
            adresse = ipaddress.ip_address(brut)
        except ValueError:
            continue
        if str(adresse) == anonymize_ip(brut):
            # Déjà tronquée : le dernier octet est nul, l'appelant a fait le
            # geste. Accepter serait incohérent avec le fait de le proposer.
            continue
        raise StatsPrivacyError(
            f"adresse IP complète dans metadata[{cle!r}]. "
            "forge-mvc-stats compte des événements, il n'enquête pas : une "
            "adresse en fait un fichier de données personnelles. Utilisez "
            "visitor_hash() pour compter des visiteurs uniques, ou "
            "anonymize_ip() si une granularité géographique est nécessaire. "
            "Pour conserver une adresse à des fins de sécurité, c'est "
            "forge-mvc-audit qu'il faut, pas les statistiques."
        )
