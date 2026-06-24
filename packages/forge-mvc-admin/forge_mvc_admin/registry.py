# pyright: strict
"""Registre explicite des ressources admin (ADMIN-RESOURCE-CONTRACT-001).

Le registre est EXPLICITE : l'application enregistre ses ressources à la main
(``registry.register(AdminResource(...))``). Il n'y a aucune découverte
automatique des ressources (charte Forge, principe 3 : refuser la magie cachée).
Forge Core n'enregistre rien de lui-même ; le registre par défaut est vide tant
que l'application ne l'a pas peuplé.
"""
from __future__ import annotations

from forge_mvc_admin.exceptions import AdminRegistryError
from forge_mvc_admin.resources import AdminResource


class AdminRegistry:
    """Collection ordonnée de ressources admin, indexées par slug.

    L'ordre d'enregistrement est préservé : il pilotera l'ordre d'affichage dans
    la navigation. Un slug déjà enregistré lève `AdminRegistryError`.
    """

    def __init__(self) -> None:
        self._by_slug: dict[str, AdminResource] = {}

    def register(self, resource: AdminResource) -> AdminResource:
        """Enregistre une ressource. Lève si le slug est déjà pris. Retourne la ressource."""
        if resource.slug in self._by_slug:
            raise AdminRegistryError(f"slug déjà enregistré : {resource.slug!r}.")
        self._by_slug[resource.slug] = resource
        return resource

    def get(self, slug: str) -> AdminResource:
        """Retourne la ressource d'un slug, ou lève `AdminRegistryError` si inconnue."""
        try:
            return self._by_slug[slug]
        except KeyError:
            raise AdminRegistryError(f"ressource inconnue pour le slug {slug!r}.") from None

    def all(self) -> tuple[AdminResource, ...]:
        """Retourne les ressources dans leur ordre d'enregistrement."""
        return tuple(self._by_slug.values())

    def __contains__(self, slug: object) -> bool:
        return slug in self._by_slug

    def __len__(self) -> int:
        return len(self._by_slug)


# Registre par défaut du processus. L'application peut l'utiliser directement ou
# instancier son propre `AdminRegistry`. Forge n'y ajoute aucune ressource.
registry = AdminRegistry()
