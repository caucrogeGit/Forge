"""DEPLOY-ARTEFACTS-REELS-001 — ce que `forge deploy:init` écrit tient debout.

`forge-mvc-deploy` produit quatre fichiers qu'un exploitant installe sur un
serveur : `wsgi.py`, une configuration Nginx, une unité systemd et un README.
Les contrôles existants vérifiaient qu'ils **contiennent des sous-chaînes** :

    assert "client_max_body_size" in conf
    assert "WorkingDirectory" in unite

C'est la signature poursuivie par tout ce pré-mortem. Un fichier peut contenir
exactement les mots attendus et rester refusé par l'outil qui le lit.

Le cas est celui du script de `forge db:init`, et il est aussi peu rattrapable :
un artefact de déploiement invalide se découvre sur le serveur de production,
au moment de la mise en service.

## Ce que ce fichier vérifie, et ce qu'il ne peut pas

`nginx` n'est pas installé ici : la configuration reste donc contrôlée par sa
forme, et c'est écrit plutôt que passé sous silence. `systemd-analyze` est
présent, et l'unité est réellement soumise à lui.

Le contrôle le plus fort ne demande aucun outil : `wsgi.py` importe
`create_configured_wsgi_app` du cœur. Un renommage de ce symbole casserait tous
les déploiements engendrés, et rien ne le disait.
"""
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

#: `systemd-analyze verify` sort **toujours en 0**, même sur une unité qu'il
#: refuse explicitement : mesuré sur cette machine, y compris avec une section
#: inconnue. C'est donc son texte qu'il faut juger, pas son code de retour.
_PLAINTES_DE_STRUCTURE = ("Refusing", "bad unit file setting", "Unknown section")

#: Cette remarque ne concerne pas l'unité mais l'environnement : le
#: `.venv/bin/gunicorn` du projet n'existe pas dans un dossier jetable.
_REMARQUE_D_ENVIRONNEMENT = "is not executable"


@pytest.fixture(scope="module")
def artefacts(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Lance réellement `forge deploy:init` dans un projet jetable."""
    projet = tmp_path_factory.mktemp("deploiement")
    resultat = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "forge.py"), "deploy:init"],
        cwd=projet, capture_output=True, text=True, timeout=180,
    )
    assert resultat.returncode == 0, (
        f"`forge deploy:init` a échoué :\n{resultat.stdout}\n{resultat.stderr}"
    )
    return projet


def test_les_quatre_fichiers_sont_ecrits(artefacts: Path) -> None:
    """Contrôle de montage : sans eux, tous les tests suivants passeraient à vide."""
    attendus = [
        "wsgi.py",
        "deploy/nginx/forge-app.conf",
        "deploy/systemd/forge-app.service",
        "deploy/README_DEPLOY.md",
    ]
    manquants = [rel for rel in attendus if not (artefacts / rel).is_file()]

    assert not manquants, f"fichiers non écrits : {manquants}"


# ── Le point d'entrée WSGI ───────────────────────────────────────────────────


def test_le_wsgi_engendre_est_du_python_valide(artefacts: Path) -> None:
    """Un fichier de production non compilable ne se découvre qu'au démarrage."""
    source = (artefacts / "wsgi.py").read_text(encoding="utf-8")

    ast.parse(source)  # lève SyntaxError si le gabarit a dérivé


#: Modules du PROJET, absents du dépôt framework (ADR-044). Leur contenu est
#: engendré par le squelette : c'est là qu'on vérifie ce qu'ils exposent.
MODULES_DU_PROJET = {"app": Path("skeleton") / "data" / "app.py"}


def _noms_exposes_par(source: str) -> set[str]:
    """Noms affectés au niveau module, sans exécuter le fichier."""
    noms: set[str] = set()
    for noeud in ast.parse(source).body:
        if isinstance(noeud, ast.Assign):
            noms.update(c.id for c in noeud.targets if isinstance(c, ast.Name))
    return noms


def test_le_symbole_importe_par_le_wsgi_existe_vraiment(artefacts: Path) -> None:
    """LE test du ticket, et il ne demande aucun outil externe.

    `wsgi.py` importe `create_wsgi_app` de `core.app.wsgi` et `application` de
    `app`. Un renommage de l'un ou l'autre casserait **tous les déploiements
    engendrés**, et aucun contrôle de sous-chaîne ne l'aurait dit : le fichier
    contiendrait toujours le mot attendu.

    Le second import ne se résout pas ici, `app.py` vivant dans le projet et
    non dans le dépôt framework. Il est donc vérifié là où il est écrit, dans le
    squelette. C'est cette moitié ci qui compte le plus : le ticket 67 est né
    d'un `wsgi.py` qui servait autre chose que l'application de `app.py`.
    """
    import importlib

    racine_depot = Path(__file__).resolve().parent.parent
    arbre = ast.parse((artefacts / "wsgi.py").read_text(encoding="utf-8"))

    importes = [
        (noeud.module, alias.name)
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.ImportFrom) and noeud.module
        for alias in noeud.names
    ]
    assert importes, "le wsgi engendré n'importe rien : il ne peut pas servir"

    absents: list[str] = []
    for module, symbole in importes:
        fichier_projet = MODULES_DU_PROJET.get(module)
        if fichier_projet is not None:
            source = (racine_depot / fichier_projet).read_text(encoding="utf-8")
            if symbole not in _noms_exposes_par(source):
                absents.append(f"{module}.{symbole} (absent de {fichier_projet})")
            continue
        try:
            objet = importlib.import_module(module)
        except ImportError:
            absents.append(f"{module} (module introuvable)")
            continue
        if not hasattr(objet, symbole):
            absents.append(f"{module}.{symbole}")

    assert not absents, (
        "le wsgi engendré importe des symboles qui n'existent pas dans Forge :\n  "
        + "\n  ".join(absents)
        + "\nTout déploiement produit par `forge deploy:init` échouerait au démarrage."
    )


