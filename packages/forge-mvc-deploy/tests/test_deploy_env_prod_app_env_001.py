"""DEPLOY-ENV-PROD-APP-ENV-001 — `env/prod` déclare l'environnement qu'il sert.

`config.py` lit `APP_ENV` dans l'environnement du processus et retombe sur
`dev` quand elle est absente. Le gabarit `env/example` ne la déclarait pas : un
`env/prod` qui l'oublie fait donc tourner la **production** en configuration de
développement.

Ce n'est pas un détail de confort. En `dev`, la page d'erreur du squelette rend
au visiteur le type, le message et la pile de l'exception.

Le point d'entrée ne peut plus rattraper l'oubli, et c'est voulu :
`SKELETON-PUBLIC-APPLICATION-001` a retiré de `app.py` le `setdefault` qui
posait `APP_ENV` à l'import, précisément parce qu'il posait `dev` sous Gunicorn.
La déclaration doit vivre dans `env/prod`, et son absence est une erreur.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli.deploy import _check_results, _verifier_app_env_prod


class TestControle:

    def test_declaration_correcte(self) -> None:
        resultat = _verifier_app_env_prod({"APP_ENV": "prod"}, True)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_absence_est_une_erreur(self) -> None:
        """Le cas par défaut, et le plus dangereux."""
        resultat = _verifier_app_env_prod({"DB_NAME": "x"}, True)

        assert resultat is not None
        assert resultat.status == "error"
        assert "dev" in resultat.detail

    def test_le_message_dit_ce_qui_fuirait(self) -> None:
        resultat = _verifier_app_env_prod({}, True)

        assert resultat is not None
        assert "pile d'exception" in resultat.detail

    @pytest.mark.parametrize("valeur", ["dev", "test", "Prod", ""])
    def test_toute_autre_valeur_est_une_erreur(self, valeur: str) -> None:
        resultat = _verifier_app_env_prod({"APP_ENV": valeur}, True)

        assert resultat is not None
        assert resultat.status == "error"

    def test_espaces_tolerees(self) -> None:
        resultat = _verifier_app_env_prod({"APP_ENV": "  prod  "}, True)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_sans_env_prod_ne_dit_rien(self) -> None:
        """Son absence est déjà signalée ailleurs."""
        assert _verifier_app_env_prod({}, False) is None


class TestBranchement:

    def test_le_controle_figure_dans_le_diagnostic(self, tmp_path: Path) -> None:
        (tmp_path / "env").mkdir()
        (tmp_path / "env" / "prod").write_text(
            "DB_HOST=localhost\nDB_NAME=x\nDB_APP_LOGIN=y\n", encoding="utf-8")

        resultats = _check_results(tmp_path)
        ligne = next((r for r in resultats if r.label == "Variable APP_ENV"), None)

        assert ligne is not None
        assert ligne.status == "error"

    def test_un_env_prod_complet_ne_declenche_rien(self, tmp_path: Path) -> None:
        (tmp_path / "env").mkdir()
        (tmp_path / "env" / "prod").write_text(
            "APP_ENV=prod\nDB_HOST=localhost\nDB_NAME=x\nDB_APP_LOGIN=y\n",
            encoding="utf-8")

        ligne = next(r for r in _check_results(tmp_path) if r.label == "Variable APP_ENV")

        assert ligne.status == "ok"


class TestGabaritEnv:

    def test_le_gabarit_nomme_la_variable(self) -> None:
        """Ce qui n'est pas dans le gabarit n'est pas dans les env dérivés."""
        racine = Path(__file__).resolve().parents[3]
        gabarit = (racine / "skeleton" / "data" / "env" / "example").read_text(encoding="utf-8")

        assert "APP_ENV=" in gabarit
        assert "APP_ENV=prod" in gabarit, "le gabarit doit dire ce que prod exige"
