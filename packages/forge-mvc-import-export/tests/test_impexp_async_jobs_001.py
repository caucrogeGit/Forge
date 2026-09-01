"""IMPEXP-ASYNC-JOBS-001 : importer un gros fichier par la file de tâches.

Importer pendant une requête HTTP la fait attendre autant qu'il y a de lignes.
Dix mille lignes, dix mille insertions, et le navigateur abandonne avant la
fin : l'utilisateur relance, l'import repart de zéro, et parfois double les
lignes déjà écrites.

Le moteur prend des fonctions de conversion et d'insertion, que JSON ne sait
pas transporter. La tâche ne porte donc qu'un nom d'importeur et un chemin, ce
qui déplace la question vers deux autres : d'où vient ce chemin, et que faire
d'un fichier mal rempli.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_import_export")

from forge_mvc_import_export import (  # noqa: E402
    IMPORT_JOB_TASK,
    CsvImportError,
    FieldSpec,
    ImporterNotFound,
    ImportReport,
    ImportSourceError,
    clear_importers,
    coerce_int,
    import_payload,
    make_import_job_handler,
    register_importer,
    registered_importers,
)

SPECS = [FieldSpec("nom"), FieldSpec("age", coerce=coerce_int)]
CSV_VALIDE = "nom,age\nRoger,52\nAlice,31\n"


@pytest.fixture(autouse=True)
def _sans_importeur():
    clear_importers()
    yield
    clear_importers()


@pytest.fixture
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "personnes.csv"
    chemin.write_text(CSV_VALIDE, encoding="utf-8")
    return chemin


class TestEnregistrement:
    def test_un_importeur_enregistre_est_retrouve(self) -> None:
        register_importer("personnes", specs=SPECS, insert=lambda r: None)
        assert registered_importers() == ("personnes",)

    def test_un_nom_vide_est_refuse(self) -> None:
        with pytest.raises(CsvImportError):
            register_importer("  ", specs=SPECS, insert=lambda r: None)

    def test_un_nom_deja_pris_est_refuse(self) -> None:
        """Écraser en silence ferait écrire dans la mauvaise table."""
        register_importer("personnes", specs=SPECS, insert=lambda r: None)
        with pytest.raises(CsvImportError, match="déjà enregistré"):
            register_importer("personnes", specs=SPECS, insert=lambda r: None)


class TestChargeUtile:
    def test_la_charge_ne_porte_que_des_chaines(self) -> None:
        """Les specs et l'insertion ne se sérialisent pas en JSON."""
        import json

        charge = import_payload("personnes", "/tmp/a.csv", auteur="roger")
        assert json.loads(json.dumps(charge)) == charge

    def test_le_contexte_suit_la_tache(self) -> None:
        """Sans lui, le rapport ne saurait à qui répondre."""
        charge = import_payload("personnes", "/tmp/a.csv", auteur="roger")
        assert charge["context"] == {"auteur": "roger"}

    @pytest.mark.parametrize(("nom", "chemin"), [("", "/tmp/a.csv"), ("x", "  ")])
    def test_une_charge_incomplete_est_refusee(self, nom: str, chemin: str) -> None:
        with pytest.raises(CsvImportError):
            import_payload(nom, chemin)


class TestTraitement:
    def test_les_lignes_valides_sont_inserees(self, fichier: Path) -> None:
        inserees: list[dict[str, Any]] = []
        register_importer("personnes", specs=SPECS, insert=inserees.append)
        handler = make_import_job_handler(root=fichier.parent)

        handler(import_payload("personnes", fichier.name))

        assert inserees == [{"nom": "Roger", "age": 52}, {"nom": "Alice", "age": 31}]

    def test_le_rapport_est_rendu_a_l_application(self, fichier: Path) -> None:
        """Sans lui, un import différé serait muet."""
        rapports: list[tuple[ImportReport, dict[str, Any]]] = []
        register_importer(
            "personnes", specs=SPECS, insert=lambda r: None,
            on_report=lambda rapport, contexte: rapports.append((rapport, contexte)),
        )
        handler = make_import_job_handler(root=fichier.parent)

        handler(import_payload("personnes", fichier.name, auteur="roger"))

        rapport, contexte = rapports[0]
        assert rapport.imported == 2
        assert rapport.ok
        assert contexte == {"auteur": "roger"}


