"""GOV-CLAUDE-MD-DERIVE-GARDEFOU-001 — le briefing agent ne ment pas.

`CLAUDE.md` est le fichier que lit tout agent travaillant sur Forge, et ses
instructions y sont présentées comme prioritaires. Il avait dérivé, et il
affirmait deux choses fausses :

    « runtime Python volontairement limité : MariaDB, python-dotenv,
      Jinja2, Argon2, jsonschema »

MariaDB avait quitté le cœur avec l'ADR-054, qui l'a rendu agnostique de la base
de données. `jsonschema` avait suivi le moteur d'entités par l'ADR-070. Le
fichier se contredisait lui-même, sa section 3 listant correctement les backends
en opt-ins.

Le coût est immédiat et silencieux : un agent qui lit cette ligne propose du code
supposant MariaDB dans un cœur qu'un ADR a rendu agnostique. C'est la classe de
défaut que ce dépôt corrige ailleurs depuis deux jours, une affirmation qui n'est
plus vraie et que rien ne surveille.

Le tableau des ADR avait dérivé de même : arrêté à 086 alors que le dépôt était
à 093, soit **sept décisions absentes** d'une liste que le fichier présente comme
celle à lire avant toute proposition.

Ce garde-fou compare ce que le briefing DÉCLARE à ce que le dépôt EST. Il ne
teste pas de la documentation contre de la documentation (règle D) : les deux
côtés sont des faits, lus dans `pyproject.toml` et dans `docs/adr/`.

Le remède de fond n'est pas ici mais dans le fichier : l'énumération des
dépendances a été retirée au profit d'un renvoi à sa source. Ce qui n'est pas
énuméré ne peut pas dériver ; ce garde-fou couvre ce qui doit le rester.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BRIEFING = PROJECT_ROOT / "CLAUDE.md"

#: Distributions dont le nom peut légitimement apparaître dans le briefing sans
#: être une dépendance du cœur : ce sont celles des opt-ins, cités par ailleurs.
_HORS_COEUR = {"pyotp", "pillow", "mariadb", "jsonschema"}


@pytest.fixture(scope="module")
def briefing() -> str:
    return BRIEFING.read_text(encoding="utf-8")


def _dependances_du_coeur() -> set[str]:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return {
        re.split(r"[<>=!~\[;\s]", exigence.strip(), maxsplit=1)[0].lower()
        for exigence in data["project"]["dependencies"]
    }


# ── Les dépendances ne sont plus énumérées ───────────────────────────────────

class TestDependancesNonEnumerees:
    """La cause retirée : une énumération volatile dans un fichier durable."""

    def test_le_briefing_renvoie_a_la_source(self, briefing: str) -> None:
        section = briefing.split("**Type** :")[0]

        assert "pyproject.toml" in section, (
            "la section 1 doit renvoyer à la source des dépendances plutôt que "
            "de les énumérer : l'énumération avait dérivé sur deux entrées")

    @pytest.mark.parametrize("paquet", sorted(_HORS_COEUR))
    def test_aucune_dependance_hors_coeur_n_est_annoncee_comme_runtime(
        self, briefing: str, paquet: str,
    ) -> None:
        """Le cas mesuré : MariaDB et jsonschema annoncés comme runtime du cœur."""
        section = briefing.split("**Type** :")[0]
        reel = _dependances_du_coeur()

        if paquet in reel:
            return  # redevenu une dépendance : la mention serait juste
        assert paquet.lower() not in section.lower(), (
            f"la section 1 cite « {paquet} » comme runtime alors qu'il n'est pas "
            f"dans les dépendances du cœur : {sorted(reel)}")


# ── Le tableau des ADR couvre toutes les décisions ───────────────────────────

class TestTableauDesAdr:

    @staticmethod
    def _cites(briefing: str) -> set[int]:
        return {int(n) for n in re.findall(r"^\| ADR-(\d{3}) \|", briefing, re.MULTILINE)}

    @staticmethod
    def _existants() -> set[int]:
        return {int(p.name[:3]) for p in (PROJECT_ROOT / "docs" / "adr").glob("[0-9][0-9][0-9]-*.md")}

    def test_aucune_decision_ne_manque_au_tableau(self, briefing: str) -> None:
        """Sept y manquaient, dont deux écrites la veille."""
        manquants = sorted(self._existants() - self._cites(briefing))

        assert not manquants, (
            "le tableau des ADR de CLAUDE.md ne cite pas ces décisions, que le "
            f"dépôt porte pourtant : {['ADR-%03d' % n for n in manquants]}\n"
            "Ce tableau est présenté comme la liste à lire avant toute proposition.")

    def test_aucune_decision_citee_n_a_disparu(self, briefing: str) -> None:
        """Le symétrique : un ADR retiré du dépôt et resté au tableau."""
        fantomes = sorted(self._cites(briefing) - self._existants())

        assert not fantomes, (
            "le tableau cite des ADR absents de docs/adr/ : "
            f"{['ADR-%03d' % n for n in fantomes]}")

    def test_le_nom_de_fichier_cite_existe(self, briefing: str) -> None:
        """Un chemin faux envoie l'agent lire autre chose, ou rien."""
        absents = [
            nom for nom in re.findall(r"^\| ADR-\d{3} \| `([^`]+)`", briefing, re.MULTILINE)
            if not (PROJECT_ROOT / "docs" / "adr" / nom).is_file()
        ]

        assert not absents, f"fichiers d'ADR cités mais introuvables : {absents}"


# ── Le compte de paquets ─────────────────────────────────────────────────────

class TestComptePaquets:

    def test_le_compte_annonce_est_le_bon(self, briefing: str) -> None:
        """Le briefing annonce un nombre de sous-dossiers de packages/."""
        reel = len(list((PROJECT_ROOT / "packages").glob("*/pyproject.toml")))
        annonces = {int(n) for n in re.findall(r"(\d+) sous-dossiers maintenus", briefing)}

        assert annonces, "la note sur packages/ n'annonce plus de compte"
        assert annonces == {reel}, (
            f"le briefing annonce {sorted(annonces)} paquets, le dépôt en porte {reel}")


# ── La cohérence interne du briefing ─────────────────────────────────────────

class TestCoherenceInterne:

    def test_la_section_des_sources_canoniques_survit(self, briefing: str) -> None:
        """C'est elle qui porte le remède : ne pas chercher le volatile ici.

        Les deux affirmations fausses contredisaient cette section du même
        fichier. La retirer rouvrirait la porte.
        """
        assert "Sources canoniques pour les informations volatiles" in briefing
        assert "`pyproject.toml` → `[project].version`" in briefing
