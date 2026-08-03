"""DOC-COMMAND-BEHAVIOUR-001 : la doc n'affirme pas ce que l'aide contredit.

Trois ADR récents ont changé le comportement de commandes centrales, et la
documentation a continué de décrire l'ancien pendant des mois.

L'ADR-067 est le cas le plus coûteux. `forge db:init` **affiche** le SQL de
provisioning et n'exécute qu'avec `--run` ; sept pages continuaient d'écrire
qu'il « crée la base », « se connecte en tant que forge_admin », voire citaient
un message d'erreur que le code ne produit plus. Un lecteur croyait sa base
provisionnée alors que rien n'avait tourné, et cherchait la cause d'une panne
impossible.

Ce garde compare la documentation à **l'aide de la commande**, pas à une liste
écrite ici : si l'aide dit que la commande affiche par défaut, une page ne peut
pas affirmer qu'elle crée sans nommer `--run`.

Il est volontairement **étroit**. Sa première version relevait dix phrases dont
la moitié étaient justes : une négation (« ne se connecte pas »), une
comparaison (« à la manière de db:init, qui affiche »), et le cas SQLite, où
`db:init` crée réellement le fichier puisqu'il n'y a pas de serveur. Un garde
qui crie à tort finit désactivé.

Les exemptions sont donc explicites et motivées, et le garde ne juge que les
phrases qui affirment une création **sans** aucune de ces marques.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

#: Phrase mentionnant la commande, bornée aux points et aux fins de ligne.
PHRASE_DB_INIT = re.compile(r"[^.\n]*`?forge db:init`?[^.\n]*\.")

#: Affirmation d'une création de base ou de compte.
CREATION = re.compile(r"\b(cr[ée]e|se connecte)\b", re.IGNORECASE)

#: Marques qui rendent la phrase juste, et qu'il faut donc laisser passer.
#:
#: - `--run` : la phrase parle bien du mode qui exécute ;
#: - `affiche`, `génère` : elle décrit le comportement par défaut ;
#: - `ne se connecte pas`, `ne crée` : c'est une négation ;
#: - `SQLite`, `sans serveur`, `fichier` : sur un backend sans serveur, `db:init`
#:   crée réellement, n'ayant ni serveur à joindre ni compte à créer.
EXEMPTIONS = ("--run", "affiche", "génère", "ne se connecte pas", "ne crée",
              "sqlite", "sans serveur", "fichier")


def _pages() -> "list[Path]":
    trouvees: "list[Path]" = []
    for motif in ("docs/**/*.md", "packages/*/docs/**/*.md",
                  "core/**/docs/**/*.md", "cli/**/docs/**/*.md"):
        trouvees += [p for p in PROJECT_ROOT.glob(motif)
                     # `docs/history/` et `docs/adr/` énoncent ce qui était vrai
                     # à leur date. Les corriger réécrirait la décision qu'ils
                     # enregistrent ; ce garde vise les pages qu'un lecteur suit.
                     if "history" not in p.parts and p.parent.name != "adr"]
    return sorted(set(trouvees))


def _aide(commande: str) -> str:
    from cli._support.help_dispatch import HELP_TEXTS_RICH

    return HELP_TEXTS_RICH[commande]


# ── L'aide fait foi ──────────────────────────────────────────────────────────

def test_l_aide_dit_bien_que_db_init_affiche_par_defaut() -> None:
    """Si ce postulat tombe, le garde ci-dessous n'a plus lieu d'être."""
    aide = _aide("db:init").lower()

    assert "affiche" in aide
    assert "--run" in aide


def test_aucune_page_n_affirme_que_db_init_cree_sans_nommer_run() -> None:
    """Le cas mesuré, sept pages durant des mois (ADR-067)."""
    fautives: "list[str]" = []
    for page in _pages():
        texte = page.read_text(encoding="utf-8")
        for phrase in PHRASE_DB_INIT.findall(texte):
            plate = " ".join(phrase.split())
            if not CREATION.search(plate):
                continue
            if any(marque in plate.lower() for marque in EXEMPTIONS):
                continue
            ligne = texte[: texte.index(phrase)].count("\n") + 1
            fautives.append(
                f"{page.relative_to(PROJECT_ROOT)}:{ligne} — {plate[:88]}")

    assert not fautives, (
        "pages affirmant que `db:init` crée ou se connecte, sans nommer `--run` "
        "ni le cas sans serveur :\n  " + "\n  ".join(fautives))


# ── Le garde reste étroit, et le dit ─────────────────────────────────────────

@pytest.mark.parametrize("phrase", [
    "Par défaut, `forge db:init` ne se connecte pas : il affiche le SQL.",
    "`forge db:init --run` crée la base et les deux comptes.",
    "`forge db:init` génère le SQL qui crée la base.",
    "Sur SQLite, `forge db:init` crée le fichier.",
])
def test_une_phrase_juste_n_est_pas_refusee(phrase: str) -> None:
    """Quatre formulations correctes, relevées à tort par la première version."""
    plate = " ".join(phrase.split())

    assert CREATION.search(plate) is None or any(
        m in plate.lower() for m in EXEMPTIONS)


def test_une_phrase_fautive_est_bien_refusee() -> None:
    """Contre-épreuve : sans elle, le garde pourrait ne rien garder du tout."""
    plate = "`forge db:init` crée la base, l'utilisateur applicatif et la table."

    assert CREATION.search(plate)
    assert not any(m in plate.lower() for m in EXEMPTIONS)


def test_les_exemptions_disent_pourquoi() -> None:
    """Une exemption sans motif écrit se transforme en trou silencieux."""
    source = Path(__file__).read_text(encoding="utf-8")
    bloc = source[source.index("#: Marques qui rendent"):source.index("EXEMPTIONS = (")]

    assert "négation" in bloc
    assert "sans serveur" in bloc
