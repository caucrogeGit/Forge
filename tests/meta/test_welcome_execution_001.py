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

# Boucle code, et non documentaire. Ce fichier a d'abord porté le marqueur
# `docs`, tant qu'il ne lisait que des parcours et un `nav`. Il éprouve désormais
# aussi la logique du harnais, sur un projet temporaire, ce qui en fait un test
# d'outillage : le garde des marqueurs l'a signalé, et il avait raison.
pytestmark = pytest.mark.meta

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


# ── Les quatre backends portaient le même défaut ─────────────────────────────

@pytest.mark.parametrize("backend", ["sqlite", "mariadb", "postgres", "mssql"])
def test_chaque_backend_cite_le_moteur_d_entites(backend: str) -> None:
    """`db:init`, `db:apply` et `migration:*` viennent de l'opt-in entities
    (ADR-070) : les quatre parcours l'omettaient de leurs prérequis."""
    dossier = PROJECT_ROOT / "packages" / f"forge-mvc-{backend}" / "docs" / "welcome"
    textes = "\n".join(p.read_text(encoding="utf-8") for p in dossier.rglob("*.md"))

    assert "forge-mvc-entities" in textes


@pytest.mark.parametrize("backend", ["sqlite", "mariadb", "postgres", "mssql"])
def test_chaque_backend_configure_avant_de_provisionner(backend: str) -> None:
    """Sans `db:config`, le backend ignore où se connecter et `db:init` refuse."""
    dossier = PROJECT_ROOT / "packages" / f"forge-mvc-{backend}" / "docs" / "welcome"
    textes = "\n".join(p.read_text(encoding="utf-8") for p in dossier.rglob("*.md"))

    assert "forge db:config" in textes


@pytest.mark.parametrize("backend", ["sqlite", "mariadb", "postgres", "mssql"])
def test_chaque_backend_declare_l_entite_avant_son_crud(backend: str) -> None:
    """`make:crud` consomme un contrat que seul `make:entity` crée."""
    dossier = PROJECT_ROOT / "packages" / f"forge-mvc-{backend}" / "docs" / "welcome"
    page = next(p for p in dossier.rglob("*.md")
                if "make:crud" in p.read_text(encoding="utf-8"))
    texte = page.read_text(encoding="utf-8")

    assert "make:entity" in texte, f"{page.name} appelle make:crud sans make:entity"
    assert texte.index("make:entity") < texte.index("make:crud")


# ── Un harnais ne prétend pas avoir vérifié ce qu'il n'a pas joué ────────────

def test_un_parcours_sans_bloc_joue_le_dit(capsys: pytest.CaptureFixture[str],
                                           tmp_path: Path) -> None:
    """« De bout en bout » sur zéro bloc se lirait comme une couverture.

    Même leçon que le verdict pytest lu dans le texte plutôt que dans le code
    retour : un contrôle qui n'a rien contrôlé doit le dire.
    """
    harnais.parcourir("iot", tmp_path, lister=False)

    assert "RIEN JOUÉ" in capsys.readouterr().out


def test_forge_doctor_reste_verifie() -> None:
    """Une règle large sur « tout ce qui ressemble à un diagnostic » sautait
    `forge doctor`, qui sort en 0 et se vérifie très bien."""
    assert harnais.raison_de_sauter("forge doctor") is None


@pytest.mark.parametrize(("script", "raison"), [
    ("forge deploy:check", "DIAGNOSTIC"),
    ("forge iot:doctor", "DIAGNOSTIC"),
    ("forge iot:listen", "SERVICE_EXTERNE"),
    ("curl -k https://localhost:8000/api/iot/events", "SERVEUR"),
    ("docker run --rm postgres", "BLOQUANT"),
    ("sudo mariadb", "MANUEL"),
])
def test_les_motifs_ajoutes_sont_reconnus(script: str, raison: str) -> None:
    assert harnais.raison_de_sauter(script) == raison


def test_un_script_que_le_lecteur_ecrit_n_est_pas_lance(tmp_path: Path) -> None:
    """Les parcours font écrire un fichier dans un bloc `python`, puis le
    lancent : le harnais n'en pose aucun, le lancer mesurerait son propre trou."""
    # Pas `worker.py` : celui-la est declare bloquant, une boucle de worker
    # ne rendant jamais la main meme une fois le fichier pose.
    assert harnais.raison_de_sauter("python script_du_lecteur.py", tmp_path) == \
        "FICHIER_ABSENT"

    (tmp_path / "script_du_lecteur.py").write_text("", encoding="utf-8")
    assert harnais.raison_de_sauter("python script_du_lecteur.py", tmp_path) is None


# ── Les deux blocs corrigés ──────────────────────────────────────────────────

