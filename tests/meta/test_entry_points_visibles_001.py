"""PKG-ENTRY-POINTS-VISIBLES-001 — ce qu'un paquet déclare, l'exécution le voit.

Un entry point est le seul mécanisme par lequel le cœur découvre un opt-in :
backends BDD (ADR-054), commandes CLI (ADR-059), fournisseur de médias
(`CORE-WSGI-MEDIA-PARITY-001`). Il est déclaré dans le `pyproject.toml` du
paquet, et lu à l'exécution par `importlib.metadata`.

Entre les deux, il y a un piège, rencontré en ajoutant le groupe
`forge_mvc.media_server` :

`conftest.py` place chaque `packages/*` en TÊTE de `sys.path`, si bien que
`importlib.metadata` lit d'abord les `*.egg-info` du dépôt, avant les
métadonnées de l'installation. Ces `egg-info` sont des artefacts de build,
ignorés par git, et une installation éditable moderne (PEP 660) ne les
régénère pas : ils survivent donc aux modifications du `pyproject.toml`.

L'entry point était déclaré, installé, visible depuis un shell, et **invisible
sous pytest**. Rien ne le disait : un opt-in simplement pas découvert se
comporte comme un opt-in pas installé, c'est à dire en silence.

Ce garde-fou compare la déclaration à ce que l'exécution voit, et nomme le
geste de réparation. Il ne teste pas la documentation (règle D) : les deux
côtés sont des faits d'exécution.
"""
from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGES = PROJECT_ROOT / "packages"

#: Geste de réparation, cité dans les échecs pour qu'ils soient actionnables.
REGENERER = (
    "Régénérer les métadonnées du paquet :\n"
    "    cd packages/<paquet> && python -c \"from setuptools import setup; "
    "import sys; sys.argv=['setup.py','egg_info','-q']; setup()\"\n"
    "ou réinstaller : pip install -e ./packages/<paquet> --no-deps"
)


def _pyprojects() -> list[Path]:
    fichiers = sorted(PACKAGES.glob("*/pyproject.toml"))
    assert fichiers, "aucun paquet trouvé sous packages/"
    return [PROJECT_ROOT / "pyproject.toml", *fichiers]


def _declares(pyproject: Path) -> tuple[str, set[tuple[str, str, str]]]:
    """(nom de distribution, entry points déclarés) lus sur la source versionnée."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    projet = data["project"]
    groupes = projet.get("entry-points", {}) or {}
    declares = {
        (groupe, cle, valeur)
        for groupe, entrees in groupes.items()
        for cle, valeur in entrees.items()
    }
    return projet["name"], declares


def _vus(nom: str) -> "set[tuple[str, str, str]] | None":
    """Entry points vus à l'exécution, ou `None` si le paquet n'est pas installé."""
    try:
        dist = distribution(nom)
    except PackageNotFoundError:
        return None
    return {(e.group, e.name, e.value) for e in dist.entry_points}


@pytest.mark.parametrize(
    "pyproject", _pyprojects(), ids=lambda p: p.parent.name,
)
def test_les_entry_points_declares_sont_vus(pyproject: Path) -> None:
    """Le cas mesuré : un entry point ajouté au pyproject, invisible des tests."""
    nom, declares = _declares(pyproject)
    if not declares:
        pytest.skip(f"{nom} ne déclare aucun entry point")

    vus = _vus(nom)
    if vus is None:
        pytest.skip(f"{nom} n'est pas installé dans cet environnement")

    manquants = declares - vus
    assert not manquants, (
        f"{nom} déclare des entry points que l'exécution ne voit pas :\n"
        + "\n".join(f"    [{g}] {k} = {v}" for g, k, v in sorted(manquants))
        + f"\n\nLe cœur ne découvrira pas cet opt-in, en silence.\n{REGENERER}"
    )


@pytest.mark.parametrize(
    "pyproject", _pyprojects(), ids=lambda p: p.parent.name,
)
def test_aucun_entry_point_fantome(pyproject: Path) -> None:
    """Le symétrique : un entry point retiré du pyproject mais toujours servi.

    Il ferait charger un module supprimé, et l'échec surviendrait à la
    résolution, loin de sa cause.
    """
    nom, declares = _declares(pyproject)
    vus = _vus(nom)
    if vus is None:
        pytest.skip(f"{nom} n'est pas installé dans cet environnement")

    # Seuls les groupes de Forge sont de notre ressort : `console_scripts` et
    # les groupes d'outillage tiers ne sont pas décrits par ce pyproject.
    fantomes = {
        (g, k, v) for (g, k, v) in vus - declares if g.startswith("forge_mvc")
    }
    assert not fantomes, (
        f"{nom} sert des entry points absents de son pyproject.toml :\n"
        + "\n".join(f"    [{g}] {k} = {v}" for g, k, v in sorted(fantomes))
        + f"\n\nMétadonnées périmées : le cœur découvrirait un opt-in retiré.\n{REGENERER}"
    )


def test_le_code_importe_vient_du_depot() -> None:
    """Un paquet servi depuis une copie installée testerait autre chose que le dépôt.

    Rencontré : `forge-mvc-files` était installé en copie figée d'une version
    antérieure. Le code était identique, donc rien ne mentait ce jour là, mais
    la suite validait une copie et non la source.
    """
    import importlib.util

    copies: list[str] = []
    for pyproject in sorted(PACKAGES.glob("*/pyproject.toml")):
        dossier = pyproject.parent
        nom = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["name"]
        module = nom.replace("-", "_")
        if not (dossier / module).is_dir():
            continue
        try:
            spec = importlib.util.find_spec(module)
        except (ImportError, ValueError):
            continue
        if spec is None or not spec.origin:
            continue
        if str(PACKAGES) not in str(spec.origin):
            copies.append(f"{nom} → {spec.origin}")

    assert not copies, (
        "des paquets sont importés depuis une COPIE installée, pas depuis le dépôt :\n"
        + "\n".join(f"    {c}" for c in copies)
        + "\n\nLa suite validerait cette copie. Réinstaller en éditable :\n"
        "    pip install -r requirements-dev.txt"
    )