def test_le_wsgi_expose_bien_application(artefacts: Path) -> None:
    """`gunicorn wsgi:application` est la commande documentée : le nom compte."""
    arbre = ast.parse((artefacts / "wsgi.py").read_text(encoding="utf-8"))

    noms = {
        cible.id
        for noeud in arbre.body
        if isinstance(noeud, ast.Assign)
        for cible in noeud.targets
        if isinstance(cible, ast.Name)
    }

    assert "application" in noms, (
        f"le wsgi engendré ne définit pas `application` : {sorted(noms)}. "
        "La commande documentée `gunicorn wsgi:application` échouerait."
    )


# ── L'unité systemd, soumise à systemd ───────────────────────────────────────


def test_l_unite_systemd_est_acceptee_par_systemd(artefacts: Path) -> None:
    """Soumise à l'outil qui la lira, plutôt que fouillée à la recherche de mots.

    Le code de retour est inutilisable : `systemd-analyze verify` sort en 0
    même sur une unité qu'il refuse. C'est son texte qui porte le verdict.
    """
    if shutil.which("systemd-analyze") is None:
        pytest.skip("systemd-analyze absent : l'unité ne peut pas être soumise à systemd")

    resultat = subprocess.run(
        ["systemd-analyze", "verify", str(artefacts / "deploy/systemd/forge-app.service")],
        capture_output=True, text=True, timeout=120,
    )
    sortie = resultat.stdout + resultat.stderr

    plaintes = [
        ligne for ligne in sortie.splitlines()
        if any(motif in ligne for motif in _PLAINTES_DE_STRUCTURE)
        and _REMARQUE_D_ENVIRONNEMENT not in ligne
    ]

    assert not plaintes, (
        "systemd refuse l'unité engendrée :\n  " + "\n  ".join(plaintes)
    )


# ── La configuration Nginx, faute d'outil ────────────────────────────────────


def test_la_conf_nginx_a_la_forme_attendue(artefacts: Path) -> None:
    """Limite déclarée : `nginx` n'est pas installé, le contrôle reste formel.

    Ce test ne vaut donc pas les précédents, et il vaut mieux le dire que de
    laisser croire à une couverture équivalente. Installer `nginx` permettrait
    `nginx -t -c <fichier>`, seule vérification qui aurait la même force que
    celle de l'unité systemd.
    """
    conf = (artefacts / "deploy/nginx/forge-app.conf").read_text(encoding="utf-8")

    # Les accolades équilibrées écartent au moins un gabarit tronqué, ce qu'une
    # recherche de sous-chaîne ne fait pas.
    assert conf.count("{") == conf.count("}"), (
        "accolades déséquilibrées dans la configuration Nginx : gabarit tronqué"
    )
    assert conf.count("{") >= 2, "configuration Nginx anormalement plate"
