"""DOC-CITED-PATHS-001 : un chemin cité en prose désigne un fichier qui existe.

`mkdocs build --strict` vérifie les liens Markdown. Il ne voit pas un chemin
écrit en prose entre dos-de-chat, comme `` `docs/reference.md` ``. C'est
exactement par là que la dérive est passée.

L'ADR-039 a refondu `docs/`, et le ticket `DOCS-REFERENCE-SPLIT-001` a découpé
`docs/reference.md` en onze fichiers. Le monolithe a continué d'être cité par le
contrat de stabilité, la politique de release et la politique de dépréciation,
soit les trois documents les plus engageants du projet. Un lecteur qui suivait
la référence pour savoir où sont documentées les clés d'environnement ou les
commandes CLI garanties tombait sur un fichier absent.

Vingt chemins morts au premier passage, sur les seules pages qu'un lecteur suit.

Ce garde ne juge pas les archives. Un ADR, une entrée de roadmap ou un ticket de
campagne enregistrent ce qui était vrai à leur date, et corriger leurs chemins
réécrirait la décision ou le compte rendu qu'ils conservent.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

#: Chemin de fichier du dépôt, cité entre dos-de-chat dans la prose.
CHEMIN_CITE = re.compile(
    r"`((?:docs|core|cli|packages|tests|skeleton)/[\w./-]+\.(?:md|py|json|toml|yml))`")

#: Répertoires qui enregistrent un état passé, et qu'on ne corrige donc pas.
#:
#: - `history` : mémoire brute, conservée telle quelle ;
#: - `adr` : une décision décrit le dépôt au jour où elle a été prise ;
#: - `roadmap` : le compte rendu d'un ticket cite les fichiers qu'il a touchés,
#:   y compris ceux qu'il a supprimés ;
#: - `tickets` : campagnes de test terrain, spécifications datées.
ARCHIVES = ("history", "adr", "roadmap", "tickets")

#: Exemptions nominatives, chacune avec son motif.
#:
#: - `docs/contributing/conventions.md` cite `docs/reference.md` pour raconter
#:   son propre découpage, et recommande d'exporter une constante depuis un
#:   `tests/conftest.py` qui reste à créer. L'une est un récit, l'autre une
#:   consigne : ni l'une ni l'autre ne prétend décrire un fichier présent.
#: - `docs/features/agents.md` parle de l'ADR d'une **application** engendrée
#:   par Forge, pas d'un ADR du dépôt Forge.
EXEMPTIONS = {
    "docs/contributing/conventions.md": {"docs/reference.md", "tests/conftest.py"},
    "docs/features/agents.md": {"docs/adr/001-adopter-forge.md"},
}


def _pages() -> "list[Path]":
    return sorted(p for p in PROJECT_ROOT.glob("docs/**/*.md")
                  if not any(x in p.parts for x in ARCHIVES))


# ── Le cas mesuré ────────────────────────────────────────────────────────────

def test_aucun_chemin_cite_ne_designe_un_fichier_absent() -> None:
    """Vingt chemins morts au premier passage, dont sept dans les documents de release."""
    morts: "list[str]" = []
    for page in _pages():
        relative = page.relative_to(PROJECT_ROOT).as_posix()
        exemptes = EXEMPTIONS.get(relative, set())
        for numero, ligne in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            for chemin in CHEMIN_CITE.findall(ligne):
                if chemin in exemptes:
                    continue
                if not (PROJECT_ROOT / chemin).exists():
                    morts.append(f"{relative}:{numero} — {chemin}")

    assert not morts, (
        "chemins cités en prose qui ne désignent aucun fichier :\n  "
        + "\n  ".join(morts))


# ── Le contrat nomme des classes qui existent ────────────────────────────────

def test_le_contrat_de_stabilite_nomme_des_stores_reels() -> None:
    """Il garantissait `MariaDbStore` et `FileStore`, absents tous deux du code.

    Les vrais noms sont `FileSessionStore` (cœur) et `DbSessionStore`
    (`forge-mvc-sessions-db`). Un contrat qui garantit une classe inexistante ne
    garantit rien, et personne ne peut le constater en le lisant.
    """
    contrat = (PROJECT_ROOT / "docs" / "release" / "stability-contract.md").read_text(
        encoding="utf-8")

    for fantome in ("MariaDbStore", "FileStore"):
        assert fantome not in contrat, (
            f"le contrat de stabilité nomme `{fantome}`, absent du code")
    for reel in ("FileSessionStore", "DbSessionStore"):
        assert reel in contrat


def test_les_stores_nommes_par_le_contrat_existent_vraiment() -> None:
    """Contre-épreuve : sans elle, on pourrait y écrire n'importe quel nom."""
    sources = "\n".join(
        p.read_text(encoding="utf-8")
        for p in list((PROJECT_ROOT / "core" / "sessions").glob("*.py"))
        + list((PROJECT_ROOT / "packages" / "forge-mvc-sessions-db").rglob("*.py")))

    assert "class FileSessionStore" in sources
    assert "class DbSessionStore" in sources


# ── Le contrat ne se contredit pas sur leur statut ───────────────────────────

def test_le_statut_des_stores_suit_la_source_unique() -> None:
    """Le contrat les disait `API stable` et, plus bas, non garantis.

    `release-policy.md` fait foi sur la maturité, le contrat le dit lui-même.
    Elle les classe en expérimental, donc le contrat aussi.
    """
    politique = (PROJECT_ROOT / "docs" / "release" / "release-policy.md").read_text(
        encoding="utf-8")
    experimental = politique[politique.index("### Expérimental"):]
    borne = experimental.find("\n## ")
    if borne != -1:
        experimental = experimental[:borne]

    assert "FileSessionStore" in experimental
    assert "DbSessionStore" in experimental

    contrat = (PROJECT_ROOT / "docs" / "release" / "stability-contract.md").read_text(
        encoding="utf-8")
    ligne = next(l for l in contrat.splitlines() if "FileSessionStore" in l and "|" in l)

    assert "Expérimental" in ligne


def test_les_exemptions_disent_pourquoi() -> None:
    """Une exemption sans motif écrit se transforme en trou silencieux."""
    source = Path(__file__).read_text(encoding="utf-8")
    bloc = source[source.index("#: Exemptions nominatives"):source.index("EXEMPTIONS = {")]

    for page in EXEMPTIONS:
        assert page in bloc
