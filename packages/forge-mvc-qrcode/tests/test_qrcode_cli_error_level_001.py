"""`QRCODE-CLI-001` et `QRCODE-ERROR-LEVEL-001`.

Le niveau de correction existait sur `QrCode.from_text`, mais
`QrCodeResponse.from_text` **ne le transmettait pas** : un contrôleur, c'est à
dire le chemin documenté pour servir un QR Code, ne pouvait pas le choisir.

Ce n'est pas un réglage de confort. Un code imprimé sur une étiquette ou une
affiche, susceptible d'être rayé ou partiellement couvert, demande `h`, qui
tolère 30 % de perte. En `m`, le défaut, qui en tolère 15 %, il devient
illisible.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_qrcode")
pytest.importorskip("segno")

from forge_mvc_qrcode import (  # noqa: E402
    ERROR_LEVELS,
    QrCode,
    QrCodeError,
    QrCodeResponse,
)
from forge_mvc_qrcode.cli.make import main, parse_options  # noqa: E402


# ------------------------------------------------- QRCODE-ERROR-LEVEL


class TestNiveauSurLeCheminHttp:

    def test_la_reponse_transmet_le_niveau(self) -> None:
        """Le défaut corrigé : la fabrique appelait `from_text(text)` tout court."""
        leger = QrCodeResponse.from_text("https://exemple.fr", error="l")
        robuste = QrCodeResponse.from_text("https://exemple.fr", error="h")

        assert len(robuste.body) > len(leger.body), (
            "un niveau de correction plus élevé produit un code plus dense"
        )

    def test_le_defaut_reste_m(self) -> None:
        assert QrCodeResponse.from_text("x").body == QrCodeResponse.from_text(
            "x", error="m"
        ).body

    def test_un_niveau_inconnu_est_refuse(self) -> None:
        with pytest.raises(QrCodeError, match="Niveau de correction"):
            QrCodeResponse.from_text("x", error="z")

    @pytest.mark.parametrize("niveau", sorted(ERROR_LEVELS))
    def test_les_quatre_niveaux_repondent(self, niveau: str) -> None:
        assert QrCodeResponse.from_text("x", error=niveau).body

    def test_le_niveau_vaut_pour_les_deux_formats(self) -> None:
        png = QrCodeResponse.from_text("https://exemple.fr", fmt="png", error="h")
        svg = QrCodeResponse.from_text("https://exemple.fr", fmt="svg", error="h")

        assert png.body and svg.body

    def test_les_niveaux_sont_decouvrables(self) -> None:
        """Sans export, une application ne peut pas connaître les valeurs
        valides sans lire la source du paquet."""
        assert ERROR_LEVELS == {"l", "m", "q", "h"}


# ------------------------------------------------------- QRCODE-CLI


class TestOptions:

    def test_un_texte_est_exige(self) -> None:
        assert parse_options([]).err is not None

    def test_une_option_inconnue_est_une_erreur(self) -> None:
        assert parse_options(["texte", "--fomat", "png"]).err is not None

    def test_le_format_se_deduit_de_l_extension(self) -> None:
        assert parse_options(["x", "--out", "a.svg"]).fmt == "svg"
        assert parse_options(["x", "--out", "a.png"]).fmt == "png"

    def test_une_extension_qui_contredit_le_format_est_refusee(self) -> None:
        """Un SVG nommé .png est servi avec le mauvais type et refusé par un
        imprimeur."""
        options = parse_options(["x", "--out", "a.png", "--format", "svg"])

        assert options.err is not None
        assert "contredit" in options.err

    def test_une_extension_inconnue_est_refusee(self) -> None:
        options = parse_options(["x", "--out", "a.jpg"])

        assert options.err is not None

    def test_sans_sortie_le_format_par_defaut_est_png(self) -> None:
        assert parse_options(["x"]).fmt == "png"

    @pytest.mark.parametrize("argv", [["x", "--error", "h"], ["x", "--error=h"]])
    def test_les_deux_ecritures_sont_lues(self, argv: list[str]) -> None:
        assert parse_options(argv).error == "h"

    def test_un_niveau_inconnu_est_refuse(self) -> None:
        assert parse_options(["x", "--error", "z"]).err is not None

    @pytest.mark.parametrize("option", ["--scale", "--border"])
    def test_une_valeur_non_entiere_est_refusee(self, option: str) -> None:
        assert parse_options(["x", option, "grand"]).err is not None

    @pytest.mark.parametrize("option", ["--scale", "--border"])
    def test_une_valeur_nulle_est_refusee(self, option: str) -> None:
        assert parse_options(["x", option, "0"]).err is not None


class TestExecution:

    def test_sans_sortie_rien_n_est_ecrit(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(["https://exemple.fr"])

        assert code == 0
        assert "Aucun fichier écrit" in capsys.readouterr().out
        assert list(tmp_path.iterdir()) == []

    def test_avec_sortie_le_fichier_est_ecrit(self, tmp_path: Path) -> None:
        cible = tmp_path / "code.png"

        assert main(["https://exemple.fr", "--out", str(cible)]) == 0
        assert cible.read_bytes().startswith(b"\x89PNG")

    def test_le_svg_est_bien_du_svg(self, tmp_path: Path) -> None:
        cible = tmp_path / "code.svg"
        main(["https://exemple.fr", "--out", str(cible)])

        assert cible.read_text(encoding="utf-8").lstrip().startswith("<?xml")

    def test_un_fichier_existant_n_est_pas_ecrase(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Deux QR Codes se ressemblent à l'œil : l'ancien serait perdu sans
        que rien ne le signale."""
        cible = tmp_path / "code.png"
        cible.write_bytes(b"precieux")

        code = main(["https://exemple.fr", "--out", str(cible)])

        assert code == 1
        assert cible.read_bytes() == b"precieux"
        assert "existe déjà" in capsys.readouterr().out

    def test_le_dossier_parent_est_cree(self, tmp_path: Path) -> None:
        cible = tmp_path / "sous" / "dossier" / "code.png"

        assert main(["x", "--out", str(cible)]) == 0
        assert cible.is_file()

    def test_le_niveau_par_defaut_est_rappele(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Pour qu'une étiquette ne parte pas en « m » par inadvertance."""
        main(["x", "--out", str(tmp_path / "a.png")])

        assert "--error h" in capsys.readouterr().out

    def test_un_niveau_explicite_ne_declenche_pas_le_rappel(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["x", "--out", str(tmp_path / "a.png"), "--error", "h"])

        assert "--error h" not in capsys.readouterr().out

    def test_un_texte_vide_est_refuse(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["   "]) == 1

    def test_un_texte_trop_long_est_refuse(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["x" * 10_000]) == 1
        assert "trop long" in capsys.readouterr().out


class TestGenerateurInchange:

    def test_le_niveau_y_etait_deja(self) -> None:
        """Le ticket ne l'a pas inventé : il l'a rendu accessible depuis HTTP."""
        assert QrCode.from_text("x", error="h").to_png()
