"""Garde-fou — CLI-PUBLIC-SHARED-001 : pas de reach-in privé entre générateurs publics.

Les générateurs make:public-* partageaient des helpers de scaffolding en
s'important mutuellement des symboles privés (``_insert_import``, ``_humanize``,
``_ensure_route``...), chacun sous ``# pyright: reportPrivateUsage=false``. Les
helpers purs vivent désormais dans ``cli/public/_shared.py`` (API interne du
sous-paquet) et les deux helpers spécifiques aux pages sont publics dans
``public_page``. Ce garde interdit la réapparition d'un reach-in privé et de la
directive de suppression.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PUBLIC_DIR = PROJECT_ROOT / "cli" / "public"


def _modules() -> list[Path]:
    return sorted(p for p in PUBLIC_DIR.glob("*.py") if p.name != "__init__.py")


def test_shared_module_expose_les_helpers_purs():
    import cli.public._shared as shared

    for name in (
        "humanize", "ensure_trailing_newline", "insert_import", "ensure_import",
        "require_entities_module", "build_public_routes_file", "public_routes_branchement",
    ):
        assert callable(getattr(shared, name, None)), f"_shared doit exposer {name}"


def test_aucune_directive_reportprivateusage_active():
    # Le reach-in privé cross-module est ce que pyright strict interdit (et ce
    # que les directives supprimaient). Plus aucune directive = pyright strict
    # (exécuté en CI) garantit désormais l'absence de reach-in privé.
    for path in _modules():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            assert not stripped.startswith("# pyright: reportPrivateUsage"), (
                f"{path.name} ne doit plus supprimer reportPrivateUsage "
                "(le reach-in privé a été retiré, CLI-PUBLIC-SHARED-001)."
            )
