"""DEPLOY-NGINX-STATIC-LOCATIONS-001 — Nginx sert ce que WSGI cesse de servir.

Mesuré à la première mise en production réelle (retour terrain SéquenCiel,
2026-08-24). La configuration générée n'avait qu'un `location /`, qui relaie
tout vers Gunicorn.

Or `/static/` et `/favicon.ico` vivent dans le `RequestHandler` de `app.py`,
donc avant le routage : le chemin WSGI ne les voit pas. Une application
déployée avec cette configuration démarre, répond 200, et sert des pages sans
feuille de style. La panne coûte une heure à comprendre parce que tout paraît
sain : le service tourne, les journaux sont vides, les pages répondent.

`/media/` a la même cause et pas le même remède. Le servir depuis Nginx rend
public tout `UPLOAD_ROOT` et retire définitivement à l'application le droit de
décider qui lit quoi. Le bloc est donc écrit commenté, et ces tests vérifient
qu'il le reste : un gabarit qui l'activerait remplacerait une panne visible par
une fuite silencieuse.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli import deploy


def _conf(project_dir: str = "/srv/app", upload_root: str = "/srv/app/storage/uploads") -> str:
    return deploy._nginx_conf(5, Path(project_dir), upload_root)


def _blocs_actifs(conf: str) -> set[str]:
    """Chemins des `location` réellement déclarés, commentaires exclus."""
    actives = "\n".join(l for l in conf.splitlines() if not l.strip().startswith("#"))
    return {t.group(1) for t in deploy._LOCATION_NGINX.finditer(actives)}


# ── Le gabarit écrit ─────────────────────────────────────────────────────────

class TestGabarit:

    def test_sert_les_fichiers_statiques(self) -> None:
        assert "/static/" in _blocs_actifs(_conf())

    def test_l_alias_pointe_le_dossier_du_projet(self) -> None:
        assert "alias /srv/app/static/;" in _conf()

    def test_sert_le_favicon(self) -> None:
        """`app.py` le sert depuis static/ ; sous WSGI il tombait en 404."""
        assert "/favicon.ico" in _blocs_actifs(_conf())

    def test_relaie_toujours_le_reste_vers_gunicorn(self) -> None:
        conf = _conf()

        assert "/" in _blocs_actifs(conf)
        assert "proxy_pass         http://127.0.0.1:8000;" in conf

    def test_location_et_alias_finissent_par_un_slash(self) -> None:
        """`location /static` sans slash avec un alias ouvre une traversée."""
        conf = _conf()

        assert "location /static/ {" in conf
        assert "alias /srv/app/static/;" in conf

    def test_client_max_body_size_survit(self) -> None:
        """Le lien avec UPLOAD_MAX_SIZE ne doit pas être perdu au passage."""
        assert "client_max_body_size 6m;" in _conf()


class TestMediasNonServis:
    """Nginx ne sert pas /media/, et depuis CORE-WSGI-MEDIA-PARITY-001 il n'a
    plus aucune raison de le faire : l'application les sert sur les deux
    serveurs, avec sa résolution anti-traversal et ses tranches HTTP Range.

    Le décommenter reste possible, et reste une décision : cela rendrait public
    tout `UPLOAD_ROOT`.
    """

    def test_media_n_est_pas_un_bloc_actif(self) -> None:
        assert not any(c.startswith("/media") for c in _blocs_actifs(_conf()))

    def test_le_texte_montre_le_bon_chemin(self) -> None:
        """Celui qui décide de décharger Nginx doit lire le vrai chemin."""
        conf = _conf(upload_root="/var/lib/sequenciel/uploads")

        assert "/var/lib/sequenciel/uploads/" in conf

    def test_la_reserve_est_ecrite_dans_le_fichier(self) -> None:
        """Celui qui déploie doit lire la question au moment de la trancher."""
        conf = _conf()

        assert "UPLOAD_ROOT" in conf
        assert "public" in conf

    def test_le_fichier_dit_que_l_application_les_sert(self) -> None:
        """Sans ça, le contournement reste tentant pour une panne disparue."""
        conf = _conf()

        assert "CORE-WSGI-MEDIA-PARITY-001" in conf


# ── La résolution de UPLOAD_ROOT ─────────────────────────────────────────────

class TestUploadRoot:

    def test_defaut_de_l_opt_in_sous_la_racine(self, tmp_path: Path) -> None:
        assert deploy._upload_root(tmp_path) == str(tmp_path / "storage" / "uploads")

    def test_valeur_absolue_de_env_prod(self, tmp_path: Path) -> None:
        (tmp_path / "env").mkdir()
        (tmp_path / "env" / "prod").write_text(
            "DB_NAME=x\nUPLOAD_ROOT=/var/lib/app/uploads\n", encoding="utf-8")

        assert deploy._upload_root(tmp_path) == "/var/lib/app/uploads"

    def test_valeur_relative_resolue_sous_la_racine(self, tmp_path: Path) -> None:
        """Nginx n'a pas de répertoire courant : un chemin relatif ne lui dit rien."""
        (tmp_path / "env").mkdir()
        (tmp_path / "env" / "prod").write_text("UPLOAD_ROOT=medias\n", encoding="utf-8")

        assert deploy._upload_root(tmp_path) == str(tmp_path / "medias")

    def test_valeur_vide_retombe_sur_le_defaut(self, tmp_path: Path) -> None:
        (tmp_path / "env").mkdir()
        (tmp_path / "env" / "prod").write_text("UPLOAD_ROOT=\n", encoding="utf-8")

        assert deploy._upload_root(tmp_path) == str(tmp_path / "storage" / "uploads")