class TestLignesInvalides:
    def test_un_fichier_mal_rempli_ne_fait_pas_echouer_la_tache(
        self, tmp_path: Path
    ) -> None:
        """Réessayer ne corrigerait pas un CSV : la tâche rejouerait sans fin."""
        chemin = tmp_path / "mauvais.csv"
        chemin.write_text("nom,age\nRoger,pas_un_nombre\n", encoding="utf-8")

        rapports: list[ImportReport] = []
        register_importer(
            "personnes", specs=SPECS, insert=lambda r: None,
            on_report=lambda rapport, contexte: rapports.append(rapport),
        )
        handler = make_import_job_handler(root=tmp_path)

        handler(import_payload("personnes", chemin.name))

        assert rapports[0].errors, "les erreurs doivent être rapportées"
        assert not rapports[0].ok

    def test_les_erreurs_sont_localisees(self, tmp_path: Path) -> None:
        chemin = tmp_path / "mauvais.csv"
        chemin.write_text("nom,age\nRoger,52\nAlice,x\n", encoding="utf-8")

        rapports: list[ImportReport] = []
        register_importer(
            "personnes", specs=SPECS, insert=lambda r: None,
            on_report=lambda rapport, contexte: rapports.append(rapport),
        )
        make_import_job_handler(root=tmp_path)(import_payload("personnes", chemin.name))

        assert rapports[0].errors[0].row == 2
        assert rapports[0].errors[0].field == "age"


class TestErreursTechniques:
    def test_un_importeur_inconnu_leve(self, fichier: Path) -> None:
        """Erreur de configuration : l'exploitant doit la voir."""
        handler = make_import_job_handler(root=fichier.parent)

        with pytest.raises(ImporterNotFound, match="inconnu"):
            handler(import_payload("jamais_declare", fichier.name))

    def test_le_message_nomme_les_importeurs_connus(self, fichier: Path) -> None:
        register_importer("personnes", specs=SPECS, insert=lambda r: None)
        handler = make_import_job_handler(root=fichier.parent)

        with pytest.raises(ImporterNotFound, match="personnes"):
            handler(import_payload("autre", fichier.name))

    def test_un_fichier_absent_leve(self, tmp_path: Path) -> None:
        register_importer("personnes", specs=SPECS, insert=lambda r: None)
        handler = make_import_job_handler(root=tmp_path)

        with pytest.raises(ImportSourceError, match="introuvable"):
            handler(import_payload("personnes", "jamais_depose.csv"))


class TestCheminHorsRacine:
    """Le chemin vient d'une file que plusieurs processus écrivent."""

    @pytest.mark.parametrize(
        "hostile", ["../../etc/passwd", "../secret.csv", "/etc/hosts"]
    )
    def test_un_chemin_hors_racine_est_refuse(
        self, hostile: str, tmp_path: Path
    ) -> None:
        register_importer("personnes", specs=SPECS, insert=lambda r: None)
        handler = make_import_job_handler(root=tmp_path)

        with pytest.raises(ImportSourceError):
            handler(import_payload("personnes", hostile))

    def test_le_refus_dit_la_racine_plutot_que_le_contenu(self, tmp_path: Path) -> None:
        register_importer("personnes", specs=SPECS, insert=lambda r: None)
        handler = make_import_job_handler(root=tmp_path)

        with pytest.raises(ImportSourceError, match="racine autorisée"):
            handler(import_payload("personnes", "../../etc/passwd"))

    def test_un_sous_dossier_de_la_racine_est_permis(self, tmp_path: Path) -> None:
        depot = tmp_path / "depots" / "2026"
        depot.mkdir(parents=True)
        (depot / "a.csv").write_text(CSV_VALIDE, encoding="utf-8")

        inserees: list[dict[str, Any]] = []
        register_importer("personnes", specs=SPECS, insert=inserees.append)
        handler = make_import_job_handler(root=tmp_path)

        handler(import_payload("personnes", "depots/2026/a.csv"))

        assert len(inserees) == 2


class TestParcoursComplet:
    def test_de_la_mise_en_file_a_l_import(self, fichier: Path) -> None:
        pytest.importorskip("forge_mvc_jobs")
        import importlib.util
        import sys

        from forge_mvc_jobs.queue import enqueue, process_one

        chemin = (
            Path(__file__).resolve().parent.parent.parent
            / "forge-mvc-jobs" / "tests" / "test_jobs_queue_001.py"
        )
        spec = importlib.util.spec_from_file_location("_jobs_double_impexp", chemin)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["_jobs_double_impexp"] = module
        spec.loader.exec_module(module)

        file = module.FakeDb()
        inserees: list[dict[str, Any]] = []
        register_importer("personnes", specs=SPECS, insert=inserees.append)

        enqueue(IMPORT_JOB_TASK, import_payload("personnes", fichier.name), db=file)
        assert inserees == [], "rien ne s'importe pendant la requête"

        traitee = process_one(
            {IMPORT_JOB_TASK: make_import_job_handler(root=fichier.parent)}, db=file
        )

        assert traitee is True
        assert len(inserees) == 2
