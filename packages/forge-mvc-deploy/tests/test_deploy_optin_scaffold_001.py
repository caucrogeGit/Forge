"""Scaffold du paquet forge-mvc-deploy (DEPLOY-EXTRACT-001, ADR-053).

Garde-fous structurels : opt-in CLI-only, indépendance du cœur, le cœur ne
fournit plus deploy:init/deploy:check, dépendances minimales.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_deploy = pytest.importorskip("forge_mvc_deploy")

PKG_ROOT = Path(forge_mvc_deploy.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_n_importe_pas_le_paquet_deploy() -> None:
    core_dir = REPO_ROOT / "core"
    offenders: list[str] = []
    for path in core_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "import forge_mvc_deploy" in text or "from forge_mvc_deploy" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"le cœur ne doit pas importer forge_mvc_deploy : {offenders}"


def test_code_deploy_retire_du_coeur_cli() -> None:
    # ADR-053 : le code de déploiement a quitté cli/deploy/deploy.py.
    assert not (REPO_ROOT / "cli" / "deploy" / "deploy.py").exists(), (
        "cli/deploy/deploy.py doit avoir été retiré au profit de forge-mvc-deploy"
    )


def test_dispatch_deploy_passe_par_l_optin() -> None:
    # ADR-059 : deploy:* est dispatché via la table opt-in (import paresseux,
    # repli propre si forge-mvc-deploy n'est pas installé).
    from cli.commands.optin_dispatch import OPTIN_COMMANDS

    assert "deploy:init" in OPTIN_COMMANDS and "deploy:check" in OPTIN_COMMANDS
    spec = OPTIN_COMMANDS["deploy:init"]
    assert spec.module == "forge_mvc_deploy.cli.deploy"
    assert spec.package == "forge-mvc-deploy"


def test_optin_cli_only_pas_de_migration() -> None:
    # Opt-in CLI-only : aucune migration SQL embarquée, aucune API runtime.
    assert not (PKG_ROOT / "migrations").exists(), (
        "forge-mvc-deploy est CLI-only : pas de migrations embarquées"
    )


def test_dependances_minimales() -> None:
    pyproject = (PKG_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert "forge-mvc>=" in pyproject
    assert "segno" not in pyproject and "Pillow" not in pyproject
