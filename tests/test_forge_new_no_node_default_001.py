"""`FORGE-NEW-NO-NODE-DEFAULT-001` — `forge new` cesse de rebâtir ce qu'il livre.

`forge new` lançait `npm install` puis `npm run build:css` à chaque création.

Mesuré : **deux minutes sur cent quarante-quatre**, pour produire un
`static/tailwind.css` identique **au bit près** à celui que le squelette
versionne. La dépense était donc entière, et son produit nul.

Elle exigeait en outre une chaîne Node complète, `@parcel/watcher` compilé
depuis ses sources compris. Le squelette active `engine-strict` : sous une
version de Node antérieure à `.nvmrc`, `npm install` refuse de tourner et
`forge new` échouait entièrement.

## Ce que la mesure a permis

Cesser de reconstruire n'était honnête qu'à une condition : que le fichier livré
ne puisse plus dériver en silence. C'est ce que garantit
`SKELETON-TAILWIND-CSS-STALE-001`, qui refuse qu'il manque une classe utilisée
par les gabarits. Les deux tickets vont ensemble, et dans cet ordre.

## Ce qui n'est pas retiré

Le squelette continue de livrer `package.json` et `static/src/input.css`. Node
reste à un appel de distance, annoncé plutôt que deviné : `--with-node` à la
création, ou `npm install && npm run build:css` plus tard.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import forge
from cli.project.front_assets import annoncer_css_livre, installer_node

PROJECT_ROOT = Path(__file__).parent.parent
FORGE = str(PROJECT_ROOT / "forge.py")


# ─────────────────────────────────────────────────────────────────────────────
# Les options
# ─────────────────────────────────────────────────────────────────────────────


class TestOptions:

    def test_sans_drapeau_node_n_est_pas_demande(self) -> None:
        assert forge._options_de_new([]) == ("standard", False, False)

    def test_le_drapeau_demande_node(self) -> None:
        _, _, with_node = forge._options_de_new(["--with-node"])

        assert with_node is True

    def test_il_se_combine_aux_autres(self) -> None:
        profil, bare, with_node = forge._options_de_new(
            ["--bare", "--with-node", "--profile", "standard"])

        assert (profil, bare, with_node) == ("standard", True, True)

    def test_une_faute_de_frappe_est_refusee(self) -> None:
        """`CLI-NEW-UNKNOWN-ARGS-001` : une option mal orthographiée doit
        échouer, pas passer inaperçue en laissant croire qu'elle a agi."""
        with pytest.raises(SystemExit):
            forge._options_de_new(["--with-nodes"])

    def test_l_usage_cite_le_drapeau(self, capsys: Any) -> None:
        """Un drapeau absent du message d'usage ne se découvre pas."""
        with pytest.raises(SystemExit):
            forge._options_de_new(["--inconnu"])

        assert "--with-node" in capsys.readouterr().err


# ─────────────────────────────────────────────────────────────────────────────
# Le comportement par défaut
# ─────────────────────────────────────────────────────────────────────────────


class TestParDefaut:

    def _creation(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                  **kw: Any) -> "list[str]":
        appels: "list[str]" = []
        monkeypatch.setattr(forge, "_require_command", lambda c, label=None: None)
        monkeypatch.setattr(forge, "_materialize_skeleton",
                            lambda dest, *, bare=False: os.makedirs(dest, exist_ok=True))
        monkeypatch.setattr(forge, "_configure_env_files", lambda dest, name: None)
        monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
        monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
        monkeypatch.setattr(forge, "_reinitialize_git", lambda dest, name: None)
        monkeypatch.setattr(
            forge, "installer_node",
            lambda dest, etape, run: (appels.append("node"), [])[1])
        monkeypatch.setattr(
            forge, "annoncer_css_livre",
            lambda etape: appels.append("annonce"))
        monkeypatch.chdir(tmp_path)
        forge.cmd_new("projet", **kw)
        return appels

    def test_node_n_est_pas_installe(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: Any
    ) -> None:
        appels = self._creation(monkeypatch, tmp_path)
        capsys.readouterr()

        assert "node" not in appels

    def test_le_css_livre_est_annonce(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: Any
    ) -> None:
        """Ne rien dire laisserait croire à un oubli."""
        appels = self._creation(monkeypatch, tmp_path)
        capsys.readouterr()

        assert "annonce" in appels

    def test_le_drapeau_installe_node(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: Any
    ) -> None:
        appels = self._creation(monkeypatch, tmp_path, with_node=True)
        capsys.readouterr()

        assert appels == ["node"]


