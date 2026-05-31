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


class OptIn(NamedTuple):
    """Une brique opt-in officielle."""

    name: str            # identifiant court (mfa, rbac, …)
    package_dist: str    # nom de distribution PyPI (forge-mvc-…)
    package_import: str  # namespace Python importable (forge_mvc_…)
    summary: str         # description d'une ligne


OFFICIAL_OPTINS: dict[str, OptIn] = {
    "mfa": OptIn(
        "mfa", "forge-mvc-mfa", "forge_mvc_mfa",
        "Authentification multi-facteurs (TOTP, codes de récupération).",
    ),
    "rbac": OptIn(
        "rbac", "forge-mvc-rbac", "forge_mvc_rbac",
        "Contrôle d'accès par rôles et permissions déclaratives.",
    ),
    "workflow": OptIn(
        "workflow", "forge-mvc-workflow", "forge_mvc_workflow",
        "Statuts et transitions applicatives.",
    ),
    "stats": OptIn(
        "stats", "forge-mvc-stats", "forge_mvc_stats",
        "Agrégats et compteurs d'événements.",
    ),
    "media": OptIn(
        "media", "forge-mvc-media", "forge_mvc_media",
        "Gestion applicative des médias.",
    ),
    "iot": OptIn(
        "iot", "forge-mvc-iot", "forge_mvc_iot",
        "Réception/exposition de données IoT (MQTT, stockage, API HTTP).",
    ),
}


def optin_names() -> list[str]:
    """Identifiants courts des opt-ins officiels, triés."""
    return sorted(OFFICIAL_OPTINS)
