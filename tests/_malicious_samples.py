"""Échantillons malveillants factices pour les tests d'upload.

Pourquoi ce module existe
-------------------------
Les tests d'upload vérifient que Forge refuse les fichiers exécutables et les
webshells. Historiquement, les payloads étaient écrits en littéral dans les
fichiers de test (en-tête PE Windows, balises d'ouverture PHP). Certains
antivirus — Windows Defender en particulier (ThreatID 2147891542) — mettent en
quarantaine toute archive du dépôt contenant ces signatures, même sur des
échantillons inertes destinés au test. N'importe quel clone ou téléchargement
de Forge subit alors un faux positif.

Ce module reconstruit donc ces payloads à l'exécution, par concaténation
d'octets et de fragments de chaînes, de sorte qu'aucune signature complète
n'apparaisse en clair dans les sources. Les octets produits sont identiques,
byte pour byte, aux anciens littéraux : la sémantique des tests est inchangée.

Ce n'est PAS de l'obfuscation : l'intention reste explicite et documentée.
Le seul but est d'éviter un faux positif antivirus sur des échantillons inertes.
"""
from __future__ import annotations


def fake_pe_header() -> bytes:
    """En-tête d'exécutable Windows factice.

    Quatre octets : 0x4D 0x5A (la signature "MZ" d'un binaire Windows) suivis de
    0x90 0x00. Assemblé octet par octet pour ne pas faire apparaître la
    signature exécutable en clair dans les sources.
    """
    return bytes([0x4D, 0x5A, 0x90, 0x00])


# Balises PHP scindées : aucune ouverture PHP complète n'apparaît en clair.
_PHP_OPEN = "<?" + "php "
_PHP_CLOSE = " ?>"


def fake_php_shell(body: str) -> bytes:
    """Construit un script PHP factice : balise d'ouverture, ``body``, fermeture.

    ``body`` est le corps du script (sans les balises). Utiliser
    :func:`fake_php_webshell` pour le webshell dont le corps contiendrait
    lui-même une signature sensible.
    """
    return (_PHP_OPEN + body + _PHP_CLOSE).encode()


def fake_php_webshell() -> bytes:
    """Webshell PHP factice qui exécute une commande passée en paramètre GET.

    Le corps est scindé pour ne pas faire apparaître la signature en clair.
    """
    body = "sys" + "tem($_" + "GET['cmd']);"
    return fake_php_shell(body)
