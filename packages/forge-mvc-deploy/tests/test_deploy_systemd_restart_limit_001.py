"""DEPLOY-SYSTEMD-RESTART-LIMIT-001 — l'unité générée tient en service.

Deux défauts mesurés à la première mise en production réelle (retour terrain
SéquenCiel, 2026-08-24), dans le gabarit `[Unit]` que Forge écrit.

Le premier : `Restart=always` avec `RestartSec=5`, sans
`StartLimitIntervalSec=0`. Le défaut de systemd s'applique alors — cinq
démarrages en dix secondes, puis le service reste à terre. Deux minutes de base
indisponible transforment une coupure passagère en panne du lendemain matin,
soit exactement ce que `Restart=always` prétend couvrir.

Le piège dans le piège : la clé vit dans `[Unit]`. Posée dans `[Service]`,
systemd l'ignore avec un simple avertissement au journal, et la garantie
n'existe pas alors que le fichier a toutes les apparences d'être correct. Un
contrôle qui lit l'unité comme un seul bloc de texte ne peut pas le voir : ces
tests vérifient donc la SECTION, jamais la seule présence de la chaîne.

Le second : `After=network.target` ne dit pas que le réseau est configuré,
seulement que la pile est montée. Une application qui ouvre une connexion à son
démarrage veut `network-online.target`, et le `Wants=` qui va avec — sans lui,
la cible n'est pas tirée et l'`After=` n'ordonne rien.

`deploy:init` écrit en write-if-new (principe 9) : un projet provisionné avant
ce correctif garde son unité. `deploy:check` le lui dit, sans jamais réécrire.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli import deploy


@pytest.fixture
def unite(tmp_path: Path):
    """Écrit une unité systemd dans un projet jetable et rend sa racine."""
    def _ecrire(contenu: "str | None") -> Path:
        if contenu is not None:
            dossier = tmp_path / "deploy" / "systemd"
            dossier.mkdir(parents=True, exist_ok=True)
            (dossier / "forge-app.service").write_text(contenu, encoding="utf-8")
        return tmp_path
    return _ecrire


# ── Le gabarit écrit ─────────────────────────────────────────────────────────

class TestGabarit:
    """Ce que `deploy:init` pose dans une unité neuve."""

    def test_start_limit_est_dans_la_section_unit(self) -> None:
        """La clé mal placée est ignorée par systemd : la section fait foi."""
        rendu = deploy._systemd_service(Path("/srv/app"))

        assert deploy._section_de_la_cle(rendu, "StartLimitIntervalSec") == "Unit"

    def test_start_limit_leve_le_plafond(self) -> None:
        assert "StartLimitIntervalSec=0" in deploy._systemd_service(Path("/srv/app"))

    def test_attend_le_reseau_configure(self) -> None:
        rendu = deploy._systemd_service(Path("/srv/app"))

        assert deploy._section_de_la_cle(rendu, "Wants") == "Unit"
        assert "Wants=network-online.target" in rendu

    def test_after_nomme_la_meme_cible_que_wants(self) -> None:
        """Un `Wants=` sans l'`After=` correspondant tire la cible sans l'attendre."""
        rendu = deploy._systemd_service(Path("/srv/app"))

        ligne_after = next(l for l in rendu.splitlines() if l.startswith("After="))
        assert "network-online.target" in ligne_after

    def test_le_gabarit_reste_lisible_par_le_controle_de_backend(self) -> None:
        """DEPLOY-SYSTEMD-STALE-AFTER-001 lit `After=` : il doit y survivre."""
        rendu = deploy._systemd_service(Path("/srv/app"))

        assert deploy._APRES_SYSTEMD.search(rendu) is not None


# ── Le découpage par section ─────────────────────────────────────────────────

class TestSectionDeLaCle:
    """Le contrôle rattache chaque clé à sa section, comme le fait systemd."""

    def test_trouve_la_cle_dans_sa_section(self) -> None:
        texte = "[Unit]\nStartLimitIntervalSec=0\n\n[Service]\nType=simple\n"

        assert deploy._section_de_la_cle(texte, "StartLimitIntervalSec") == "Unit"
        assert deploy._section_de_la_cle(texte, "Type") == "Service"

    def test_cle_absente_rend_none(self) -> None:
        assert deploy._section_de_la_cle("[Unit]\nDescription=X\n", "Restart") is None

    def test_ignore_la_cle_commentee(self) -> None:
        """Une ligne commentée n'est pas une déclaration."""
        texte = "[Unit]\n# StartLimitIntervalSec=0\n"

        assert deploy._section_de_la_cle(texte, "StartLimitIntervalSec") is None

    def test_ignore_le_nom_cite_dans_un_commentaire(self) -> None:
        """Le mot dans une phrase de commentaire ne vaut pas déclaration."""
        texte = "[Service]\n# poser StartLimitIntervalSec ailleurs\nType=simple\n"

        assert deploy._section_de_la_cle(texte, "StartLimitIntervalSec") is None

    @pytest.mark.parametrize("ligne", [
        "StartLimitIntervalSec=0",
        "  StartLimitIntervalSec=0",
        "StartLimitIntervalSec = 0",
    ])
    def test_tolere_les_espaces(self, ligne: str) -> None:
        assert deploy._section_de_la_cle(f"[Unit]\n{ligne}\n", "StartLimitIntervalSec") == "Unit"


