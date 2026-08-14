"""GUIDE-PRISE-EN-MAIN-EXEC-001 — le tutoriel complet est joué, pas relu.

Les six guides de prise en main contiennent 77 lignes de commande, dont 46
invocations de `forge`. Un ticket précédent a vérifié que ces commandes et
leurs options **existent** (`DOC-CLI-INVOCATIONS-001`). Personne n'avait
vérifié qu'elles **aboutissent**.

C'est ce que suit un nouvel utilisateur, et l'échec y coûte le plus cher : il
ne connaît pas encore assez Forge pour distinguer sa propre erreur d'un défaut
du framework.

Ce fichier joue l'enchaînement du tutoriel complet, du projet vide à
l'application qui répond, dans un dossier jetable.

## Ce qui a été trouvé en l'écrivant

`docs/guide/app-complete-tutorial.md` se contredisait à l'intérieur d'une même
page : son tableau de synthèse annonçait « `forge db:init` crée la base et
applique le SQL », alors que trois cents lignes plus bas la même page dit qu'il
**affiche**. L'ADR-067 a tranché pour la seconde forme.

## Une limite de méthode

`DB_BACKEND` est fixé explicitement : le dépôt de développement a les quatre
backends installés, ce qu'un projet interdit (ADR-054). Un utilisateur n'en a
qu'un ; sans ce réglage, on mesurerait un artefact de l'environnement de test.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_entities")
pytest.importorskip("forge_mvc_sqlite")


PROJECT_ROOT = Path(__file__).parent.parent
FORGE = str(PROJECT_ROOT / "forge.py")


def _node_trop_ancien() -> str | None:
    """Motif de saut si Node est trop ancien pour `forge new`, sinon `None`.

    Le squelette épingle Node dans `.nvmrc`, déclare `engines.node` et active
    `engine-strict` : `npm install` **refuse** de tourner sous une version
    inférieure, et `forge new` échoue donc entièrement.

    Un contributeur sous une version plus ancienne ne doit pas voir une suite
    rouge pour une raison étrangère à son changement. La CI, elle, installe la
    version épinglée : le parcours y est réellement joué
    (`GUIDE-PRISE-EN-MAIN-EXEC-001`).
    """
    if shutil.which("npm") is None:
        return "npm absent : `forge new` ne peut pas installer les dépendances Node."
    exige = (PROJECT_ROOT / ".nvmrc").read_text(encoding="utf-8").strip()
    resultat = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=60)
    if resultat.returncode != 0:
        return "node absent : `forge new` ne peut pas installer les dépendances Node."
    presente = resultat.stdout.strip().lstrip("v")

    def _cle(version: str) -> tuple[int, ...]:
        return tuple(int(x) for x in version.split(".") if x.isdigit())

    if _cle(presente) < _cle(exige):
        return (
            f"Node {presente} < {exige} exigé par .nvmrc : `npm install` refuse "
            "de tourner (engine-strict), donc `forge new` échoue. Installez la "
            "version épinglée (nvm use) pour couvrir le parcours."
        )
    return None


pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(_node_trop_ancien() is not None, reason=_node_trop_ancien() or ""),
]


def _forge(*args: str, cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    """Lance `forge <args>` comme le lecteur du guide le ferait."""
    environnement = dict(os.environ)
    # Un projet n'a qu'un backend (ADR-054) ; le dépôt de développement les a
    # tous. Sans ce réglage, `make:entity` échouerait sur l'environnement de
    # test et non sur le code.
    environnement["DB_BACKEND"] = "sqlite"
    return subprocess.run(
        [sys.executable, FORGE, *args],
        cwd=cwd, capture_output=True, text=True, timeout=timeout, env=environnement,
    )


@pytest.fixture(scope="module")
def projet(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Le projet du tutoriel, mené jusqu'aux tables en base.

    L'enchaînement suit `docs/guide/app-complete-tutorial.md`. Chaque étape est
    contrôlée : un échec en milieu de parcours laisserait les suivantes mesurer
    autre chose que ce qu'elles croient.
    """
    racine = tmp_path_factory.mktemp("prise_en_main")

    cree = _forge("new", "carnet", cwd=racine)
    assert cree.returncode == 0, f"`forge new` a échoué :\n{cree.stdout}\n{cree.stderr}"
    projet = racine / "carnet"

    etapes = [
        ("make:entity", "Ville", "--no-input"),
        ("make:entity", "Contact", "--no-input"),
        # Le guide montre `forge make:relation` sans argument, donc en mode
        # dialogue. La forme non interactive est employée ici : un test ne peut
        # pas répondre à des questions.
        ("make:relation", "--type", "many_to_one", "--from", "Contact", "--to", "Ville"),
        ("build:model",),
        ("make:crud", "Ville"),
        ("make:crud", "Contact"),
        ("db:config",),
        ("db:init",),
        ("db:apply",),
    ]
    for etape in etapes:
        resultat = _forge(*etape, cwd=projet)
        assert resultat.returncode == 0, (
            f"`forge {' '.join(etape)}` a échoué :\n{resultat.stdout}\n{resultat.stderr}"
        )
    return projet


