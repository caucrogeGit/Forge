"""`DEPLOY-NGINX-RATE-LIMIT-001` — la parade prescrite est enfin livrée.

Le compteur anti-bruteforce de Forge vit en mémoire du **processus**
(`core/auth/rate_limit.py`). L'unité systemd engendrée lance quatre
travailleurs, chacun comptant séparément : les cinq tentatives par minute en
deviennent vingt, et le verrouillage ne suit pas l'attaquant d'un travailleur à
l'autre.

Ce n'est pas une découverte, `docs/deployment/production-security.md` le disait,
prescrivait la parade Nginx, et la donnait en extrait à recopier.

C'est précisément le défaut : la configuration engendrée ne la portait pas. Une
ligne de défense qui vit dans une page de documentation est absente de tout
projet qui n'a pas lu cette page.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli.deploy import _nginx_conf, _zone_limite


@pytest.fixture
def conf() -> str:
    return _nginx_conf(20, Path("/srv/monapp"), "/srv/monapp/storage/uploads")


# ─────────────────────────────────────────────────────────────────────────────
# La limite est là
# ─────────────────────────────────────────────────────────────────────────────


class TestLimitePosee:

    def test_la_zone_est_declaree(self, conf: str) -> None:
        assert "limit_req_zone" in conf

    def test_la_route_de_connexion_est_bornee(self, conf: str) -> None:
        assert "location = /login" in conf
        assert "limit_req " in conf

    def test_le_refus_est_un_429(self, conf: str) -> None:
        """`503`, le défaut de Nginx, ferait croire à une panne du serveur."""
        assert "limit_req_status 429" in conf

    def test_le_debit_est_celui_que_le_guide_prescrit(self, conf: str) -> None:
        """Forge dit une chose, d'une seule façon (principe 11)."""
        assert "rate=5r/m" in conf
        assert "burst=5 nodelay" in conf

    def test_la_route_bornee_relaie_bien_vers_gunicorn(self, conf: str) -> None:
        """Un `location` qui borne sans relayer répondrait 404 sur /login."""
        bloc = conf.split("location = /login")[1].split("}")[0]

        assert "proxy_pass" in bloc
        assert "X-Forwarded-For" in bloc, (
            "sans cet en-tête, request.ip vaudrait l'adresse du proxy, et le "
            "compteur applicatif compterait tout le monde ensemble")


# ─────────────────────────────────────────────────────────────────────────────
# Elle est au bon endroit
# ─────────────────────────────────────────────────────────────────────────────


class TestPlacement:

    @pytest.mark.parametrize("directive", ["map $request_method", "limit_req_zone"])
    def test_les_directives_http_precedent_le_bloc_server(
        self, conf: str, directive: str
    ) -> None:
        """`map` et `limit_req_zone` vivent dans le contexte `http`.

        Placées dans le bloc `server`, Nginx refuse de démarrer. Le fichier est
        dans le contexte `http` parce qu'il est inclus depuis `sites-enabled/`.
        """
        assert conf.index(directive) < conf.index("server {")

    def test_la_route_bornee_precede_l_attrape_tout(self, conf: str) -> None:
        """Lisibilité seulement, `location =` gagne sur `location /` quel que
        soit l'ordre, mais un lecteur ne le sait pas forcément."""
        assert conf.index("location = /login") < conf.index("location / {")

    def test_les_accolades_sont_equilibrees(self, conf: str) -> None:
        assert conf.count("{") == conf.count("}")


# ─────────────────────────────────────────────────────────────────────────────
# Seul le POST compte
# ─────────────────────────────────────────────────────────────────────────────


class TestSeulLePostCompte:

    def test_la_cle_est_vide_hors_POST(self, conf: str) -> None:
        """Une clé vide n'applique pas la limite, c'est l'idiome Nginx.

        Limiter aussi le GET ferait répondre 429 à qui recharge la page de
        connexion six fois. Une limite qui gêne se fait désactiver, et ne
        protège alors plus rien.
        """
        bloc = conf.split("map $request_method")[1].split("}")[0]

        assert "POST" in bloc
        assert 'default "";' in bloc

    def test_la_cle_est_l_adresse_du_client(self, conf: str) -> None:
        bloc = conf.split("map $request_method")[1].split("}")[0]

        assert "$binary_remote_addr" in bloc


# ─────────────────────────────────────────────────────────────────────────────
# Deux projets derrière le même Nginx
# ─────────────────────────────────────────────────────────────────────────────


class TestNomDeZone:

    def test_deux_projets_ne_declarent_pas_la_meme_zone(self) -> None:
        """Nginx refuserait de démarrer sur « is already bound », un message
        qui ne dit pas quel fichier est en cause."""
        a = _zone_limite(Path("/srv/sequenciel"))
        b = _zone_limite(Path("/srv/referenciel"))

        assert a != b

    @pytest.mark.parametrize(
        "chemin", ["/srv/mon-app", "/srv/mon.app", "/srv/Mon App", "/srv/app_2026"]
    )
    def test_le_nom_reste_un_identifiant_valide(self, chemin: str) -> None:
        """Un tiret ou un point dans le nom du dossier casserait la directive."""
        zone = _zone_limite(Path(chemin))

        assert zone.replace("_", "").isalnum()
        assert not zone.endswith("_")

    def test_un_nom_vide_ne_donne_pas_une_zone_vide(self) -> None:
        assert _zone_limite(Path("/srv/___")) == "forge_login_app"

    def test_la_zone_declaree_est_celle_qui_est_utilisee(self, conf: str) -> None:
        """Une zone déclarée sous un nom et référencée sous un autre fait
        refuser Nginx au démarrage."""
        zone = _zone_limite(Path("/srv/monapp"))

        assert f"zone={zone}:10m" in conf
        assert f"limit_req        zone={zone} " in conf


# ─────────────────────────────────────────────────────────────────────────────
# Cohérence avec ce que Forge écrit ailleurs
# ─────────────────────────────────────────────────────────────────────────────


class TestCoherenceDocumentaire:

    def _guide(self) -> str:
        racine = Path(__file__).resolve().parents[3]
        return (racine / "docs" / "deployment" / "production-security.md").read_text(
            encoding="utf-8")

    def test_le_guide_ne_prescrit_plus_un_extrait_a_recopier(self) -> None:
        """C'était le défaut : une parade qui vivait dans une page."""
        assert "deploy:init" in self._guide()

    def test_le_guide_avertit_d_une_route_renommee(self) -> None:
        """Un `location` qui vise une route qui n'existe plus paraît posé et ne
        garde rien."""
        guide = self._guide()

        assert "renommé" in guide or "renommée" in guide

    def test_le_guide_dit_que_le_challenge_mfa_n_est_pas_couvert(self) -> None:
        """`forge-mvc-mfa` ne pose aucune route : Forge ne peut pas viser
        celle du challenge."""
        assert "challenge" in self._guide().lower()
