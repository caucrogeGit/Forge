"""DEPLOY-CHECK-ROUTES-PACKAGE-001 — `deploy:check` reconnaît un projet rc7.

Le contrôle de racine exigeait le fichier de routes unique, supprimé par
l'ADR-068 au profit du package `mvc/routes/`, un fichier par contrôleur. Depuis,
`deploy:check` n'a reconnu AUCUN projet généré : il ouvrait son diagnostic de
production par « racine non détectée », sur une racine parfaitement valide.

Le défaut a survécu à sa propre suite de tests parce que celle-ci fabriquait
son projet jetable avec cet ancien fichier. Le test validait donc un projet
d'avant l'ADR-068, et ne pouvait pas voir ce que voyait tout utilisateur.

C'est le motif à retenir : une fixture qui construit le monde d'avant valide
autre chose que ce qu'elle annonce. Les tests ci-dessous partent donc de la
structure que `forge new` écrit réellement aujourd'hui.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli.deploy import _check_results, _looks_like_forge_project


def _socle(racine: Path) -> Path:
    """Ce que tout projet Forge porte, hors déclaration de routes."""
    (racine / "app.py").write_text("", encoding="utf-8")
    (racine / "config.py").write_text("", encoding="utf-8")
    (racine / "env").mkdir()
    (racine / "env" / "example").write_text("", encoding="utf-8")
    (racine / "mvc").mkdir()
    return racine


def _package_de_routes(racine: Path) -> Path:
    """La forme canonique depuis l'ADR-068."""
    (racine / "mvc" / "routes").mkdir()
    (racine / "mvc" / "routes" / "__init__.py").write_text("", encoding="utf-8")
    return racine


class TestRacineReconnue:

    def test_projet_rc7_reconnu(self, tmp_path: Path) -> None:
        """Le cas mesuré : un projet généré aujourd'hui."""
        assert _looks_like_forge_project(_package_de_routes(_socle(tmp_path)))

    def test_projet_anterieur_reste_reconnu(self, tmp_path: Path) -> None:
        """Un projet pré-ADR-068 n'a pas cessé d'être un projet Forge."""
        racine = _socle(tmp_path)
        (racine / "mvc" / "routes.py").write_text("", encoding="utf-8")  # adr-068-forme-anterieure

        assert _looks_like_forge_project(racine)

    def test_le_diagnostic_ouvre_sur_un_vert(self, tmp_path: Path) -> None:
        """La ligne lue en premier par celui qui déploie."""
        racine = _package_de_routes(_socle(tmp_path))

        resultat = next(r for r in _check_results(racine) if r.label == "Projet Forge")

        assert resultat.status == "ok"


class TestRacineRefusee:

    def test_dossier_vide_refuse(self, tmp_path: Path) -> None:
        assert not _looks_like_forge_project(tmp_path)

    def test_mvc_sans_routes_refuse(self, tmp_path: Path) -> None:
        """`mvc/` seul ne prouve rien : les routes font le projet."""
        assert not _looks_like_forge_project(_socle(tmp_path))

    def test_package_de_routes_sans_init_refuse(self, tmp_path: Path) -> None:
        """Un dossier `routes/` sans `__init__.py` n'est pas un package."""
        racine = _socle(tmp_path)
        (racine / "mvc" / "routes").mkdir()

        assert not _looks_like_forge_project(racine)

    @pytest.mark.parametrize("manquant", ["app.py", "config.py", "env/example"])
    def test_socle_incomplet_refuse(self, tmp_path: Path, manquant: str) -> None:
        racine = _package_de_routes(_socle(tmp_path))
        (racine / manquant).unlink()

        assert not _looks_like_forge_project(racine)