def test_la_ligne_de_crontab_n_est_pas_etiquetee_bash() -> None:
    """`0 3 * * * ...` n'est pas une commande : bash y lit « 0 » comme un binaire."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-sessions-db" / "docs" / "welcome"
            / "intermediaire" / "sessions-db-cleanup.md").read_text(encoding="utf-8")
    bloc = page[page.index("crontab de l'application") - 200:
                page.index("crontab de l'application")]

    assert "```bash" not in bloc


def test_la_verification_du_paquet_de_test_sort_en_zero_quand_tout_va_bien() -> None:
    """`grep` sort en 1 quand il ne trouve rien, soit le cas qui convient :
    posé tel quel dans une CI, il signalerait un échec au meilleur moment."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-testing" / "docs" / "welcome"
            / "avance" / "testing-devonly.md").read_text(encoding="utf-8")

    assert 'grep -r "forge_mvc_testing" mvc/   # ne doit rien retourner' not in page
    assert "if grep -rq" in page


# ── Le harnais pose les fichiers que le parcours fait écrire ─────────────────

def test_un_bloc_nommant_son_fichier_est_reconnu() -> None:
    """Convention suivie par 187 des 279 blocs `python` des parcours."""
    assert harnais.fichier_du_bloc("# mvc/controllers/x.py\nprint(1)\n") == \
        "mvc/controllers/x.py"


def test_le_nom_peut_etre_suivi_d_une_precision() -> None:
    """« # worker.py, à la racine de l'application » : la précision est utile
    au lecteur, et ne doit pas empêcher la pose."""
    assert harnais.fichier_du_bloc("# worker.py, à la racine\nprint(1)\n") == "worker.py"


def test_une_phrase_citant_un_fichier_n_est_pas_une_consigne_de_pose() -> None:
    """Le nom doit venir en premier, sans quoi tout commentaire mentionnant un
    module serait pris pour un ordre d'écriture."""
    assert harnais.fichier_du_bloc("# on modifie mvc/x.py plus tard\n") is None


def test_un_bloc_sans_nom_de_fichier_n_est_pas_pose() -> None:
    assert harnais.fichier_du_bloc("from forge_mvc_import_export import to_csv\n") is None


def test_un_fichier_existant_n_est_jamais_ecrase(tmp_path: "Path") -> None:
    """`mvc/routes/__init__.py` est nommé 92 fois dans les parcours, toujours
    pour un FRAGMENT à fusionner : l'écrire entier détruirait le câblage posé
    par `forge new` (principe 9)."""
    cible = tmp_path / "mvc" / "routes" / "__init__.py"
    cible.parent.mkdir(parents=True)
    cible.write_text("# câblage existant\n", encoding="utf-8")

    verdict = harnais.poser_fichier("mvc/routes/__init__.py", "# fragment\n", tmp_path)

    assert verdict == "FRAGMENT"
    assert cible.read_text(encoding="utf-8") == "# câblage existant\n"


def test_un_fichier_neuf_est_pose(tmp_path: "Path") -> None:
    verdict = harnais.poser_fichier("mvc/controllers/x.py", "# mvc/controllers/x.py\n",
                                    tmp_path)

    assert verdict == "ÉCRIT"
    assert (tmp_path / "mvc" / "controllers" / "x.py").is_file()


def test_les_blocs_sont_lus_dans_l_ordre_du_document() -> None:
    """Un parcours alterne « posez ce fichier » et « lancez cette commande » :
    ne lire que le `bash` revenait à jouer la moitié d'un dialogue."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-jobs" / "docs" / "welcome"
            / "intermediaire" / "jobs-worker.md")
    ordonnes = harnais.blocs_ordonnes(page)
    langages = [langage for _l, langage, _c in ordonnes]

    assert "python" in langages and "bash" in langages
    lignes = [ligne for ligne, _lang, _c in ordonnes]
    assert lignes == sorted(lignes)


# ── Le palier des fixtures reliées, débloqué ─────────────────────────────────

def test_les_fixtures_reliees_preparent_leurs_deux_tables() -> None:
    """Ce palier relie `eleve` à `users` : il lui faut les deux.

    Il était le dernier arrêt du parcours des fixtures, faute de pouvoir
    déclarer une entité avec ses champs sans terminal. Les modes non interactifs
    de `make:entity` l'ont débloqué (ENTITIES-NON-INTERACTIVE-001).
    """
    page = (PROJECT_ROOT / "packages" / "forge-mvc-fixtures" / "docs" / "welcome"
            / "avance" / "fixtures-reliees.md").read_text(encoding="utf-8")

    for commande in ("forge make:auth", "forge auth:init", "forge db:apply"):
        assert commande in page, f"{commande} manque aux prérequis du palier"
    assert page.index("forge make:auth") < page.index("fixtures:make-factory eleve")


def test_le_champ_user_id_est_annonce_comme_entier() -> None:
    """La page enseigne la différence de nommage entre un entier (`UserId`) et
    un champ `foreign_key` (`user_id`) : la confondre égarerait sa factory."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-fixtures" / "docs" / "welcome"
            / "avance" / "fixtures-reliees.md").read_text(encoding="utf-8")

    assert 'user_id:integer' in page
    assert "entier ordinaire" in page


def test_une_commande_deja_non_interactive_n_est_pas_substituee() -> None:
    """Annoncer un geste qu'on ne fait pas trompe autant que taire celui
    qu'on fait."""
    script = 'forge make:entity Eleve --field "nom:string"'
    _joue, substitution = harnais.substituer(script)

    assert substitution is None
