"""Garde-fou TOOLS-REFLOW-DOCS-FIABILITE-001.

`tools/reflow_docs.py` met la documentation en une phrase par ligne.
Sous nl2br, chaque retour à la ligne de la source devient un saut au rendu.
Une coupure fautive se voit donc, et l'outil en produisait.

Quatre défauts, mesurés sur la documentation du dépôt le 2026-09-16.
Les abréviations étaient reconnues sans limite de mot : « al. » captait
« local. » et « minimal. », et l'outil collait deux phrases correctes.
Il coupait après tout « » », alors qu'un guillemet fermant termine rarement une
phrase : ses deux passages de juillet ont posé 64 coupures au milieu de phrases.
Il fusionnait les blocs de champs (`**Date** :` puis `**Ticket** :`).
Il ne reconnaissait que les blocs de code en ```, pris en simple bascule, et
traitait en prose les blocs ~~~, les blocs imbriqués, les listes de
définitions, les abréviations et le CSS d'un `<style>`.

Sur les 277 pages de `docs/` qu'il signalait, 75 n'avaient aucun défaut.
Et l'invariant qui validait ses passages, aucun caractère non blanc modifié,
ne pouvait rien voir : coller deux phrases ne change aucun caractère non plus.

La comparaison des rendus en a révélé deux de plus, partagés avec l'ancien
outil et invisibles à toute mesure faite sur la source.
Une citation était aplatie en une ligne, ses paragraphes et son bloc de code
compris, et sortait de son admonition en perdant son indentation.
Des marqueurs de liste seuls (« 1. », « 2. ») étaient joints en listes imbriquées.
D'où le dernier test : le rendu HTML ne doit différer que par les sauts de ligne.

Les entrées sont fabriquées : ces tests exercent l'outil, pas les pages.
"""
from __future__ import annotations

import re

import markdown
import pytest

from tools.reflow_docs import reflow


def _sans_blancs(texte: str) -> str:
    """Caractères non blancs, marqueurs de citation retirés."""
    return re.sub(r"\s+", "", re.sub(r"(?m)^[ \t]*>", "", texte))


# ── Défaut 1 : une abréviation se reconnaît comme mot entier ─────────────────

@pytest.mark.parametrize(
    "source",
    [
        "Cette étape ne recrée pas le dépôt Git local.\nElle vérifie qu'il est prêt.",
        "L'applicatif garde un privilège minimal.\nRelisez-le avant de l'exécuter.",
        "Le fichier est lu dans l'index.\nLa suite en dépend.",
        "La colonne se nomme `VilleId`, etc.\nDans le format canonique, rien ne change.",
    ],
)
def test_une_fin_de_mot_n_est_pas_une_abreviation(source: str) -> None:
    assert reflow(source) == source


def test_deux_phrases_collees_apres_un_faux_suffixe_sont_separees() -> None:
    source = "Le serveur écoute en HTTP local. La politique est détaillée ailleurs."

    assert reflow(source) == (
        "Le serveur écoute en HTTP local.\nLa politique est détaillée ailleurs."
    )


@pytest.mark.parametrize(
    "source",
    [
        "Un opt-in, p. ex. `forge-mvc-mail`, se déclare.",
        "Voir la page, cf. Configuration, pour le détail.",
        "Les travaux de Dupont et al. Martin les reprennent.",
    ],
)
def test_une_vraie_abreviation_ne_coupe_pas(source: str) -> None:
    assert reflow(source) == source


# ── Défaut 2 : un guillemet fermant ne termine pas la phrase ─────────────────

@pytest.mark.parametrize(
    "source",
    [
        "La commande «\u00a0forge new\u00a0» crée un projet nu.",
        "Un avertissement «\u00a0base de données\u00a0» : c'est normal.",
        "Le tronc «\u00a0Opt-ins officiels\u00a0» (voir la navigation) les regroupe.",
    ],
)
def test_un_guillemet_fermant_au_milieu_de_la_phrase_ne_coupe_pas(source: str) -> None:
    assert reflow(source) == source


def test_une_coupure_posee_apres_un_guillemet_est_rejointe() -> None:
    """La forme exacte que les passages précédents ont laissée dans les pages."""
    source = "Un lien «\u00a0Réinitialiser\u00a0»\nest généré dans le formulaire."

    assert reflow(source) == (
        "Un lien «\u00a0Réinitialiser\u00a0» est généré dans le formulaire."
    )


def test_une_citation_qui_finit_sa_phrase_coupe() -> None:
    source = "Le message dit «\u00a0Terminé.\u00a0» La suite démarre."

    assert reflow(source) == "Le message dit «\u00a0Terminé.\u00a0»\nLa suite démarre."