# ─────────────────────────────────────────────────────────────────────────────
# L'annonce
# ─────────────────────────────────────────────────────────────────────────────


class TestAnnonce:

    def test_elle_dit_comment_rebatir(self, capsys: Any) -> None:
        annoncer_css_livre(lambda ligne: print(ligne))
        sortie = capsys.readouterr().out

        assert "npm install && npm run build:css" in sortie

    def test_elle_nomme_le_drapeau(self, capsys: Any) -> None:
        annoncer_css_livre(lambda ligne: print(ligne))

        assert "--with-node" in capsys.readouterr().out

    def test_elle_dit_ou_vit_le_fichier(self, capsys: Any) -> None:
        annoncer_css_livre(lambda ligne: print(ligne))

        assert "static/tailwind.css" in capsys.readouterr().out


class TestInstallerNode:

    def test_sans_package_json_il_ne_fait_rien(self, tmp_path: Path) -> None:
        appels: "list[Any]" = []

        avertissements = installer_node(
            str(tmp_path), lambda s: None,
            lambda cmd, *, cwd, check=False, capture=False: appels.append(cmd))

        assert avertissements == []
        assert appels == []

    def test_sans_npm_il_avertit_sans_echouer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Le CSS livré reste en place : l'avertissement le dit désormais,
        là où il annonçait seulement l'absence de Node."""
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr("cli.project.front_assets.shutil.which", lambda c: None)

        avertissements = installer_node(
            str(tmp_path), lambda s: None,
            lambda cmd, *, cwd, check=False, capture=False: None)

        assert len(avertissements) == 1
        assert "CSS livré reste en place" in avertissements[0]


# ─────────────────────────────────────────────────────────────────────────────
# Le parcours réel
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.smoke
class TestParcoursReel:
    """Devenu jouable partout : il ne dépend plus d'une chaîne Node.

    Il coûtait plus de deux minutes, et se sautait sous une version de Node
    antérieure à `.nvmrc`.
    """

    @pytest.fixture(scope="class")
    def projet(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        racine = tmp_path_factory.mktemp("sans_node")
        environnement = dict(os.environ)
        environnement["DB_BACKEND"] = "sqlite"
        resultat = subprocess.run(
            [sys.executable, FORGE, "new", "carnet"],
            cwd=racine, capture_output=True, text=True, timeout=300,
            env=environnement,
        )
        assert resultat.returncode == 0, resultat.stdout + resultat.stderr
        return racine / "carnet"

    def test_le_projet_est_cree(self, projet: Path) -> None:
        assert projet.is_dir()

    def test_le_css_est_la(self, projet: Path) -> None:
        """C'est la condition de tout le ticket : sans CSS livré, un projet
        créé sans Node n'aurait aucune feuille de style."""
        assert (projet / "static" / "tailwind.css").is_file()

    def test_le_css_est_celui_du_squelette(self, projet: Path) -> None:
        livre = (PROJECT_ROOT / "skeleton" / "data" / "static" / "tailwind.css")

        assert (projet / "static" / "tailwind.css").read_bytes() == livre.read_bytes()

    def test_node_n_a_pas_ete_installe(self, projet: Path) -> None:
        assert not (projet / "node_modules").exists()

    def test_le_chemin_node_reste_ouvert(self, projet: Path) -> None:
        """Rien n'est retiré, seule la dépense l'est."""
        assert (projet / "package.json").is_file()
        assert (projet / "static" / "src" / "input.css").is_file()
