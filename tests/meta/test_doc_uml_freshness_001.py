"""DOC-UML-FRESHNESS-001 : les diagrammes de classe décrivent-ils le code réel.

Chaque page de référence porte un chapitre « Schémas UML », soit 27 diagrammes
de classe et 27 de séquence. Ils sont dessinés à la main et vieillissent en
silence : une méthode retirée du contrat, et le schéma continue de montrer
l'architecture d'avant, avec l'autorité que donne un dessin.

Trouvé à la première exécution : le diagramme de `forge-mvc-sessions-db`
attribuait `cleanup_expired()` au **protocole** `SessionStore` du cœur, qui ne
le déclare pas. La méthode existe bien, mais sur `DbSessionStore` seulement, et
c'est cohérent : purger des sessions périmées n'a de sens que pour un store
persistant.

Le garde est volontairement **silencieux plutôt que criard**. Sa première
version refusait douze acteurs conceptuels que les diagrammes ont parfaitement
le droit de dessiner, l'exécuteur injecté `DBExecutor`, la bibliothèque externe
`Pillow`, le contrôleur du lecteur, la factory d'exemple. Un garde qui crie à
tort finit désactivé, et ne garde alors plus rien.

La limite est assumée et écrite : une classe **renommée** sort du contrôle au
lieu d'être signalée, faute de pouvoir la distinguer d'un acteur conceptuel.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools import check_uml_diagrams as garde

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ── La lecture des diagrammes ────────────────────────────────────────────────

def test_les_classes_et_leurs_methodes_sont_lues() -> None:
    diagramme = (
        "classDiagram\n"
        "    class SQLiteBackend {\n"
        "        +name = \"sqlite\"\n"
        "        +get_connection() connexion\n"
        "    }\n"
    )
    lues = garde.lire_classes(diagramme)

    assert lues == {"SQLiteBackend": ["get_connection"]}


def test_une_entree_de_prose_n_est_pas_prise_pour_une_methode() -> None:
    """`+CREATE INDEX séparés` décrit un comportement, pas un appel."""
    diagramme = ("classDiagram\n    class SQLiteDialect {\n"
                 "        +types SQLite\n        +CREATE INDEX séparés\n    }\n")

    assert garde.lire_classes(diagramme) == {"SQLiteDialect": []}


def test_les_classes_du_code_sont_lues_par_ast() -> None:
    """Jamais importées : un opt-in absent ne doit pas faire tomber le reste."""
    code = garde.classes_du_code()

    assert "DbSessionStore" in code
    assert "cleanup_expired" in code["DbSessionStore"]


# ── Le tri, et ce qu'il laisse passer ────────────────────────────────────────

@pytest.mark.parametrize("acteur", ["DBExecutor", "Pillow", "VilleFactory", "Controller"])
def test_un_acteur_conceptuel_ne_fait_pas_echouer(acteur: str,
                                                  capsys: pytest.CaptureFixture[str]) -> None:
    """Un diagramme a le droit de dessiner ce qui n'est pas une classe du dépôt."""
    assert acteur not in garde.classes_du_code()


def test_le_motif_de_classe_exige_un_pascal_case() -> None:
    """`class fichier` ou `class forge_sessions` désignent une base, une table."""
    assert not garde.IDENTIFIANT_CLASSE.match("fichier")
    assert not garde.IDENTIFIANT_CLASSE.match("forge_sessions")
    assert garde.IDENTIFIANT_CLASSE.match("DbSessionStore")


def test_la_limite_est_ecrite() -> None:
    """Un garde silencieux doit dire ce qu'il ne voit pas (principe 3)."""
    source = (PROJECT_ROOT / "tools" / "check_uml_diagrams.py").read_text(
        encoding="utf-8")

    assert "renommée" in source
    assert "conceptuel" in source


# ── Le contrat de session, correctement dessiné ──────────────────────────────

def test_le_protocole_ne_promet_pas_ce_qu_il_ne_declare_pas() -> None:
    """Le cas mesuré : `cleanup_expired()` attribuée au contrat du cœur."""
    contrat = (PROJECT_ROOT / "core" / "sessions" / "contract.py").read_text(
        encoding="utf-8")
    diagramme = (PROJECT_ROOT / "packages" / "forge-mvc-sessions-db" / "docs"
                 / "reference.md").read_text(encoding="utf-8")
    protocole = diagramme[diagramme.index("class SessionStore {"):
                          diagramme.index("class DbSessionStore {")]

    assert "def cleanup_expired" not in contrat
    assert "cleanup_expired" not in protocole


def test_la_page_dit_pourquoi_la_methode_deborde_du_contrat() -> None:
    """Retirer une ligne d'un schéma sans l'expliquer laisserait croire à un oubli."""
    page = (PROJECT_ROOT / "packages" / "forge-mvc-sessions-db" / "docs"
            / "reference.md").read_text(encoding="utf-8")

    assert "ne figure **pas** au contrat" in page


# ── Le verdict d'ensemble ────────────────────────────────────────────────────

def test_tous_les_diagrammes_decrivent_du_code_existant(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = garde.verifier(None)
    sortie = capsys.readouterr().out

    assert code == 0, f"un diagramme dessine du code absent :\n{sortie}"