def test_une_minuscule_ne_commence_pas_une_phrase() -> None:
    """Dans le doute, ne pas couper : une question en incise en est l'exemple."""
    source = "Une commande dédiée (`make:pivot-crud` ?) ou un module gère cela."

    assert reflow(source) == source


def test_une_ponctuation_ne_commence_pas_une_phrase() -> None:
    """Après « etc.) », un « ; » n'est pas une minuscule, et ne commence rien non plus."""
    source = "Les valeurs refusées (`change-me`, `default`, etc.)\n; la suite reste."

    assert reflow(source) == "Les valeurs refusées (`change-me`, `default`, etc.) ; la suite reste."


def test_une_coupure_ne_fait_pas_naitre_de_structure() -> None:
    """Placée en début de ligne, « 1. » ouvrirait une liste au rendu."""
    source = "Voici les étapes suivantes. 1. Installer le paquet."

    assert reflow(source) == source


def test_un_numero_en_tete_n_est_pas_une_phrase() -> None:
    source = "**3. `core.auth.session` expose les fonctions.**"

    assert reflow(source) == source


# ── Défaut 3 : un bloc de champs garde une ligne par champ ───────────────────

@pytest.mark.parametrize(
    "source",
    [
        "**Date** : 2026-05-20\n**Ticket** : `PIVOT-CRUD-001`\n**Statut** : Décision rendue",
        "**Date :** 2026-05-09\n**Ticket :** PUBLICATION-2.0-TAG-001",
        "**Date**\u00a0: 2026-05-20\n**Auteur**\u00a0: Forge",
    ],
)
def test_un_bloc_de_champs_n_est_pas_fusionne(source: str) -> None:
    assert reflow(source) == source


def test_un_champ_isole_coupe_en_milieu_de_phrase_est_rejoint() -> None:
    source = "**Cause** : le serveur répond\nmal au client."

    assert reflow(source) == "**Cause** : le serveur répond mal au client."


def test_la_valeur_coupee_d_un_champ_se_rejoint_dans_le_bloc() -> None:
    source = (
        "**Date** : 2026-05-20\n"
        "**Périmètre** : toutes les fixtures\ndéclarées dans `tests/`.\n"
        "**Auteur** : Forge"
    )

    assert reflow(source) == (
        "**Date** : 2026-05-20\n"
        "**Périmètre** : toutes les fixtures déclarées dans `tests/`.\n"
        "**Auteur** : Forge"
    )


# ── Défaut 4 : les blocs dont la structure dépend restent intacts ────────────

@pytest.mark.parametrize(
    ("nom", "source"),
    [
        ("bloc tilde", "~~~md\nune ligne\nsans point\n~~~"),
        (
            "bloc imbriqué",
            "````md\n```bash\nune ligne\nsans point\n```\ncette ligne\nreste du code\n````",
        ),
        ("style", "<style>\n  .md-grid {\n    margin: 0 auto;\n    max-width: 1500px;\n  }\n</style>"),
        ("maths", "$$\na^2 +\nb^2\n$$"),
        ("définitions", "Contrôleur\n:   Classe qui reçoit une requête.\n:   Et renvoie une réponse."),
        (
            "définition en admonition",
            '??? note "Termes"\n    Route\n    :   Association entre un chemin et une méthode.',
        ),
        ("abréviations", "*[CSRF]: Cross-Site Request Forgery\n*[SQL]: Structured Query Language"),
        ("onglets", '=== "Linux"\n\n    Installer le paquet.'),
    ],
)
def test_un_bloc_structurel_n_est_pas_reformate(nom: str, source: str) -> None:
    assert reflow(source) == source, nom


def test_la_prose_apres_un_bloc_imbrique_est_bien_reformatee() -> None:
    """Le bloc externe se ferme sur sa propre clôture, pas sur une plus courte.

    Une clôture interne isolée, montrée en exemple, ne ferme rien.
    En simple bascule, elle décalait tout le reste de la page d'un cran.
    """
    source = "````md\n```\n````\n\nUne phrase coupée\nen deux."

    assert reflow(source) == "````md\n```\n````\n\nUne phrase coupée en deux."


# ── Citations et marqueurs vides : la structure passe avant la phrase ────────

def test_les_paragraphes_d_une_citation_restent_distincts() -> None:
    source = "> Premier paragraphe\n> coupé.\n>\n> **Audience** : contributeurs."

    assert reflow(source) == "> Premier paragraphe coupé.\n>\n> **Audience** : contributeurs."


def test_le_code_d_une_citation_n_est_pas_aplati() -> None:
    source = "> Exemple :\n>\n> ```python\n> x = 1\n> y = 2\n> ```\n>\n> Fin de\n> l'exemple."

    assert reflow(source) == (
        "> Exemple :\n>\n> ```python\n> x = 1\n> y = 2\n> ```\n>\n> Fin de l'exemple."
    )


