# pyright: strict
"""Garde RBAC par préfixe d'URL, en middleware (manque terrain B).

Le natif ne protège qu'au décorateur, route par route. Ce middleware protège des
**domaines entiers** par préfixe de chemin (``/admin``, ``/facturation``…), en une
table ``préfixe -> permission`` évaluée à chaque requête. Il couvre donc aussi les
**routes futures** d'un préfixe, sans passe sur le routeur ni décoration.

Adossé au **contrat** (rbac.json) : réutilise ``get_request_roles`` (résolution
moderne en base, ADR-010) et ``has_contract_permission``. Aucune table
``permissions``/``role_permissions`` requise.

Usage (couche app) ::

    from forge_mvc_rbac import PrefixPermissionMiddleware
    app = Application(router, middlewares=[
        AuthMiddleware("/login"),
        PrefixPermissionMiddleware({
            "/admin": "admin.access",
            "/facturation": "billing.view",
        }),
    ])
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from core.http.request import Request
from core.http.response import Response

__all__ = ["PrefixPermissionMiddleware"]


def _matches(path: str, prefix: str) -> bool:
    """Vrai si ``path`` est sous ``prefix`` : égal, ou suivi de « / ».

    ``/admin`` couvre ``/admin`` et ``/admin/...`` mais pas ``/administrateur``.
    """
    normalized = prefix.rstrip("/")
    if not normalized:
        return True
    return path == normalized or path.startswith(normalized + "/")


class PrefixPermissionMiddleware:
    """Refuse (403) toute requête sous un préfixe sans la permission contractuelle.

    Le préfixe **le plus spécifique** (le plus long) qui matche gagne : une seule
    règle s'applique par requête. Aucune règle ne matche → laisse passer.
    """

    def __init__(
        self,
        rules: "Mapping[str, str]",
        *,
        project_root: "str | Path" = ".",
        denied_response: "Callable[[], Response] | None" = None,
    ) -> None:
        # Table préfixe -> permission, triée du plus spécifique (préfixe le plus
        # long) au moins spécifique : une seule règle (la plus précise) s'applique.
        self._rules: list[tuple[str, str]] = sorted(
            rules.items(), key=lambda kv: len(kv[0].rstrip("/")), reverse=True
        )
        self._project_root = project_root
        self._denied_response = denied_response

    def check(self, request: Request) -> "Response | None":
        path = getattr(request, "path", "") or ""
        for prefix, permission in self._rules:
            if not _matches(path, prefix):
                continue
            # Import paresseux : évite un cycle et ne charge le contrat que si utile.
            from forge_mvc_rbac.contract import (
                get_request_roles,
                has_contract_permission,
                load_rbac_contract,
            )

            result = load_rbac_contract(self._project_root)
            roles = get_request_roles(request)
            if has_contract_permission(result, roles, permission):
                return None
            return self._denied()
        return None

    def _denied(self) -> Response:
        if self._denied_response is not None:
            return self._denied_response()
        return Response(403, body=b"Forbidden")
