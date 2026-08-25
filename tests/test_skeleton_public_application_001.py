"""SKELETON-PUBLIC-APPLICATION-001 — le squelette expose l'application armée.

Suite du ticket 67 (retour terrain SéquenCiel), sous l'ADR-092. Le refus posé
par `WSGI-UNARMED-APP-GUARD-001` rend la panne bruyante ; ce ticket ci donne la
sortie, en attendant que le câblage descende dans une source lue par les deux
points d'entrée.

Deux conditions, et la seconde est celle qu'on oublie.

**Un nom public.** L'`Application` s'appelait `_app`. Le souligné disait
« personne d'autre que ce fichier », ce qui a cessé d'être vrai le jour où une
production a existé : `wsgi.py` doit pouvoir servir cette application ci, celle
qui porte les gardes.

**Aucun effet de bord à l'import.** `app.py` analysait `--env` au niveau module.
Sous Gunicorn, `sys.argv` est celui de Gunicorn, `--env` est absent, le défaut
vaut `dev`, et `os.environ.setdefault` posait donc `APP_ENV=dev` **sur un
serveur de production** dès que l'environnement du processus ne la déclarait pas.
Mesuré avant correction, en important le fichier avec l'`argv` de Gunicorn :

    APP_ENV posé dans l'environnement par l'import : 'dev'

Une production ainsi basculée en configuration de développement rend les
tracebacks au visiteur (`_error_context` les livre quand `APP_ENV == "dev"`).
Le seul rempart était alors l'`EnvironmentFile` de l'unité systemd : la justesse
du point d'entrée dépendait de la façon dont l'exploitant avait écrit son unité,
ce qui est exactement le défaut du ticket 67 déplacé d'un cran.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKELETON_APP = PROJECT_ROOT / "skeleton" / "data" / "app.py"


@pytest.fixture(scope="module")
def arbre() -> ast.Module:
    return ast.parse(SKELETON_APP.read_text(encoding="utf-8"))


def _affectations_de_module(arbre: ast.Module) -> set[str]:
    """Noms affectés au niveau module, hors blocs conditionnels."""
    noms: set[str] = set()
    for noeud in arbre.body:
        if isinstance(noeud, ast.Assign):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name):
                    noms.add(cible.id)
    return noms


# ── Le nom public ────────────────────────────────────────────────────────────

class TestNomPublic:

    def test_l_application_porte_un_nom_public(self, arbre: ast.Module) -> None:
        assert "application" in _affectations_de_module(arbre)

    def test_le_nom_prive_a_disparu(self, arbre: ast.Module) -> None:
        """Deux noms pour un objet, c'est le second qui finit servi par erreur."""
        assert "_app" not in _affectations_de_module(arbre)

    def test_c_est_bien_une_Application(self, arbre: ast.Module) -> None:
        affectation = next(
            n for n in arbre.body
            if isinstance(n, ast.Assign)
            and any(isinstance(c, ast.Name) and c.id == "application" for c in n.targets)
        )
        appel = affectation.value
        assert isinstance(appel, ast.Call)
        assert isinstance(appel.func, ast.Name) and appel.func.id == "Application"

    def test_le_handler_dispatche_sur_ce_nom(self) -> None:
        """Le serveur de développement et wsgi.py servent le MÊME objet."""
        source = SKELETON_APP.read_text(encoding="utf-8")

        assert "return application.dispatch(request)" in source


# ── L'absence d'effet de bord à l'import ─────────────────────────────────────

class TestImportSansEffetDeBord:

    def test_l_analyse_d_arguments_est_sous_le_garde(self, arbre: ast.Module) -> None:
        """`parse_known_args` au niveau module s'exécute sous Gunicorn."""
        for noeud in arbre.body:
            if isinstance(noeud, ast.If):
                continue  # protégé par une condition, `__main__` en pratique
            for interne in ast.walk(noeud):
                if isinstance(interne, ast.Call):
                    cible = interne.func
                    nom = cible.attr if isinstance(cible, ast.Attribute) else None
                    assert nom != "parse_known_args", (
                        "l'analyse d'arguments s'exécute à l'import : sous Gunicorn "
                        "elle pose APP_ENV=dev sur un serveur de production")

    def test_le_garde_est_bien_celui_du_script_principal(self, arbre: ast.Module) -> None:
        """Le protéger par autre chose ne protégerait rien."""
        gardes = [
            n for n in arbre.body
            if isinstance(n, ast.If)
            and any(isinstance(i, ast.Call)
                    and isinstance(i.func, ast.Attribute)
                    and i.func.attr == "parse_known_args"
                    for i in ast.walk(n))
        ]
        assert gardes, "aucune analyse d'arguments trouvée"
        test = gardes[0].test
        assert isinstance(test, ast.Compare)
        assert isinstance(test.left, ast.Name) and test.left.id == "__name__"

    def test_l_import_ne_pose_pas_app_env(self, tmp_path: Path) -> None:
        """La mesure, pas la lecture : on importe avec l'argv de Gunicorn.

        Un sous processus, parce que `app.py` importe `config` et configure le
        framework : le faire dans le processus de test contaminerait les autres.
        """
        (tmp_path / "app.py").write_text(
            SKELETON_APP.read_text(encoding="utf-8"), encoding="utf-8")

        programme = (
            "import sys, os\n"
            "sys.argv = ['gunicorn', 'wsgi:application', '--workers', '4']\n"
            "try:\n"
            "    import app\n"
            "except Exception:\n"
            "    pass\n"   # l'import complet demande un projet ; seul l'en-tête compte
            "print(repr(os.environ.get('APP_ENV')))\n"
        )
        env = {k: v for k, v in os.environ.items() if k != "APP_ENV"}
        env["PYTHONPATH"] = f"{PROJECT_ROOT}{os.pathsep}{tmp_path}"

        rendu = subprocess.run(
            [sys.executable, "-c", programme],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
        )

        assert rendu.stdout.strip() == "None", (
            f"l'import a posé APP_ENV={rendu.stdout.strip()} : sous Gunicorn, "
            f"une production basculerait en configuration de développement")


# ── Le fichier engendré par deploy:init ──────────────────────────────────────

class TestGabaritWsgi:
    """Le pont ne tient que si les deux moitiés se rejoignent."""

    def test_le_gabarit_importe_le_nom_que_le_squelette_expose(self) -> None:
        pytest.importorskip("forge_mvc_deploy")
        from forge_mvc_deploy.cli.deploy import _wsgi_py

        importes = {
            alias.name
            for noeud in ast.walk(ast.parse(_wsgi_py()))
            if isinstance(noeud, ast.ImportFrom) and noeud.module == "app"
            for alias in noeud.names
        }

        assert "application" in importes, (
            "le wsgi.py engendré importe un nom que le squelette n'expose pas")

    def test_le_gabarit_n_utilise_plus_la_fabrique_generique(self) -> None:
        pytest.importorskip("forge_mvc_deploy")
        from forge_mvc_deploy.cli.deploy import _wsgi_py

        source = _wsgi_py()
        appels = {
            noeud.func.id
            for noeud in ast.walk(ast.parse(source))
            if isinstance(noeud, ast.Call) and isinstance(noeud.func, ast.Name)
        }

        assert "create_wsgi_app" in appels
        assert "create_configured_wsgi_app" not in appels
