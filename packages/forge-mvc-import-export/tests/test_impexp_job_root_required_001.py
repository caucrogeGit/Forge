"""`IMPEXP-JOB-ROOT-REQUIRED-001` — la racine des imports est obligatoire.

La décision de livraison d'`IMPEXP-ASYNC-JOBS-001` annonce « racine de chemins
**obligatoire** ». Elle ne l'était pas : `root` valait `None` par défaut, et
`_resoudre_source` ne vérifiait alors **rien**.

Le chemin du fichier vient de la charge utile d'une tâche, donc d'une table que
plusieurs processus écrivent. Pouvoir y écrire une ligne suffisait donc à faire
lire au worker n'importe quel fichier du serveur, et à l'**importer ligne à
ligne dans la base**. C'est une escalade de « je peux écrire une ligne » vers
« je peux lire tout le disque ».

## Le refus a lieu au câblage, pas au premier import

Une application qui enregistre ce gestionnaire sans racine a fait une erreur de
câblage, et la découvrir au démarrage du worker vaut mieux qu'en production.
C'est le même parti que `register_notification_routes` pour son résolveur de
destinataire.

Aucun appelant du dépôt ne dépendait du défaut permissif : la documentation et
les huit sites de test passaient tous une racine.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_import_export")

from forge_mvc_import_export import (  # noqa: E402
    ImportSourceError,
    make_import_job_handler,
)
from forge_mvc_import_export.queueing import _resoudre_source  # noqa: E402


class TestRacineObligatoire:

    def test_sans_racine_le_cablage_leve(self) -> None:
        """Le cas qui passait, et qui ouvrait le disque."""
        with pytest.raises(ImportSourceError):
            make_import_job_handler()

    def test_le_refus_dit_le_danger(self) -> None:
        """Un refus qui n'explique pas se contourne par le premier
        contournement venu."""
        with pytest.raises(ImportSourceError) as leve:
            make_import_job_handler()

        assert "etc/passwd" in str(leve.value)
        assert "file" in str(leve.value)

    def test_le_refus_dit_quoi_faire(self) -> None:
        with pytest.raises(ImportSourceError) as leve:
            make_import_job_handler()

        assert "storage/imports" in str(leve.value)

    def test_avec_racine_le_gestionnaire_est_rendu(self, tmp_path: Path) -> None:
        assert callable(make_import_job_handler(root=tmp_path))

    def test_une_racine_en_chaine_convient(self, tmp_path: Path) -> None:
        """La signature accepte `str | Path` : la refuser en chaîne ferait
        échouer un câblage écrit depuis la configuration."""
        assert callable(make_import_job_handler(root=str(tmp_path)))


class TestGardeDeChemin:
    """La garde elle même était juste : c'est son activation qui manquait."""

    @pytest.mark.parametrize(
        "chemin",
        ["../../../etc/passwd", "/etc/passwd", "imports/../../secret.csv"],
        ids=["remontee", "absolu", "remontee-interne"],
    )
    def test_un_chemin_hors_racine_est_refuse(
        self, tmp_path: Path, chemin: str
    ) -> None:
        with pytest.raises(ImportSourceError, match="hors de la racine"):
            _resoudre_source(chemin, tmp_path)

    def test_un_chemin_sous_la_racine_est_accepte(self, tmp_path: Path) -> None:
        fichier = tmp_path / "imports" / "personnes.csv"
        fichier.parent.mkdir(parents=True)
        fichier.write_text("nom\nDurand\n", encoding="utf-8")

        assert _resoudre_source("imports/personnes.csv", tmp_path) == fichier.resolve()

    def test_un_fichier_absent_est_refuse(self, tmp_path: Path) -> None:
        """Et le motif diffère de celui d'un chemin hors racine : les deux ne
        se corrigent pas au même endroit."""
        with pytest.raises(ImportSourceError, match="introuvable"):
            _resoudre_source("imports/absent.csv", tmp_path)


class TestAucunAppelantSansRacine:

    def test_la_documentation_passe_une_racine(self) -> None:
        """La doc montrait déjà le bon geste : c'est le code qui ne l'exigeait
        pas."""
        reference = (Path(__file__).resolve().parents[1] / "docs" / "reference.md")
        texte = reference.read_text(encoding="utf-8")

        assert "make_import_job_handler(root=" in texte

    def test_aucun_appel_sans_racine_dans_le_depot(self) -> None:
        """Lu par `ast` : un appel sans racine lèverait désormais, et le
        découvrir par la suite de tests vaut mieux que par un worker."""
        import ast

        # Balayé sur ce paquet et le squelette, où vivent les appels réels.
        # Parcourir tout le dépôt coûtait seize secondes et faisait remonter
        # les avertissements de syntaxe de fichiers étrangers au sujet.
        racine = Path(__file__).resolve().parents[3]
        cibles = [racine / "packages" / "forge-mvc-import-export", racine / "skeleton"]
        fautifs: "list[str]" = []
        for base in cibles:
            for source in base.rglob("*.py"):
                chemin = source.as_posix()
                if "__pycache__" in chemin or "/build/" in chemin:
                    continue
                try:
                    arbre = ast.parse(source.read_text(encoding="utf-8"))
                except (SyntaxError, UnicodeDecodeError, OSError):
                    continue
                for noeud in ast.walk(arbre):
                    if not isinstance(noeud, ast.Call):
                        continue
                    nom = (noeud.func.id if isinstance(noeud.func, ast.Name)
                           else noeud.func.attr if isinstance(noeud.func, ast.Attribute)
                           else "")
                    if nom != "make_import_job_handler":
                        continue
                    if not any(k.arg == "root" for k in noeud.keywords):
                        fautifs.append(f"{source.relative_to(racine)}:{noeud.lineno}")

        # Les appels du test présent sont volontaires : ils vérifient le refus.
        fautifs = [f for f in fautifs if "test_impexp_job_root_required" not in f]

        assert not fautifs, (
            f"ces appels n'ont pas de racine et lèveront : {', '.join(fautifs)}")