# ── Le contrôle des configurations déjà écrites ──────────────────────────────

class TestControle:

    def _ecrire(self, racine: Path, contenu: str) -> Path:
        dossier = racine / "deploy" / "nginx"
        dossier.mkdir(parents=True, exist_ok=True)
        (dossier / "forge-app.conf").write_text(contenu, encoding="utf-8")
        return racine

    def test_conf_sans_static_avertit(self, tmp_path: Path) -> None:
        """La configuration rc7 d'origine, exactement."""
        racine = self._ecrire(tmp_path, "server {\n    location / {\n    }\n}\n")

        resultat = deploy._verifier_locations_nginx(racine)

        assert resultat is not None
        assert resultat.status == "warn"
        assert "feuille de style" in resultat.detail

    def test_un_bloc_static_commente_ne_compte_pas(self, tmp_path: Path) -> None:
        """C'est le cas qu'un contrôle naïf rate : le texte est là, pas la règle."""
        racine = self._ecrire(
            tmp_path,
            "server {\n    # location /static/ {\n    #     alias /srv/app/static/;\n"
            "    # }\n    location / {\n    }\n}\n")

        resultat = deploy._verifier_locations_nginx(racine)

        assert resultat is not None
        assert resultat.status == "warn"

    def test_conf_avec_static_valide(self, tmp_path: Path) -> None:
        racine = self._ecrire(
            tmp_path,
            "server {\n    location /static/ {\n        alias /srv/app/static/;\n"
            "    }\n    location / {\n    }\n}\n")

        resultat = deploy._verifier_locations_nginx(racine)

        assert resultat is not None
        assert resultat.status == "ok"

    @pytest.mark.parametrize("ligne", [
        "location /static/ {",
        "location ^~ /static/ {",
        "location ~ /static/.*\\.css$ {",
    ])
    def test_reconnait_les_formes_usuelles(self, tmp_path: Path, ligne: str) -> None:
        racine = self._ecrire(tmp_path, f"server {{\n    {ligne}\n    }}\n}}\n")

        resultat = deploy._verifier_locations_nginx(racine)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_conf_absente_ne_dit_rien(self, tmp_path: Path) -> None:
        assert deploy._verifier_locations_nginx(tmp_path) is None

    def test_le_gabarit_neuf_passe_son_propre_controle(self, tmp_path: Path) -> None:
        racine = self._ecrire(tmp_path, _conf())

        resultat = deploy._verifier_locations_nginx(racine)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_le_controle_figure_dans_le_diagnostic(self, tmp_path: Path) -> None:
        racine = self._ecrire(tmp_path, "server {\n    location / {\n    }\n}\n")

        labels = [r.label for r in deploy._check_results(racine)]

        assert "Nginx /static/" in labels