def test_une_citation_reste_dans_son_admonition() -> None:
    source = '??? note "Rendu"\n    > Une citation\n    > coupée.'

    assert reflow(source) == '??? note "Rendu"\n    > Une citation coupée.'


def test_des_marqueurs_de_liste_seuls_ne_sont_pas_joints() -> None:
    source = "Lister les étapes exécutées.\n\n1.\n2.\n3."

    assert reflow(source) == source


# ── Ce que l'outil fait toujours ─────────────────────────────────────────────

def test_rejoint_une_phrase_coupee_et_separe_les_phrases() -> None:
    source = "Une phrase coupée\nen deux. Une autre phrase.\n\n- Un item coupé\n  en deux. Suite."

    assert reflow(source) == (
        "Une phrase coupée en deux.\nUne autre phrase.\n\n- Un item coupé en deux.\n  Suite."
    )


_ECHANTILLON = "\n".join([
    "# Titre",
    "",
    "**Date** : 2026-09-16",
    "**Ticket** : `TOOLS-REFLOW-DOCS-FIABILITE-001`",
    "",
    "Le dépôt Git local. Il est prêt. La commande «\u00a0forge new\u00a0»",
    "crée un projet, p. ex. sous `~/Projets`.",
    "",
    '??? note "Détail"',
    "    Une admonition coupée",
    "    au milieu. Puis la suite ?",
    "",
    "> Une citation coupée",
    "> en deux. Fin.",
    "",
    "~~~",
    "du code",
    "~~~",
    "",
    "Terme",
    ":   Sa définition.",
    "",
])


def test_reformater_deux_fois_ne_change_plus_rien() -> None:
    une_fois = reflow(_ECHANTILLON)

    assert reflow(une_fois) == une_fois


def test_aucun_caractere_non_blanc_ne_change() -> None:
    assert _sans_blancs(reflow(_ECHANTILLON)) == _sans_blancs(_ECHANTILLON)


_RICHE = "\n".join([
    "# Page",
    "",
    "**Date** : 2026-09-16",
    "**Périmètre** : toutes les pages",
    "de la documentation.",
    "",
    "Une phrase coupée",
    "au milieu. Une autre «\u00a0citée\u00a0»",
    "au milieu, p. ex. ici. Le dépôt local. Il suit.",
    "",
    "> Une citation",
    "> coupée.",
    ">",
    "> ```python",
    "> x = 1",
    "> ```",
    "",
    '??? note "Détail"',
    "    Un contenu coupé",
    "    en deux.",
    "",
    "    > Citée dans",
    "    > l'admonition.",
    "",
    "- Un item coupé",
    "  en deux. Suite.",
    "- Second item.",
    "",
    "1.",
    "2.",
    "",
    "Terme",
    ":   Sa définition.",
    "",
    "| a | b |",
    "|---|---|",
    "| 1 | 2 |",
    "",
    "~~~md",
    "texte",
    "coupé",
    "~~~",
    "",
    "````md",
    "```",
    "````",
    "",
    '=== "Onglet"',
    "",
    "    Contenu coupé",
    "    d'onglet.",
    "",
    "<style>",
    "  .a {",
    "    margin: 0;",
    "  }",
    "</style>",
    "",
    "$$",
    "a +",
    "b",
    "$$",
    "",
    "Le SQL visible[^1].",
    "",
    "[^1]: Une note.",
    "",
    "*[SQL]: Structured Query Language",
    "*[CSRF]: Cross-Site Request Forgery",
    "",
])


def _rendu(texte: str) -> str:
    """Rendu avec les extensions structurelles de `mkdocs.yml`, sauts retirés."""
    html = markdown.markdown(
        texte,
        extensions=[
            "abbr", "admonition", "attr_list", "def_list", "footnotes", "md_in_html",
            "nl2br", "sane_lists", "tables", "pymdownx.details", "pymdownx.superfences",
            "pymdownx.tabbed", "pymdownx.arithmatex",
        ],
        extension_configs={
            "pymdownx.tabbed": {"alternate_style": True},
            "pymdownx.arithmatex": {"generic": True},
        },
    )
    return re.sub(r"\s+", " ", re.sub(r"<br\s*/?>", " ", html)).strip()


def test_le_rendu_ne_differe_que_par_les_sauts_de_ligne() -> None:
    """La seule preuve qu'un reformatage est juste : l'invariant de caractères ne suffit pas."""
    reformate = reflow(_RICHE)

    assert reformate != _RICHE, "l'échantillon doit exercer des reformatages"
    assert _rendu(reformate) == _rendu(_RICHE)


def test_les_espaces_insecables_sont_preserves() -> None:
    source = "Pourquoi\u00a0? Parce\u202fque la typographie l'exige."

    assert reflow(source) == "Pourquoi\u00a0?\nParce\u202fque la typographie l'exige."
