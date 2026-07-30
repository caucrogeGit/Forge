"""RELEASE-SMOKE-INSTALL-PATH-001 : le smoke d'installation fume ce qu'on publie.

Le script pointait `cli/skeleton/data/requirements.txt`. Le squelette vit à la
racine depuis l'ADR-065 : le smoke échouait donc dès sa première vérification,
sans jamais rien fumer, et personne ne le voyait puisqu'il n'est pas dans la
suite de tests.

Réparé, il a immédiatement révélé ce qu'il existait pour révéler.

- Il installait la wheel **par son nom** avec `--find-links`. À numéro égal,
  pip pouvait donc préférer la version déjà publiée sur PyPI : le smoke fumait
  la rc2 du mois précédent au lieu de la version en préparation. Le projet
  généré naissait alors avec un backend BDD épinglé, que l'ADR-060 interdit.
- Il ne construisait que le cœur. Les opt-ins que le squelette nomme sont
  **documentés en commentaire** depuis l'ADR-060 et l'ADR-070, et la lecture ne
  retenait que les lignes épinglées : le premier geste du parcours documenté,
  `pip install forge-mvc-<...>`, n'était jamais éprouvé.

Ce garde-fou fige ce qui ne doit pas repourrir : un chemin qui existe, des
wheels désignées par leur chemin, et le parcours documenté réellement installé.
Il ne remplace pas l'exécution du script, qui reste manuelle et longue.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = PROJECT_ROOT / "tools" / "smoke-install.sh"


@pytest.fixture(scope="module")
def source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_le_script_existe() -> None:
    assert SCRIPT.is_file()


def test_le_chemin_du_squelette_existe_vraiment(source: str) -> None:
    """Le défaut d'origine : un chemin qui ne désignait plus rien."""
    chemins = re.findall(r'SKEL_REQ="([^"]+)"', source)

    assert chemins, "le script ne nomme plus de requirements de squelette"
    for chemin in chemins:
        assert (PROJECT_ROOT / chemin).is_file(), (
            f"{chemin} n'existe pas : le squelette a bougé sans que le smoke suive"
        )


def test_le_squelette_est_bien_celui_de_la_racine() -> None:
    """ADR-065 : le squelette est un paquet à la racine, plus sous `cli/`."""
    assert (PROJECT_ROOT / "skeleton" / "data" / "requirements.txt").is_file()
    assert not (PROJECT_ROOT / "cli" / "skeleton").exists()


def test_les_wheels_sont_designees_par_leur_chemin(source: str) -> None:
    """Par leur nom, pip pouvait préférer la version publiée à la version locale."""
    assert "CORE_WHL=" in source
    assert 'install -q "$CORE_WHL"' in source
    assert '--find-links "$WHEELHOUSE" "forge-mvc==$VERSION"' not in source, (
        "installation par nom : le smoke peut fumer la version déjà publiée"
    )


def test_l_arbre_de_construction_est_nettoye(source: str) -> None:
    """`--no-isolation` réutilise `build/`, où un fichier supprimé survit."""
    assert 'rm -rf "$REPO_ROOT/build"' in source


def test_les_optins_documentes_sont_releves(source: str) -> None:
    """Ne lire que les lignes épinglées revenait à ne fumer que le cœur."""
    assert "grep -oE 'forge-mvc-[a-z0-9-]+'" in source
    assert "^forge-mvc-" not in source, "l'ancrage en début de ligne rate les commentaires"


def test_le_releve_du_squelette_nomme_bien_des_optins() -> None:
    """Si le squelette cesse de les nommer, le smoke doit le dire, pas se taire."""
    texte = (PROJECT_ROOT / "skeleton" / "data" / "requirements.txt").read_text(
        encoding="utf-8")

    assert set(re.findall(r"forge-mvc-[a-z0-9-]+", texte)), (
        "le squelette ne documente plus aucun opt-in : revoir le smoke"
    )


def test_le_script_verifie_l_origine_du_projet_genere(source: str) -> None:
    """Sans ce contrôle, une wheel publiée se glissait dans la résolution."""
    assert "vient d'une autre version de Forge" in source


def test_un_seul_backend_est_installe(source: str) -> None:
    """ADR-054 : les backends sont exclusifs, les empiler casse la résolution."""
    assert "forge-mvc-mariadb|forge-mvc-postgres|forge-mvc-mssql" in source
    assert "--dry-run" in source
