"""DOC-CODE-ADEQUATION-001 : la documentation nomme-t-elle du code qui existe.

Une page qui montre `from forge_mvc_x import Y` promet que `Y` s'importe, et une
qui écrit `forge machin:truc` promet que la commande existe. Rien ne le
vérifiait, et le seul retour possible était celui d'un lecteur qui essaie.

Forge a beaucoup renommé, extrait et supprimé depuis la 0.x, et la documentation
suit à la main. L'ADR-035 exigeait d'ailleurs déjà, à sa liste de suites, de
« vérifier chaque parcours de bout en bout ».

Ce garde ne juge pas le sens, seulement l'existence : c'est le minimum qu'une
documentation doive à son lecteur, et c'est vérifiable sans ambiguïté.

Ce test appartient à la boucle **code**, délibérément, et ne porte donc pas le
marqueur `docs`. La dérive qu'il attrape naît le plus souvent d'un changement de
code, un symbole renommé ou une commande retirée, et un garde qui ne se
réveillerait qu'en modifiant la documentation la manquerait toujours.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.database.errors import DatabaseConfigurationError  # symbole réel, cf. plus bas
from tools import check_docs_symbols as garde

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ── Le verdict sur un symbole ────────────────────────────────────────────────

def test_un_symbole_existant_passe() -> None:
    assert DatabaseConfigurationError is not None  # il existe vraiment
    assert garde.verdict("core.database.errors", "DatabaseConfigurationError") is None


def test_un_symbole_absent_est_refuse() -> None:
    assert garde.verdict("core.database.errors", "ErreurQuiNExistePas") is not None


def test_un_module_absent_est_refuse() -> None:
    souci = garde.verdict("core.ce_module_nexiste_pas", "Truc")

    assert souci is not None
    assert "INTROUVABLE" in souci


def test_un_sous_module_n_est_pas_pris_pour_un_symbole_absent() -> None:
    """`from core.database import db` vise un sous-module, pas un attribut.

    Conclure sur le seul `hasattr` refusait des imports valides : ce garde a
    commencé par se tromper ainsi sur deux pages de fixtures.
    """
    assert garde.verdict("core.database", "db") is None


# ── L'extraction ─────────────────────────────────────────────────────────────

def test_les_imports_applicatifs_sont_hors_de_portee() -> None:
    """`mvc.*` appartient au projet du lecteur et n'existe pas dans ce dépôt."""
    couples = garde.imports_forge(
        "from mvc.models.article_model import list_articles\n"
        "from core.database import db\n"
    )

    assert couples == [("core.database", "db")]


def test_un_fragment_non_parsable_ne_fait_pas_echouer() -> None:
    """La documentation montre souvent des fragments : les refuser noierait le signal."""
    assert garde.imports_forge("    def ma_methode(self):\n        return 1") == []


@pytest.mark.parametrize(("script", "attendu"), [
    ("forge db:init", ["db:init"]),
    ("forge db:init --run", ["db:init"]),
    ("./.venv/bin/forge doctor", ["doctor"]),
    ("cd projet && forge make:entity Article", ["make:entity"]),
    ("pip install forge-mvc-sqlite", []),
])
def test_les_appels_de_commande_sont_reconnus(script: str, attendu: "list[str]") -> None:
    assert garde.APPEL_FORGE.findall(script) == attendu


# ── Les exclusions, et leur motif ────────────────────────────────────────────

def test_les_archives_sont_hors_de_portee() -> None:
    """`docs/history/` conserve à dessein du code supprimé."""
    assert not any("history" in page.parts for page in garde.pages(None))


def test_un_adr_remplace_est_hors_de_portee() -> None:
    """Il doit continuer de montrer ce qu'il a fait adopter, sans quoi on
    réécrirait la décision qu'il enregistre."""
    remplace = PROJECT_ROOT / "docs" / "adr" / "023-starter-build-canonical.md"

    assert remplace.is_file()
    assert garde._adr_remplace(remplace), (
        "l'ADR-023 doit déclarer son remplacement par l'ADR-035 dans son Statut"
    )
    assert remplace not in garde.pages(None)


def test_un_adr_en_vigueur_reste_sous_controle() -> None:
    """L'exclusion vise les ADR remplacés, pas la famille entière."""
    vigueur = PROJECT_ROOT / "docs" / "adr" / "035-starters-manual-not-generated.md"

    assert not garde._adr_remplace(vigueur)


def test_une_page_ne_s_exclut_qu_en_le_declarant() -> None:
    """Une liste de répertoires exclus se remplirait en silence (principe 3)."""
    source = (PROJECT_ROOT / "tools" / "check_docs_symbols.py").read_text(
        encoding="utf-8")

    assert garde.MARQUEUR_IGNORE in source
    assert "ignore" in garde.MARQUEUR_IGNORE


# ── Le verdict d'ensemble, sur la vraie documentation ────────────────────────

def test_toute_la_documentation_nomme_du_code_qui_existe(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Le garde lui-même, sur les 1192 imports et 619 commandes du dépôt."""
    code = garde.verifier(None, welcome_seul=False)
    sortie = capsys.readouterr().out

    assert code == 0, f"la documentation cite du code absent :\n{sortie}"


def test_les_parcours_d_accueil_en_particulier(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ce sont eux qu'un débutant suit à la lettre."""
    code = garde.verifier(None, welcome_seul=True)
    sortie = capsys.readouterr().out

    assert code == 0, f"un parcours d'accueil cite du code absent :\n{sortie}"
