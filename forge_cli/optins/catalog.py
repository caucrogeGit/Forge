"""Catalogue canonique des opt-ins officiels Forge.

Ticket : OPTIN-CLI-VERBS-001 (ADR-016, palier 3a).

Source de vérité unique pour la famille de commandes ``opt-in:*``. Chaque opt-in
officiel est une brique optionnelle distribuée comme package PyPI
``forge-mvc-*`` (voir docs/reference/vocabulaire-opt-in.md). Le catalogue ne
décrit que *ce qui existe* (plan distribution) ; l'état d'activation d'un projet
donné se lit ailleurs (couche ``optins/``).
"""
from __future__ import annotations

from typing import NamedTuple


# Les trois formes d'intégration d'un opt-in dans une application (ADR-016 D8) :
#   - "route"        : la brique possède ses routes (register_*_routes) →
#                      câblage projet via la couche optins/ ;
#   - "library"      : bibliothèque pure → on importe et on appelle, rien à
#                      brancher côté projet ;
#   - "crosscutting" : se greffe dans un flux existant (décorateurs, starter).
KIND_ROUTE = "route"
KIND_LIBRARY = "library"
KIND_CROSSCUTTING = "crosscutting"


class OptIn(NamedTuple):
    """Une brique opt-in officielle."""

    name: str            # identifiant court (mfa, rbac, …)
    package_dist: str    # nom de distribution PyPI (forge-mvc-…)
    package_import: str  # namespace Python importable (forge_mvc_…)
    kind: str            # forme d'intégration : route | library | crosscutting
    summary: str         # description d'une ligne


OFFICIAL_OPTINS: dict[str, OptIn] = {
    "mfa": OptIn(
        "mfa", "forge-mvc-mfa", "forge_mvc_mfa", KIND_CROSSCUTTING,
        "Authentification multi-facteurs (TOTP, codes de récupération).",
    ),
    "rbac": OptIn(
        "rbac", "forge-mvc-rbac", "forge_mvc_rbac", KIND_CROSSCUTTING,
        "Contrôle d'accès par rôles et permissions déclaratives.",
    ),
    "workflow": OptIn(
        "workflow", "forge-mvc-workflow", "forge_mvc_workflow", KIND_LIBRARY,
        "Statuts et transitions applicatives.",
    ),
    "stats": OptIn(
        "stats", "forge-mvc-stats", "forge_mvc_stats", KIND_LIBRARY,
        "Agrégats et compteurs d'événements.",
    ),
    "images": OptIn(
        "images", "forge-mvc-images", "forge_mvc_images", KIND_LIBRARY,
        "Traitement d'image (Pillow) + gestion applicative des médias (galerie, couverture).",
    ),
    "files": OptIn(
        "files", "forge-mvc-files", "forge_mvc_files", KIND_LIBRARY,
        "Upload générique : écriture sécurisée, storage, service de fichiers, rate-limit.",
    ),
    "iot": OptIn(
        "iot", "forge-mvc-iot", "forge_mvc_iot", KIND_ROUTE,
        "Réception/exposition de données IoT (MQTT, stockage, API HTTP).",
    ),
    "video": OptIn(
        "video", "forge-mvc-video", "forge_mvc_video", KIND_ROUTE,
        "Upload, transcodage MP4 et lecture vidéo en streaming (HTTP Range).",
    ),
    "audio": OptIn(
        "audio", "forge-mvc-audio", "forge_mvc_audio", KIND_ROUTE,
        "Upload, sondage, transcodage MP3 et lecture audio en streaming (HTTP Range).",
    ),
}


def optin_names() -> list[str]:
    """Identifiants courts des opt-ins officiels, triés."""
    return sorted(OFFICIAL_OPTINS)


# La famille opt-in:* ne gère que les opt-ins officiels. Un module local que
# le développeur écrit lui-même reste géré par module:* (ADR-016 A2).
LOCAL_MODULE_HINT = (
    "Pour un module local que vous écrivez vous-même, voir : forge module:install"
)
