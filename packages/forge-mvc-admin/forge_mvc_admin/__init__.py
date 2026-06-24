# pyright: strict
"""forge-mvc-admin — Opt-in de back-office applicatif Forge.

Couche châssis (couche 1 de l'architecture hybride, voir la roadmap de cadrage
section 7) : ce paquet porte le contrat d'une ressource administrable
(`AdminResource`) et le registre explicite (`AdminRegistry`) que les vues
consommeront. Les vues, les actions et la sécurité HTTP viendront par les
tickets `ADMIN-*` suivants.

Voir `docs/roadmap/forge-admin-roadmap.md`.
"""
from forge_mvc_admin.exceptions import (
    AdminError,
    AdminRegistryError,
    AdminResourceError,
)
from forge_mvc_admin.registry import AdminRegistry, registry
from forge_mvc_admin.resources import AdminResource

__version__ = "1.0.0b17"

__all__ = [
    "AdminResource",
    "AdminRegistry",
    "registry",
    "AdminError",
    "AdminResourceError",
    "AdminRegistryError",
]
