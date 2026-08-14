"""WELCOME-PYTHON-EXECUTION-001 — les blocs du parcours sont joués, pas relus.

Le harnais `tools/run_welcome_parcours.py` joue les blocs `bash` d'un parcours
dans un vrai projet. Celui d'import/export n'en contient aucun, et pour une
bonne raison : cet opt-in s'utilise par import, sans commande CLI. Il ne portait
donc que des blocs `python`, qu'aucun outil ne pouvait exercer.

`tools/check_docs_symbols.py` couvrait déjà l'existence : les sept symboles
importés par le parcours existent, et les appels lient aux signatures réelles.
Ce qu'il ne dit pas, c'est si le code **tourne**. Un exemple peut nommer des
symboles réels et lever à la première ligne.

Ces tests exécutent chaque bloc. Le namespace est partagé au sein d'une page,
les paliers s'y enchaînant comme le lecteur les suit, et remis à neuf entre deux
pages, qui sont indépendantes.

Un bloc qui dépend de l'application du lecteur (`mvc.models.eleve`) ne peut pas
être joué ici sans fabriquer un projet : il est déclaré, avec son motif, plutôt
que silencieusement ignoré.
"""
from __future__ import annotations

import ast
import contextlib
import io
import re
from pathlib import Path

import pytest

PAQUET = Path(__file__).resolve().parent.parent
WELCOME = PAQUET / "docs" / "welcome"

#: Bloc `python` d'une page Markdown, y compris indenté dans un encart.
BLOC_PYTHON = re.compile(r"^([ \t]*)```python[ \t]*$(.*?)^\1```[ \t]*$", re.MULTILINE | re.DOTALL)

#: Racines de modules qui appartiennent au projet du lecteur, pas à l'opt-in.
#: Un bloc qui les importe décrit du code applicatif que ce parcours demande
#: d'écrire ; le jouer supposerait un projet généré, une base et une entité.
RACINES_APPLICATIVES = ("mvc", "config", "app")


def _blocs() -> "list[tuple[Path, int, int, str]]":
    """Rend (page, numéro de bloc, ligne, code) pour tout le parcours."""
    trouves: "list[tuple[Path, int, int, str]]" = []
    for page in sorted(WELCOME.rglob("*.md")):
        texte = page.read_text(encoding="utf-8")
        for numero, bloc in enumerate(BLOC_PYTHON.finditer(texte), 1):
            marge = bloc.group(1)
            code = "\n".join(
                ligne[len(marge):] if ligne.startswith(marge) else ligne
                for ligne in bloc.group(2).splitlines())
            ligne_no = texte[: bloc.start()].count("\n") + 1
            trouves.append((page, numero, ligne_no, code))
    return trouves


def _modules_importes(arbre: ast.Module) -> "set[str]":
    modules: "set[str]" = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.ImportFrom) and noeud.module:
            modules.add(noeud.module)
        elif isinstance(noeud, ast.Import):
            modules |= {alias.name for alias in noeud.names}
    return modules


def _depend_de_l_application(code: str) -> bool:
    return any(module.split(".")[0] in RACINES_APPLICATIVES
               for module in _modules_importes(ast.parse(code)))


BLOCS = _blocs()

#: Pages du parcours, dans l'ordre de lecture.
PAGES = sorted({page for page, _, _, _ in BLOCS})


# ── Le parcours a bien du contenu à vérifier ─────────────────────────────────

def test_le_parcours_porte_des_blocs() -> None:
    """Sans ce contrôle, un chemin faux rendrait tous les tests vides et verts."""
    assert len(BLOCS) >= 10, (
        f"{len(BLOCS)} bloc(s) trouvé(s) sous {WELCOME} : chemin probablement faux")


def test_les_blocs_bash_sont_joues_ailleurs() -> None:
    """Le motif de ce fichier, énoncé et vérifié.

    Ce fichier ne couvre que le **python** du parcours. Les blocs `bash` sont
    joués par `tools/run_welcome_parcours.py`, qui suit l'ordre du site.

    Le contrôle exigeait auparavant `bash == 0`. Le parcours a gagné son bloc
    d'installation, sans lequel un lecteur partait sur un `ModuleNotFoundError`
    (`WELCOME-PREREQUIS-ACTIONNABLE-001`). Exiger l'absence de bash revenait à
    interdire au parcours de dire comment l'installer.
    """
    bash = sum(page.read_text(encoding="utf-8").count("```bash") for page in PAGES)

    assert bash <= 2, (
        f"{bash} bloc(s) bash dans le parcours : au-delà du prérequis "
        "d'installation, ils relèvent de tools/run_welcome_parcours.py, et ce "
        "fichier cesserait d'être une couverture suffisante")


# ── Chaque bloc parse ────────────────────────────────────────────────────────

@pytest.mark.parametrize(("page", "numero", "ligne", "code"), BLOCS,
                         ids=[f"{p.parent.name}/{p.stem}#b{n}" for p, n, _, _ in BLOCS])
def test_le_bloc_est_du_python_valide(page: Path, numero: int, ligne: int, code: str) -> None:
    """Une coquille de frappe se voit ici, pas chez le lecteur."""
    try:
        ast.parse(code)
    except SyntaxError as erreur:
        pytest.fail(f"{page.name}:{ligne} bloc {numero} ne parse pas : {erreur.msg}")


# ── Chaque page se joue d'un bout à l'autre ──────────────────────────────────

@pytest.mark.parametrize("page", PAGES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_la_page_se_joue_du_debut_a_la_fin(page: Path) -> None:
    """Les blocs d'une page s'enchaînent dans un même espace de noms.

    C'est ainsi que le lecteur les suit : un palier pose des variables que le
    suivant réutilise. Les jouer isolément rendrait des `NameError` qui ne
    diraient rien du parcours.

    La sortie standard est captée : ces blocs impriment à dessein, et leur
    affichage n'a pas à polluer le rapport de tests.
    """
    espace: "dict[str, object]" = {}
    joues = 0
    declares = 0

    for autre_page, numero, ligne, code in BLOCS:
        if autre_page != page:
            continue
        if _depend_de_l_application(code):
            declares += 1
            continue
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(code, f"{page.name}#bloc{numero}", "exec"), espace)
        except Exception as erreur:  # noqa: BLE001 — on rapporte, quelle qu'elle soit
            pytest.fail(
                f"{page.relative_to(WELCOME).as_posix()}:{ligne} bloc {numero} "
                f"lève {type(erreur).__name__} : {erreur}")
        joues += 1

    assert joues or declares, f"{page.name} : aucun bloc traité"


# ── Ce qui n'est pas joué est déclaré ────────────────────────────────────────

def test_les_blocs_non_joues_sont_ceux_qui_touchent_l_application() -> None:
    """Un bloc écarté sans motif serait un trou silencieux.

    Le seul écarté aujourd'hui montre l'import dans une entité du lecteur. Le
    jouer supposerait un projet généré avec son entité et sa base, ce qui
    relève de `tools/run_welcome_parcours.py`, pas d'un test unitaire de paquet.
    """
    ecartes = [
        f"{page.relative_to(WELCOME).as_posix()}#b{numero}"
        for page, numero, _, code in BLOCS if _depend_de_l_application(code)
    ]

    assert ecartes == ["avance/import-independance.md#b1"], (
        f"la liste des blocs écartés a changé : {ecartes}. "
        f"Vérifier que chacun dépend bien du projet du lecteur, et non d'un "
        f"défaut du parcours.")
