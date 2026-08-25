"""DEPLOY-CHECK-CHEMINS-DECLARABLES-001 — le pré-vol regarde là où c'est.

Retour terrain SéquenCiel, ticket 69 F2. Le pré-vol codait en dur les chemins
de l'unité systemd et de la configuration Nginx, alors que le module énonce
lui-même le principe inverse :

    Un avertissement, jamais une erreur : l'unité appartient au projet, Forge
    ne la réécrit pas (principe 9).

Le principe est juste, et les chemins le contredisaient. Un projet qui le suit,
qui adapte son unité, la renomme ou la range ailleurs, devenait invisible du
pré-vol. SéquenCiel range les siens dans `deploiement/`, sous les noms
`sequenciel-gunicorn.service` et `nginx/sequenciel.conf`, et lisait :

    [OK]    Unité systemd — absente, sera écrite par forge deploy:init

Deux lignes rassurantes sur des fichiers qui existent, tournent en production,
et n'ont jamais été regardés. Le vert sur une unité absente est le plus gênant :
c'est un vert qui ne vérifie rien.

Sans ces drapeaux, les vérifications ajoutées par les tickets précédents ne
s'exécuteraient jamais chez ceux qui en ont le plus besoin : les projets assez
avancés pour avoir adapté leur déploiement.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli.deploy import (
    Artefacts,
    NGINX_PAR_DEFAUT,
    UNITE_PAR_DEFAUT,
    _check_results,
    _parser_artefacts,
    _verifier_unite_systemd,
)


@pytest.fixture
def projet_a_la_sequenciel(tmp_path: Path) -> Path:
    """Un projet qui a rangé ses artefacts ailleurs, comme le principe 9 l'invite."""
    (tmp_path / "deploiement" / "nginx").mkdir(parents=True)
    (tmp_path / "deploiement" / "sequenciel-gunicorn.service").write_text(
        "[Unit]\nDescription=SéquenCiel\nAfter=network-online.target\n"
        "StartLimitIntervalSec=0\n\n[Service]\nRestart=always\n",
        encoding="utf-8")
    (tmp_path / "deploiement" / "nginx" / "sequenciel.conf").write_text(
        "server {\n    location /static/ {\n        alias /srv/static/;\n    }\n"
        "    location / {\n    }\n}\n", encoding="utf-8")
    return tmp_path


# ── La lecture des drapeaux ──────────────────────────────────────────────────

class TestParsing:

    def test_sans_drapeau_rien_n_est_declare(self) -> None:
        assert _parser_artefacts([]) is None

    def test_unite_seule(self) -> None:
        artefacts = _parser_artefacts(["--unite", "deploiement/app.service"])

        assert artefacts is not None
        assert artefacts.unite == Path("deploiement/app.service")
        assert artefacts.nginx == NGINX_PAR_DEFAUT

    def test_nginx_seul(self) -> None:
        artefacts = _parser_artefacts(["--nginx", "deploiement/nginx/app.conf"])

        assert artefacts is not None
        assert artefacts.nginx == Path("deploiement/nginx/app.conf")
        assert artefacts.unite == UNITE_PAR_DEFAUT

    def test_les_deux(self) -> None:
        artefacts = _parser_artefacts(
            ["--unite", "a.service", "--nginx", "b.conf"])

        assert artefacts == Artefacts(unite=Path("a.service"), nginx=Path("b.conf"))

    def test_un_drapeau_sans_valeur_est_refuse(self) -> None:
        """Mieux vaut refuser que deviner un chemin."""
        with pytest.raises(SystemExit):
            _parser_artefacts(["--unite"])

    def test_les_autres_arguments_sont_ignores(self) -> None:
        assert _parser_artefacts(["deploy:check", "--verbeux"]) is None


# ── La résolution des chemins ────────────────────────────────────────────────

class TestResolution:

    def test_un_chemin_relatif_part_de_la_racine(self, tmp_path: Path) -> None:
        resolus = Artefacts(Path("deploiement/a.service"), Path("n.conf")).resolus(tmp_path)

        assert resolus.unite == tmp_path / "deploiement" / "a.service"

    def test_un_chemin_absolu_est_respecte(self, tmp_path: Path) -> None:
        absolu = Path("/etc/systemd/system/app.service")
        resolus = Artefacts(absolu, Path("n.conf")).resolus(tmp_path)

        assert resolus.unite == absolu

    def test_le_defaut_est_celui_qu_ecrit_deploy_init(self, tmp_path: Path) -> None:
        defaut = Artefacts.par_defaut(tmp_path)

        assert defaut.unite == tmp_path / "deploy" / "systemd" / "forge-app.service"
        assert defaut.nginx == tmp_path / "deploy" / "nginx" / "forge-app.conf"


# ── Le cas du terrain, de bout en bout ───────────────────────────────────────

class TestProjetQuiARangeAilleurs:

    def _lignes(self, racine: Path, artefacts: "Artefacts | None"):
        return {r.label: r for r in _check_results(racine, artefacts)}

    def test_sans_drapeau_le_pre_vol_ne_voit_rien(self, projet_a_la_sequenciel) -> None:
        """Le comportement d'avant, désormais un avertissement et non un vert."""
        lignes = self._lignes(projet_a_la_sequenciel, None)

        assert lignes["Unité systemd"].status == "warn"
        assert "--unite" in lignes["Unité systemd"].detail

    def test_avec_les_drapeaux_il_lit_les_vrais_fichiers(self, projet_a_la_sequenciel) -> None:
        """LE test du ticket : les contrôles s'exécutent enfin."""
        artefacts = Artefacts(
            unite=Path("deploiement/sequenciel-gunicorn.service"),
            nginx=Path("deploiement/nginx/sequenciel.conf"),
        )

        lignes = self._lignes(projet_a_la_sequenciel, artefacts)

        assert lignes["Redémarrage systemd"].status == "ok"
        assert lignes["Nginx /static/"].status == "ok"

    def test_les_lignes_de_presence_suivent_les_chemins_declares(
        self, projet_a_la_sequenciel,
    ) -> None:
        """Sinon le diagnostic se contredit : « lu » ici, « absent » plus bas."""
        artefacts = Artefacts(
            unite=Path("deploiement/sequenciel-gunicorn.service"),
            nginx=Path("deploiement/nginx/sequenciel.conf"),
        )

        labels = {r.label: r.status for r in _check_results(projet_a_la_sequenciel, artefacts)}

        assert labels["deploiement/sequenciel-gunicorn.service"] == "ok"
        assert labels["deploiement/nginx/sequenciel.conf"] == "ok"

    def test_le_diagnostic_ne_se_contredit_plus(self, tmp_path: Path) -> None:
        """Un fichier absent doit l'être dans TOUTES les lignes qui en parlent."""
        lignes = self._lignes(tmp_path, None)

        assert lignes["Unité systemd"].status == "warn"
        assert lignes["deploy/systemd/forge-app.service"].status == "warn"


class TestUniteAbsente:

    def test_le_message_nomme_le_chemin_cherche(self, tmp_path: Path) -> None:
        """Savoir OÙ le pré-vol a regardé est la moitié du diagnostic."""
        resultat = _verifier_unite_systemd(tmp_path / "deploy" / "systemd" / "forge-app.service")

        assert "forge-app.service" in resultat.detail
