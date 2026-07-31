"""WELCOME-EXECUTION-001 : un parcours d'accueil se vérifie en le jouant.

Lire un parcours ne dit pas s'il marche. Mesuré sur le plus simple des
vingt-sept, SQLite, trois manques dans les deux premiers paliers, dont aucun
n'était visible à la relecture.

- Le moteur d'entités n'était pas cité, alors que `db:init` en vient.
- `db:config` manquait, si bien que le backend ignorait quel fichier ouvrir.
- `make:crud` était donné seul, alors qu'il consomme une entité que seul
  `make:entity` crée.

Chaque commande était juste prise isolément : le manque n'existait qu'entre
elles, et seul un lecteur qui suit tout dans l'ordre pouvait le rencontrer.
C'est exactement ce que `tools/run_welcome_parcours.py` fait à sa place.

L'ordre suivi est celui du `nav` de `mkdocs.yml`, qui fait autorité et que le
lecteur voit dans le menu. La convention « Palier suivant » ne pouvait pas
servir : elle ne couvre que 21 des 316 pages de parcours.

Ces tests éprouvent la logique du harnais, pas les parcours eux-mêmes : jouer un
parcours demande un projet Forge réel, plusieurs minutes et le réseau, ce qui
n'a pas sa place dans la suite.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools import run_welcome_parcours as harnais

# Boucle documentaire : ce garde lit des parcours et un `nav`, et la dérive
# qu'il attrape naît d'une édition de la documentation. Contrairement au garde
# d'adéquation (DOC-CODE-ADEQUATION-001), qui part d'un symbole renommé et
# appartient donc à la boucle code.
pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ── L'ordre vient du menu du site ────────────────────────────────────────────

def test_l_ordre_est_celui_du_nav() -> None:
    pages = harnais.nav_welcome("sqlite")

    assert pages, "aucune page de parcours trouvée pour sqlite"
    assert pages[0].name == "sqlite-welcome.md", "le premier palier n'est pas premier"
    assert all(p.is_file() for p in pages)


def test_chaque_paquet_declare_ses_parcours_dans_son_nav() -> None:
    """Un parcours absent du nav n'est ni lisible ni vérifiable."""
    manquants: "list[str]" = []
    for dossier in sorted(PROJECT_ROOT.glob("packages/forge-mvc-*/docs/welcome")):
        court = dossier.parent.parent.name.removeprefix("forge-mvc-")
        if not harnais.nav_welcome(court):
            manquants.append(court)

    assert not manquants, f"parcours absents du nav : {', '.join(manquants)}"


# ── Ce qui est sauté est déclaré et compté ───────────────────────────────────

@pytest.mark.parametrize(("script", "raison"), [
    ("forge migration:make <nom>", "PLACEHOLDER"),
    ("forge run", "BLOQUANT"),
    ("mkdocs serve", "BLOQUANT"),
    ("$EDITOR mvc/entities/article/article.json", "MANUEL"),
    ("forge db:init", None),
    ("pip install --pre forge-mvc-sqlite", None),
])
def test_les_raisons_de_sauter_sont_reconnues(script: str, raison: "str | None") -> None:
    assert harnais.raison_de_sauter(script) == raison


def test_un_bloc_saute_n_est_jamais_tu(capsys: pytest.CaptureFixture[str]) -> None:
    """Un harnais qui tait ce qu'il n'a pas fait se lit comme une couverture
    complète (principe 3)."""
    harnais.parcourir("sqlite", None, lister=True)
    sortie = capsys.readouterr().out

    assert "Blocs joués" in sortie
    assert "rien n'a été exécuté" in sortie


# ── L'extraction des blocs ───────────────────────────────────────────────────

def test_seuls_les_blocs_bash_sont_joues() -> None:
    """Les blocs `python` sont du code que le lecteur pose dans un fichier,
    et les blocs `sql` sont des requêtes à lire."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-sqlite" / "docs" / "welcome"
            / "intermediaire" / "sqlite-inspect.md")

    for _ligne, script in harnais.blocs(page):
        assert "SELECT" not in script.upper() or "forge" in script, (
            "un bloc sql a été pris pour un bloc bash"
        )


def test_le_numero_de_ligne_designe_le_bloc() -> None:
    """Sans lui, un échec renvoie à une page de cent lignes."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-sqlite" / "docs" / "welcome"
            / "debutant" / "sqlite-welcome.md")
    lignes = page.read_text(encoding="utf-8").splitlines()

    for numero, _script in harnais.blocs(page):
        assert lignes[numero - 1].startswith("```bash")


# ── Le parcours pilote, corrigé ──────────────────────────────────────────────

def test_le_parcours_sqlite_cite_ses_deux_prerequis() -> None:
    """Le backend seul ne suffit pas : `db:init` vient du moteur d'entités."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-sqlite" / "docs" / "welcome"
            / "debutant" / "sqlite-welcome.md").read_text(encoding="utf-8")

    assert "forge-mvc-entities" in page
    assert "forge db:config" in page


def test_le_parcours_sqlite_declare_l_entite_avant_son_crud() -> None:
    """`make:crud` consomme un contrat que seul `make:entity` crée."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-sqlite" / "docs" / "welcome"
            / "debutant" / "sqlite-apply.md").read_text(encoding="utf-8")

    assert page.index("make:entity") < page.index("make:crud")
