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


# ── La signature, et non le seul nom ─────────────────────────────────────────

def test_un_appel_conforme_passe() -> None:
    """Le symbole existe et l'appel se lie : rien à signaler."""
    modules = {"require_contract_permission": "forge_mvc_rbac"}

    assert garde.verdict_appel(modules, "require_contract_permission", 3, []) is None


def test_un_argument_manquant_est_refuse() -> None:
    """Cas mesuré : `verify_mfa_challenge(request, code=…)` sans `factors`."""
    modules = {"verify_mfa_challenge": "forge_mvc_mfa"}

    souci = garde.verdict_appel(modules, "verify_mfa_challenge", 1, ["code"])

    assert souci is not None
    assert "factors" in souci


def test_un_mot_cle_inexistant_est_refuse() -> None:
    """Cas mesuré : `start_mfa_challenge(request, user_id=…)`."""
    modules = {"start_mfa_challenge": "forge_mvc_mfa"}

    souci = garde.verdict_appel(modules, "start_mfa_challenge", 1, ["user_id"])

    assert souci is not None


def test_trop_de_positionnels_est_refuse() -> None:
    """Cas mesuré : `attach_media_to_entity(saved, "article", 7, …)`, dont les
    deux derniers paramètres sont réservés aux mots-clés."""
    modules = {"attach_media_to_entity": "forge_mvc_images"}

    souci = garde.verdict_appel(modules, "attach_media_to_entity", 3, ["role"])

    assert souci is not None
    assert "positional" in souci or "positionnel" in souci


def test_un_symbole_non_importe_dans_le_bloc_est_ignore() -> None:
    """Sans import dans le bloc, on ne sait pas de quoi parle le nom."""
    assert garde.verdict_appel({}, "peu_importe", 3, []) is None


def test_les_appels_du_bloc_sont_releves() -> None:
    code = ("from forge_mvc_mfa import start_mfa_challenge\n"
            "start_mfa_challenge(request, user)\n")

    releves = garde.appels_forge(code)

    assert [(nom, mots, etoile) for _l, nom, mots, etoile in releves] == \
        [("start_mfa_challenge", [], False)]


def test_un_appel_a_arguments_etoiles_est_marque() -> None:
    """`f(*args)` ne se lie pas : le marquer évite un refus arbitraire."""
    code = ("from forge_mvc_mfa import start_mfa_challenge\n"
            "start_mfa_challenge(*args)\n")

    assert garde.appels_forge(code)[0][3] is True


# ── Le périmètre du garde, mesuré et non supposé ─────────────────────────────

@pytest.mark.parametrize(("racine", "motif"), [
    ("core", "core/**/docs/**/*.md"),
    ("cli", "cli/**/docs/**/*.md"),
    ("packages", "packages/*/docs/**/*.md"),
])
def test_aucune_page_embarquee_n_echappe_au_controle(racine: str, motif: str) -> None:
    """Un garde n'est fiable que sur le périmètre qu'on lui a donné.

    Le motif était `core/*/docs`, à une seule étoile : il attrapait les treize
    `core/<module>/docs` et manquait `core/docs`, situé un niveau au-dessus.
    `core/docs/forge_config.md` échappait donc au contrôle, sans que rien ne le
    signale. Ce test mesure le périmètre au lieu de le supposer.
    """
    balayees = {p.relative_to(PROJECT_ROOT) for p in garde.pages(None)}
    toutes = {p for p in PROJECT_ROOT.glob(motif) if "history" not in p.parts}
    manquantes = sorted(p.relative_to(PROJECT_ROOT) for p in toutes
                        if p.relative_to(PROJECT_ROOT) not in balayees)

    assert not manquantes, (
        f"pages {racine} hors du balayage : {', '.join(str(p) for p in manquantes)}")


def test_la_page_qui_manquait_est_desormais_lue() -> None:
    """Le cas mesuré, nommé pour qu'un motif rétréci le fasse échouer."""
    balayees = {p.relative_to(PROJECT_ROOT) for p in garde.pages(None)}

    assert Path("core/docs/forge_config.md") in balayees