# ── Le contrôle des unités déjà écrites ──────────────────────────────────────

class TestControle:
    """`deploy:check` sur un projet provisionné avant ce correctif."""

    def test_cle_absente_avertit(self, unite) -> None:
        racine = unite("[Unit]\nDescription=X\n\n[Service]\nRestart=always\nRestartSec=5\n")

        resultat = deploy._verifier_limite_redemarrage(racine)

        assert resultat is not None
        assert resultat.status == "warn"
        assert "StartLimitIntervalSec" in resultat.detail
        assert "[Unit]" in resultat.detail

    def test_cle_dans_service_avertit(self, unite) -> None:
        """Le cas vécu : la clé posée au mauvais endroit, ignorée en silence."""
        racine = unite(
            "[Unit]\nDescription=X\n\n"
            "[Service]\nRestart=always\nStartLimitIntervalSec=0\n"
        )

        resultat = deploy._verifier_limite_redemarrage(racine)

        assert resultat is not None
        assert resultat.status == "warn"
        assert "[Service]" in resultat.detail

    def test_cle_dans_unit_valide(self, unite) -> None:
        racine = unite(
            "[Unit]\nDescription=X\nStartLimitIntervalSec=0\n\n"
            "[Service]\nRestart=always\n"
        )

        resultat = deploy._verifier_limite_redemarrage(racine)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_sans_restart_rien_a_plafonner(self, unite) -> None:
        racine = unite("[Unit]\nDescription=X\n\n[Service]\nType=oneshot\n")

        resultat = deploy._verifier_limite_redemarrage(racine)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_unite_absente_ne_dit_rien(self, tmp_path: Path) -> None:
        """L'absence est déjà signalée ailleurs ; une ligne de plus brouille."""
        assert deploy._verifier_limite_redemarrage(tmp_path) is None

    def test_le_gabarit_neuf_passe_son_propre_controle(self, unite) -> None:
        """Ce que Forge écrit ne doit jamais déclencher son propre avertissement."""
        racine = unite(deploy._systemd_service(Path("/srv/app")))

        resultat = deploy._verifier_limite_redemarrage(racine)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_le_controle_figure_dans_le_diagnostic(self, unite) -> None:
        """La vérification est branchée, pas seulement écrite."""
        racine = unite("[Unit]\nDescription=X\n\n[Service]\nRestart=always\n")

        labels = [r.label for r in deploy._check_results(racine)]

        assert "Redémarrage systemd" in labels