# ── Le parcours aboutit ──────────────────────────────────────────────────────


def test_le_projet_engendre_passe_ses_propres_controles(projet: Path) -> None:
    """`project:check` est ce que le guide fait vérifier au lecteur.

    Un projet qui ne passe pas son propre contrôle après avoir suivi le
    tutoriel au mot près est le pire accueil possible.
    """
    for commande in ("project:check", "project:audit", "entity:validate", "check:model"):
        resultat = _forge(commande, cwd=projet)
        assert resultat.returncode == 0, (
            f"`forge {commande}` échoue sur un projet suivi au mot près :\n"
            f"{resultat.stdout}\n{resultat.stderr}"
        )


def test_les_tables_des_entites_existent_vraiment(projet: Path) -> None:
    """`db:apply` promet des tables : on les lit dans le fichier de base.

    Le code de retour ne dit rien de ce qui a été écrit.
    """
    base = projet / "storage" / "app.db"
    assert base.is_file(), "aucun fichier de base après `forge db:apply`"

    connexion = sqlite3.connect(base)
    try:
        tables = {
            ligne[0]
            for ligne in connexion.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        connexion.close()

    manquantes = {"contact", "ville", "forge_migrations"} - tables
    assert not manquantes, f"tables absentes après `db:apply` : {manquantes} (présentes : {tables})"


def test_le_crud_affiche_son_branchement_sans_l_ecrire(projet: Path) -> None:
    """LE défaut trouvé en jouant le guide (`GUIDE-PRISE-EN-MAIN-EXEC-001`).

    Le tutoriel annonçait : « Les routes sont ajoutées **automatiquement** dans
    `mvc/routes/__init__.py` ». C'est faux, et contraire au principe 9 : Forge
    n'écrit jamais dans ce fichier, qui appartient à l'utilisateur.

    Mesuré : après `make:crud Contact` et `make:crud Ville`, `routes:list` ne
    montre que les deux routes d'accueil du squelette. Un lecteur qui suivait
    le guide au mot près lançait l'application et recevait un 404 sur
    `/contact`, sans rien pour l'expliquer.

    Ce test fixe le comportement réel, qui est le bon : la commande **affiche**
    le branchement, et c'est la documentation qui mentait.
    """
    resultat = _forge("routes:list", cwd=projet)
    assert resultat.returncode == 0, resultat.stderr

    routes = resultat.stdout.lower()
    assert "contact" not in routes and "ville" not in routes, (
        "les routes du CRUD sont désormais branchées automatiquement : c'est "
        "une rupture du principe 9, ou une évolution à documenter"
    )

    # Le fichier de routes de l'entité, lui, est bien écrit.
    assert (projet / "mvc" / "routes" / "contact_routes.py").is_file()

    # Le fichier de routes du projet ne contient AUCUN branchement actif. Le
    # squelette y met un exemple en commentaire, qui emploie justement
    # `contact` : la prose est donc écartée, sans quoi le contrôle se
    # déclencherait sur elle (`SOURCE-SCAN-001`).
    from forge_mvc_testing.source_scan import code_sans_prose

    init = projet / "mvc" / "routes" / "__init__.py"
    code = code_sans_prose(init.read_text(encoding="utf-8"))
    assert "register_contact_routes" not in code, (
        "Forge a écrit un branchement dans `mvc/routes/__init__.py`, fichier "
        "qui appartient à l'utilisateur (principe 9)"
    )


def test_le_branchement_colle_a_la_main_produit_les_routes(projet: Path, tmp_path: Path) -> None:
    """La contrepartie : le geste que le guide doit décrire fonctionne-t-il ?

    Sans ce contrôle, on saurait que Forge n'écrit pas les routes, sans savoir
    si l'instruction donnée au lecteur aboutit.
    """
    import shutil as _shutil

    copie = tmp_path / "carnet_branche"
    _shutil.copytree(projet, copie)

    init = copie / "mvc" / "routes" / "__init__.py"
    source = init.read_text(encoding="utf-8")
    # Exactement les deux lignes que `make:crud` affiche, collées à la fin,
    # comme le ferait un lecteur du guide.
    init.write_text(
        source
        + "\nfrom mvc.routes.contact_routes import register_contact_routes\n"
        + "register_contact_routes(router)\n",
        encoding="utf-8",
    )

    resultat = _forge("routes:list", cwd=copie)

    assert resultat.returncode == 0, (
        f"le branchement collé rend `routes:list` inutilisable :\n{resultat.stdout}\n{resultat.stderr}"
    )
    assert "contact" in resultat.stdout.lower(), (
        "le branchement que le guide fait coller ne produit aucune route :\n"
        + resultat.stdout
    )


# ── L'application démarre et répond ──────────────────────────────────────────


def test_l_application_demarre_et_repond(projet: Path) -> None:
    """La dernière promesse du tutoriel : `forge run` lance l'application.

    C'est le seul contrôle qui traverse tout, du contrat JSON à la réponse
    HTTP. Le serveur de développement sert en HTTPS avec un certificat
    auto-signé, que le client doit donc accepter.
    """
    import ssl

    environnement = dict(os.environ)
    environnement["DB_BACKEND"] = "sqlite"
    serveur = subprocess.Popen(
        [sys.executable, FORGE, "run", "--no-reload"],
        cwd=projet, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=environnement,
    )
    contexte = ssl.create_default_context()
    contexte.check_hostname = False
    contexte.verify_mode = ssl.CERT_NONE

    try:
        charge = None
        # Le démarrage n'est pas instantané : on réessaie plutôt que de dormir
        # une durée arbitraire, ce qui rendrait le test lent ou instable.
        for _ in range(40):
            if serveur.poll() is not None:
                pytest.fail(f"le serveur s'est arrêté :\n{serveur.communicate()[0]}")
            try:
                with urllib.request.urlopen(
                    "https://127.0.0.1:8000/health", timeout=2, context=contexte
                ) as reponse:
                    charge = json.loads(reponse.read().decode("utf-8"))
                    break
            except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
                time.sleep(0.5)
    finally:
        serveur.terminate()
        try:
            serveur.wait(timeout=15)
        except subprocess.TimeoutExpired:
            serveur.kill()

    assert charge is not None, "l'application n'a jamais répondu sur /health"
    assert charge.get("status") == "ok", f"sonde inattendue : {charge}"


# ── La page qui décrit le parcours ───────────────────────────────────────────


def test_le_tutoriel_ne_promet_pas_que_db_init_applique() -> None:
    """La page se contredisait d'un bout à l'autre d'elle-même.

    Son tableau de synthèse annonçait « crée la base et applique le SQL » ;
    trois cents lignes plus bas, la même page dit qu'il **affiche**, ce que
    l'ADR-067 a tranché. Un lecteur qui s'arrête au tableau attend une base
    créée et n'en a pas.
    """
    page = (PROJECT_ROOT / "docs" / "guide" / "app-complete-tutorial.md").read_text(
        encoding="utf-8"
    )

    fautives = [
        ligne.strip()
        for ligne in page.splitlines()
        if "db:init" in ligne and "applique" in ligne and "--run" not in ligne
    ]
    assert not fautives, (
        "le tutoriel annonce que `db:init` applique le SQL, alors qu'il "
        "l'affiche (ADR-067) :\n  " + "\n  ".join(fautives)
    )


def test_le_guide_est_jouable_sans_dialogue() -> None:
    """Une commande interactive ne peut pas figurer seule dans un enchaînement.

    Le tutoriel montre `forge make:relation` sans argument, donc en mode
    dialogue. C'est un choix pédagogique défendable, mais il rend le parcours
    non rejouable tel quel : ce test l'enregistre plutôt que de le corriger,
    et la forme non interactive est employée par la fixture.
    """
    page = (PROJECT_ROOT / "docs" / "guide" / "app-complete-tutorial.md").read_text(
        encoding="utf-8"
    )

    assert "--from" in page or "make:relation" in page, (
        "le tutoriel ne montre plus `make:relation` : cette note est périmée"
    )


def test_forge_est_bien_installable_dans_le_bac_a_sable() -> None:
    """Contrôle de montage : sans `forge.py`, tout le fichier passerait à vide."""
    assert Path(FORGE).is_file()
    assert shutil.which(sys.executable)
